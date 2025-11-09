<template>
  <div class="statistics-page">
    <!-- Header -->
    <mdui-card variant="outlined" style="margin-bottom: 16px;">
      <div style="padding: 24px;">
        <h2 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 500;">课程统计</h2>
        <p style="margin: 0; color: var(--mdui-color-on-surface-variant);">
          查看课程数据、出勤记录和学习统计
        </p>
      </div>
    </mdui-card>

    <!-- Statistics Cards -->
    <div class="stats-cards">
      <mdui-card variant="filled" class="stat-card">
        <div class="stat-card-content">
          <mdui-icon name="schedule" style="font-size: 48px; color: var(--mdui-color-primary);"></mdui-icon>
          <div class="stat-info">
            <div class="stat-value">{{ totalHours }}</div>
            <div class="stat-label">总课时</div>
          </div>
        </div>
      </mdui-card>

      <mdui-card variant="filled" class="stat-card">
        <div class="stat-card-content">
          <mdui-icon name="event_available" style="font-size: 48px; color: var(--mdui-color-secondary);"></mdui-icon>
          <div class="stat-info">
            <div class="stat-value">{{ attendanceRate }}%</div>
            <div class="stat-label">出勤率</div>
          </div>
        </div>
      </mdui-card>

      <mdui-card variant="filled" class="stat-card">
        <div class="stat-card-content">
          <mdui-icon name="school" style="font-size: 48px; color: var(--mdui-color-tertiary);"></mdui-icon>
          <div class="stat-info">
            <div class="stat-value">{{ totalCourses }}</div>
            <div class="stat-label">总课程数</div>
          </div>
        </div>
      </mdui-card>

      <mdui-card variant="filled" class="stat-card">
        <div class="stat-card-content">
          <mdui-icon name="trending_up" style="font-size: 48px; color: var(--mdui-color-primary);"></mdui-icon>
          <div class="stat-info">
            <div class="stat-value">{{ avgWeeklyHours }}</div>
            <div class="stat-label">周均课时</div>
          </div>
        </div>
      </mdui-card>
    </div>

    <!-- Charts Section -->
    <div class="charts-section">
      <!-- Weekly Load Chart -->
      <mdui-card variant="outlined" class="chart-card">
        <div style="padding: 16px;">
          <h3 style="margin: 0 0 16px 0;">每周课时分布</h3>
          <v-chart :option="weeklyLoadOption" :autoresize="true" style="height: 300px;"></v-chart>
        </div>
      </mdui-card>

      <!-- Course Distribution Chart -->
      <mdui-card variant="outlined" class="chart-card">
        <div style="padding: 16px;">
          <h3 style="margin: 0 0 16px 0;">课程分布</h3>
          <v-chart :option="courseDistributionOption" :autoresize="true" style="height: 300px;"></v-chart>
        </div>
      </mdui-card>
    </div>

    <!-- Time Slot Distribution -->
    <mdui-card variant="outlined" style="margin-bottom: 16px;">
      <div style="padding: 16px;">
        <h3 style="margin: 0 0 16px 0;">时段分布</h3>
        <v-chart :option="timeSlotOption" :autoresize="true" style="height: 250px;"></v-chart>
      </div>
    </mdui-card>

    <!-- Attendance Management -->
    <mdui-card variant="outlined">
      <div style="padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h3 style="margin: 0;">出勤记录</h3>
          <mdui-button variant="text" @click="loadAttendanceHistory">
            <mdui-icon slot="icon" name="refresh"></mdui-icon>
            刷新
          </mdui-button>
        </div>

        <mdui-list v-if="attendanceHistory.length > 0">
          <mdui-list-item v-for="record in attendanceHistory" :key="record.id">
            <div style="display: flex; align-items: center; width: 100%; gap: 12px;">
              <mdui-icon :name="record.attended ? 'check_circle' : 'cancel'"
                        :style="{color: record.attended ? 'var(--mdui-color-primary)' : 'var(--mdui-color-error)'}">
              </mdui-icon>
              <div style="flex: 1;">
                <div style="font-weight: 500;">{{ record.course_name }}</div>
                <div style="font-size: 14px; color: var(--mdui-color-on-surface-variant);">
                  {{ record.date }} {{ record.start_time }}-{{ record.end_time }}
                  <span v-if="record.teacher"> · {{ record.teacher }}</span>
                </div>
                <div v-if="record.notes" style="font-size: 13px; color: var(--mdui-color-on-surface-variant); margin-top: 4px;">
                  {{ record.notes }}
                </div>
              </div>
              <mdui-badge :variant="record.attended ? 'filled' : 'outlined'">
                {{ record.attended ? '已出勤' : '缺勤' }}
              </mdui-badge>
            </div>
          </mdui-list-item>
        </mdui-list>

        <div v-else style="text-align: center; padding: 40px 0; color: var(--mdui-color-on-surface-variant);">
          <mdui-icon name="event_busy" style="font-size: 48px; opacity: 0.5;"></mdui-icon>
          <p>暂无出勤记录</p>
        </div>
      </div>
    </mdui-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { pyInvoke } from 'tauri-plugin-pytauri-api';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, PieChart, LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components';

// Register ECharts components
use([
  CanvasRenderer,
  BarChart,
  PieChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
]);

// Reactive state
const statistics = reactive({
  total_hours: {},
  distribution: {},
  attendance: {},
  weekly_load: [],
  busiest_days: [],
  time_slots: {}
});

const attendanceHistory = ref([]);
const isLoading = ref(false);

// Computed stats
const totalHours = computed(() => statistics.total_hours.total_hours || 0);
const avgWeeklyHours = computed(() => statistics.total_hours.average_per_week || 0);
const attendanceRate = computed(() => statistics.attendance.attendance_rate || 0);
const totalCourses = computed(() => {
  const byDay = statistics.distribution.by_day || {};
  return Object.values(byDay).reduce((sum, count) => sum + count, 0);
});

// Chart options
const weeklyLoadOption = computed(() => {
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
  const data = statistics.weekly_load.map(item => item.total_hours);

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: statistics.weekly_load.map(item => days[item.day_of_week - 1]),
      axisTick: { alignWithLabel: true }
    },
    yAxis: {
      type: 'value',
      name: '课时',
      minInterval: 1
    },
    series: [{
      name: '课时',
      type: 'bar',
      data: data,
      itemStyle: {
        color: '#1976d2'
      },
      label: {
        show: true,
        position: 'top'
      }
    }]
  };
});

const courseDistributionOption = computed(() => {
  const byDay = statistics.distribution.by_day || {};
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

  const data = Object.entries(byDay).map(([day, count]) => ({
    name: days[parseInt(day) - 1],
    value: count
  }));

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center'
    },
    series: [{
      type: 'pie',
      radius: '60%',
      center: ['40%', '50%'],
      data: data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  };
});

const timeSlotOption = computed(() => {
  const timeSlots = statistics.time_slots || {};
  const labels = {
    morning: '上午',
    afternoon: '下午',
    evening: '晚上'
  };

  const data = Object.entries(timeSlots).map(([slot, count]) => ({
    name: labels[slot] || slot,
    value: count
  }));

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}: {c}'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      data: data
    }]
  };
});

// Methods
async function loadStatistics() {
  isLoading.value = true;
  try {
    const response = await pyInvoke('get_course_statistics', {});

    if (response.success) {
      Object.assign(statistics, response.statistics);
    } else {
      mdui.snackbar({ message: '加载统计数据失败: ' + response.message });
    }
  } catch (error) {
    console.error('Failed to load statistics:', error);
    mdui.snackbar({ message: '加载统计数据失败' });
  } finally {
    isLoading.value = false;
  }
}

async function loadAttendanceHistory() {
  try {
    const response = await pyInvoke('get_attendance_history', {
      limit: 20
    });

    if (response.success) {
      attendanceHistory.value = response.records;
    } else {
      mdui.snackbar({ message: '加载出勤记录失败: ' + response.message });
    }
  } catch (error) {
    console.error('Failed to load attendance history:', error);
    mdui.snackbar({ message: '加载出勤记录失败' });
  }
}

// Lifecycle
onMounted(async () => {
  await loadStatistics();
  await loadAttendanceHistory();
});
</script>

<style scoped>
.statistics-page {
  padding: 16px;
  max-width: 1400px;
  margin: 0 auto;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  padding: 20px;
}

.stat-card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--mdui-color-on-surface-variant);
  margin-top: 4px;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.chart-card {
  min-height: 380px;
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }

  .charts-section {
    grid-template-columns: 1fr;
  }

  .stat-value {
    font-size: 24px;
  }
}
</style>
