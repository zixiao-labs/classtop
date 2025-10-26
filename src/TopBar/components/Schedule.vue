<template>
  <div class="schedule-container" v-if="props.type === 'full'">
    <mdui-linear-progress class="currentClass" id="progress" :class="{ 'break-time': isBreakTime }" :value="progress"
      :data-text="displayText"></mdui-linear-progress>
  </div>
  <mdui-linear-progress id="mini-progress" :value="progress"
    v-if="props.type === 'mini'"></mdui-linear-progress>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import {
  getScheduleByDay,
  getScheduleForWeek,
  getCurrentWeek,
  findCurrentClass,
  findNextClass,
  findLastClass,
  findNextClassAcrossWeek,
  getTodayWeekday
} from '../../utils/schedule.js';
import { listen } from '@tauri-apps/api/event';

const props = defineProps({
  type: {
    type: String,
    default: 'full' // 'full' or 'mini'
  }
});

const emit = defineEmits(['classStart', 'classEnd']);

// 课程数据缓存
const todaySchedule = ref([]);
const weekSchedule = ref([]);
const currentWeek = ref(1);

// 显示状态
const displayText = ref('暂无课程');
const currentTime = ref(new Date());
const isBreakTime = ref(false);

// 上一次的课程状态（用于检测课程变化）
const lastClassState = ref(null);

let intervalId = null;
let updateIntervalId = null;
let unlistenScheduleUpdate = null;

let progressElement = null;

// 格式化剩余时间
const formatRemainingTime = (seconds) => {
  seconds = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) return `${hours}小时${minutes}分钟`;
  if (minutes > 0) return `${minutes}分钟${secs}秒`;
  return `${secs}秒`;
};

// 将时间字符串转为秒数
const timeToSeconds = (timeStr) => {
  const [h, m] = timeStr.split(':').map(Number);
  return h * 3600 + m * 60;
};

// 更新进度值并同步 CSS 变量（使用实际像素值）
const updateProgress = (value) => {
  progress.value = value;
  if (progressElement) {
    // 获取进度条元素的实际宽度
    const elementWidth = progressElement.getBoundingClientRect().width;
    // 计算进度条填充的实际像素位置
    const fillPositionPx = elementWidth * value;

    // 设置 CSS 变量（使用像素值而非百分比，避免计算误差）
    progressElement.style.setProperty('--progress-fill-px', `${fillPositionPx}px`);
  }
};

// 计算课程进度或课间进度
const calculateProgress = () => {
  const now = currentTime.value;
  const currentSeconds = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();

  // 查找当前课程和下一节课
  current = findCurrentClass(todaySchedule.value, now);
  const next = findNextClass(todaySchedule.value, now);
  const last = findLastClass(todaySchedule.value, now);

  if (current) {
    // 当前有课 - 显示课程进度
    const startSeconds = timeToSeconds(current.start_time);
    const endSeconds = timeToSeconds(current.end_time);

    if (currentSeconds < startSeconds) return 0;
    if (currentSeconds >= endSeconds) return 1;
    return (currentSeconds - startSeconds) / (endSeconds - startSeconds);
  }

  if (next && isBreakTime.value && last) {
    // 课间 - 显示课间进度
    const breakStartSeconds = timeToSeconds(last.end_time);
    const breakEndSeconds = timeToSeconds(next.start_time);

    if (currentSeconds < breakStartSeconds) return 0;
    if (currentSeconds >= breakEndSeconds) return 1;

    const breakDuration = breakEndSeconds - breakStartSeconds;
    const elapsedTime = currentSeconds - breakStartSeconds;
    return (breakDuration - elapsedTime) / breakDuration;
  }

  return 0;
};

// 更新显示
const updateDisplay = () => {
  const now = currentTime.value;
  const currentSeconds = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();

  // 从缓存数据中查找当前状态
  current = findCurrentClass(todaySchedule.value, now);
  const todayNext = findNextClass(todaySchedule.value, now);

  // 跨天查找下一节课
  const todayWeekday = getTodayWeekday();
  const nextAcrossWeek = findNextClassAcrossWeek(weekSchedule.value, todayWeekday, now);

  // 检测课程状态变化并触发钩子
  const currentClassId = current ? `${current.name}-${current.start_time}` : null;

  if (lastClassState.value !== currentClassId) {
    if (currentClassId && !lastClassState.value) {
      // 从无课 -> 有课：上课了
      emit('classStart', current);
    } else if (!currentClassId && lastClassState.value) {
      // 从有课 -> 无课：下课了
      const lastClass = todaySchedule.value.find(c => `${c.name}-${c.start_time}` === lastClassState.value);
      emit('classEnd', lastClass || { name: '上一节课' });
    } else if (currentClassId && lastClassState.value && currentClassId !== lastClassState.value) {
      // 从一节课 -> 另一节课：下课 + 上课
      const lastClass = todaySchedule.value.find(c => `${c.name}-${c.start_time}` === lastClassState.value);
      emit('classEnd', lastClass || { name: '上一节课' });
      emit('classStart', current);
    }

    lastClassState.value = currentClassId;
  }

  if (current) {
    // 当前有课
    isBreakTime.value = false;
    const { name, location, start_time, end_time } = current;

    // 检查是否即将结束
    const endSeconds = timeToSeconds(end_time);
    if (currentSeconds >= endSeconds - 1 && todayNext) {
      // 即将结束，提前切换到课间显示
      isBreakTime.value = true;
      const remainingSeconds = timeToSeconds(todayNext.start_time) - currentSeconds;
      const remainingTimeStr = formatRemainingTime(remainingSeconds);
      const nextLocation = todayNext.location ? ` @ ${todayNext.location}` : '';
      displayText.value = `下一节: ${todayNext.name}${nextLocation} (${remainingTimeStr}后)`;
      rewidthProgressBar();
    } else {
      const locationText = location ? ` @ ${location}` : '';
      displayText.value = `${name}${locationText} (${start_time}-${end_time})`;
      rewidthProgressBar();
    }

    updateProgress(calculateProgress());
  } else if (todayNext) {
    // 今天还有课 - 课间
    isBreakTime.value = true;
    const remainingSeconds = timeToSeconds(todayNext.start_time) - currentSeconds;

    if (remainingSeconds > 0) {
      const remainingTimeStr = formatRemainingTime(remainingSeconds);
      const nextLocation = todayNext.location ? ` @ ${todayNext.location}` : '';
      displayText.value = `下一节: ${todayNext.name}${nextLocation} (${remainingTimeStr}后)`;
      rewidthProgressBar();
      updateProgress(calculateProgress());
    } else {
      // 应该已经开始了，触发刷新
      const nextLocation = todayNext.location ? ` @ ${todayNext.location}` : '';
      displayText.value = `${todayNext.name}${nextLocation} (即将开始)`;
      rewidthProgressBar();
      updateProgress(0);
      loadScheduleData();
    }
  } else if (nextAcrossWeek && nextAcrossWeek.day_of_week !== todayWeekday) {
    // 今日课程结束，显示其他天的下一节课
    isBreakTime.value = false;
    const dayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    const dayName = dayNames[nextAcrossWeek.day_of_week] || '未知';
    displayText.value = `今日课程结束 - 下一节: ${dayName} ${nextAcrossWeek.name}`;
    rewidthProgressBar();
    current = null;
    updateProgress(0);
  } else {
    // 没有任何课程
    isBreakTime.value = false;
    displayText.value = '暂无课程';
    rewidthProgressBar();
    updateProgress(0);
  }
};

// 加载课程数据
const loadScheduleData = async () => {
  try {
    // 获取当前周数
    const weekInfo = await getCurrentWeek();
    currentWeek.value = weekInfo.week;

    // 获取今天的weekday
    const today = getTodayWeekday();

    // 并发获取今天和本周的课程
    const [todayData, weekData] = await Promise.all([
      getScheduleByDay(today, currentWeek.value),
      getScheduleForWeek(currentWeek.value)
    ]);

    todaySchedule.value = todayData;
    weekSchedule.value = weekData;

    updateDisplay();
  } catch (error) {
    console.error('Failed to load schedule data:', error);
    displayText.value = '加载失败';
    updateProgress(0);
    isBreakTime.value = false;
  }
};

// 每秒更新时间和进度
const updateTimeAndProgress = () => {
  currentTime.value = new Date();
  updateDisplay();
};

const rewidthProgressBar = () => {
  if (progressElement) {
    const text = displayText.value || '';
    // create hidden span to measure real rendered width
    const span = document.createElement('span');
    span.textContent = text;
    span.style.position = 'absolute';
    span.style.visibility = 'hidden';
    span.style.whiteSpace = 'nowrap';
    span.style.fontSize = '1rem';
    span.style.fontWeight = '500';
    span.style.fontFamily = getComputedStyle(progressElement).fontFamily || 'inherit';
    // 使用与进度条文字相同的渲染设置
    span.style.webkitFontSmoothing = 'antialiased';
    span.style.textRendering = 'geometricPrecision';
    document.body.appendChild(span);
    const widthPx = span.getBoundingClientRect().width;
    document.body.removeChild(span);

    // convert px -> rem based on root font-size
    const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
    const widthRem = widthPx / rootFontSize;

    // add padding and clamp to reasonable bounds
    const paddedRem = widthRem + 1; // 1rem padding (adjust if needed)
    const minRem = 4;
    const maxRem = 24;
    progressElement.style.width = Math.min(maxRem, Math.max(minRem, paddedRem)) + 'rem';

    // 宽度改变后，重新计算进度填充的像素位置
    // 使用 requestAnimationFrame 确保宽度已应用
    requestAnimationFrame(() => {
      updateProgress(progress.value);
    });
  }
};

onMounted(async () => {
  // 初次加载
  await loadScheduleData();

  // 每10秒刷新课程数据（从后端）
  intervalId = setInterval(loadScheduleData, 10000);

  // 每秒更新显示（使用缓存数据）
  updateIntervalId = setInterval(updateTimeAndProgress, 1000);

  progressElement = document.getElementById('progress');

  // 监听课表更新事件
  try {
    unlistenScheduleUpdate = await listen('schedule-update', (event) => {
      console.log('Schedule update received:', event.payload);
      loadScheduleData();
    });
  } catch (error) {
    console.error('Failed to setup schedule update listener:', error);
  }
});

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
  }
  if (updateIntervalId) {
    clearInterval(updateIntervalId);
  }
  if (unlistenScheduleUpdate) {
    unlistenScheduleUpdate();
  }
});
</script>

<script>
export const progress = ref(0);
export let current = null;
</script>

<style scoped>
.schedule-container {
  position: relative;
}

.currentClass {
  width: 12rem;
  height: 2rem;
  border-radius: 10px;
  position: relative;
}

/* 课间时间的样式 */
.currentClass.break-time {}

/* 底层文字 - 在浅色背景上显示（深色） */
.currentClass::before {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
  line-height: 2rem;
  color: rgb(var(--mdui-color-on-surface-variant));
  font-size: 1rem;
  font-weight: 500;
  white-space: nowrap;
  text-align: center;
  pointer-events: none;
  z-index: 1;
  /* 统一字体渲染，修复高DPI设备上的对齐问题 */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: geometricPrecision;
  transform: translateZ(0);
  backface-visibility: hidden;
}

/* 顶层文字 - 在进度条填充区域显示（浅色） */
/* 顶层文字 - 在进度条填充区域显示（浅色） */
.currentClass::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
  line-height: 2rem;
  color: rgb(var(--mdui-color-on-primary));
  font-size: 1rem;
  font-weight: 500;
  white-space: nowrap;
  text-align: center;
  pointer-events: none;
  z-index: 2;
  /* 统一字体渲染，修复高DPI设备上的对齐问题 */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: geometricPrecision;
  transform: translateZ(0);
  backface-visibility: hidden;
  /* 使用像素值精确裁剪，与进度条填充位置完全对应 */
  -webkit-mask-image: linear-gradient(
    to right,
    black var(--progress-fill-px, 0px),
    transparent var(--progress-fill-px, 0px)
  );
  mask-image: linear-gradient(
    to right,
    black var(--progress-fill-px, 0px),
    transparent var(--progress-fill-px, 0px)
  );
}

#mini-progress {
  width: 100%;
  height: calc(100% - 4px);
  border-radius: 8px;
  margin-top: 4px;
  border: 1px solid rgba(var(--mdui-color-on-surface), 0.3);
}

@media (max-width: 800px) {
  .currentClass {
    width: 10rem;
    height: 1.8rem;
  }

  .currentClass::before {
    line-height: 1.8rem;
    font-size: 0.9rem;
  }

  .currentClass::after {
    line-height: 1.8rem;
    font-size: 0.9rem;
  }
}
</style>