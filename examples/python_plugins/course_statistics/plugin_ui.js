/**
 * Course Statistics Plugin Frontend Component
 *
 * Displays statistics dashboard and configuration interface
 */

export default {
  name: 'CourseStatisticsSettings',

  data() {
    return {
      stats: {
        total_courses: 0,
        courses_by_teacher: {},
        courses_by_location: {},
        schedule_entries_per_day: {},
        total_class_hours: 0,
        busiest_day: 0,
        timestamp: ''
      },
      config: {
        update_interval: 300,
        enable_notifications: true,
        min_class_hours: 0
      },
      loading: false
    }
  },

  async mounted() {
    // Load initial data
    await this.loadStatistics();
    await this.loadConfig();

    // Subscribe to statistics updates
    this.$classtop.plugins.on('statistics_updated', this.onStatisticsUpdate);
  },

  beforeUnmount() {
    // Unsubscribe from events
    this.$classtop.plugins.off('statistics_updated', this.onStatisticsUpdate);
  },

  computed: {
    teacherChartData() {
      return Object.entries(this.stats.courses_by_teacher).map(([teacher, count]) => ({
        teacher,
        count
      }));
    },

    locationChartData() {
      return Object.entries(this.stats.courses_by_location).map(([location, count]) => ({
        location,
        count
      }));
    },

    weekdayNames() {
      return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    },

    busiestDayName() {
      const day = this.stats.busiest_day;
      return day > 0 && day <= 7 ? this.weekdayNames[day - 1] : 'N/A';
    }
  },

  methods: {
    async loadStatistics() {
      try {
        this.loading = true;
        const stats = await this.$classtop.plugins.getData('com.example.course_statistics', 'stats');
        if (stats) {
          this.stats = stats;
        }
      } catch (error) {
        mdui.snackbar({ message: 'Failed to load statistics: ' + error.message });
      } finally {
        this.loading = false;
      }
    },

    async loadConfig() {
      try {
        const config = await this.$classtop.plugins.getData('com.example.course_statistics', 'config');
        if (config) {
          this.config = config;
        }
      } catch (error) {
        console.error('Failed to load config:', error);
      }
    },

    async saveConfig() {
      try {
        await this.$classtop.plugins.setData('com.example.course_statistics', 'config', this.config);
        mdui.snackbar({ message: 'Configuration saved successfully' });
      } catch (error) {
        mdui.snackbar({ message: 'Failed to save configuration: ' + error.message });
      }
    },

    async refreshStatistics() {
      try {
        this.loading = true;
        // Trigger recalculation by emitting event
        await this.$classtop.plugins.invoke('com.example.course_statistics', 'refresh_statistics');
        await this.loadStatistics();
        mdui.snackbar({ message: 'Statistics refreshed' });
      } catch (error) {
        mdui.snackbar({ message: 'Failed to refresh statistics: ' + error.message });
      } finally {
        this.loading = false;
      }
    },

    onStatisticsUpdate(stats) {
      // Update statistics when backend emits update event
      this.stats = stats;
    }
  },

  template: `
    <div class="statistics-plugin">
      <h3>Course Statistics</h3>

      <!-- Summary Cards -->
      <div class="stats-summary">
        <mdui-card class="stat-card">
          <mdui-card-content>
            <div class="stat-number">{{ stats.total_courses }}</div>
            <div class="stat-label">Total Courses</div>
          </mdui-card-content>
        </mdui-card>

        <mdui-card class="stat-card">
          <mdui-card-content>
            <div class="stat-number">{{ stats.total_class_hours.toFixed(1) }}</div>
            <div class="stat-label">Hours per Week</div>
          </mdui-card-content>
        </mdui-card>

        <mdui-card class="stat-card">
          <mdui-card-content>
            <div class="stat-number">{{ busiestDayName }}</div>
            <div class="stat-label">Busiest Day</div>
          </mdui-card-content>
        </mdui-card>
      </div>

      <!-- Refresh Button -->
      <mdui-button
        variant="outlined"
        @click="refreshStatistics"
        :loading="loading"
        style="margin: 16px 0;"
      >
        Refresh Statistics
      </mdui-button>

      <!-- Teachers Distribution -->
      <h4>Courses by Teacher</h4>
      <mdui-list>
        <mdui-list-item v-for="(count, teacher) in stats.courses_by_teacher" :key="teacher">
          <mdui-list-item-text>
            {{ teacher }}: {{ count }} course(s)
          </mdui-list-item-text>
        </mdui-list-item>
      </mdui-list>

      <!-- Locations Distribution -->
      <h4>Courses by Location</h4>
      <mdui-list>
        <mdui-list-item v-for="(count, location) in stats.courses_by_location" :key="location">
          <mdui-list-item-text>
            {{ location }}: {{ count }} course(s)
          </mdui-list-item-text>
        </mdui-list-item>
      </mdui-list>

      <!-- Configuration -->
      <h4>Plugin Configuration</h4>

      <mdui-text-field
        label="Update Interval (seconds)"
        v-model.number="config.update_interval"
        type="number"
        min="60"
        max="3600"
        helper="How often to recalculate statistics"
      ></mdui-text-field>

      <mdui-switch v-model="config.enable_notifications" style="margin: 16px 0;">
        Enable Notifications
      </mdui-switch>

      <mdui-button variant="filled" @click="saveConfig">
        Save Configuration
      </mdui-button>

      <div class="last-update" style="margin-top: 24px; color: var(--mdui-color-on-surface-variant);">
        Last updated: {{ stats.timestamp || 'Never' }}
      </div>
    </div>
  `,

  styles: `
    <style scoped>
    .statistics-plugin {
      padding: 16px;
    }

    .stats-summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin: 16px 0;
    }

    .stat-card {
      text-align: center;
      padding: 16px;
    }

    .stat-number {
      font-size: 2em;
      font-weight: bold;
      color: var(--mdui-color-primary);
    }

    .stat-label {
      font-size: 0.9em;
      color: var(--mdui-color-on-surface-variant);
      margin-top: 8px;
    }

    h4 {
      margin: 24px 0 12px 0;
      color: var(--mdui-color-on-surface);
    }

    .last-update {
      font-size: 0.85em;
      font-style: italic;
    }
    </style>
  `
};
