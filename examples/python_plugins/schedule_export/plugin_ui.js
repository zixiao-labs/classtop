/**
 * Schedule Export Plugin Frontend Component
 *
 * Provides user interface for exporting schedules
 */

export default {
  name: 'ScheduleExportSettings',

  data() {
    return {
      config: {
        default_format: 'csv',
        include_teacher: true,
        include_location: true,
        export_all_weeks: false
      },
      exportFormat: 'csv',
      exportWeek: null,
      exporting: false,
      lastExport: null
    }
  },

  async mounted() {
    // Load configuration
    await this.loadConfig();

    // Get current week as default
    try {
      const weekInfo = await this.$classtop.invoke('get_current_week');
      this.exportWeek = weekInfo.week;
    } catch (error) {
      console.error('Failed to get current week:', error);
    }

    // Subscribe to export events
    this.$classtop.plugins.on('schedule_exported', this.onExportComplete);
  },

  beforeUnmount() {
    this.$classtop.plugins.off('schedule_exported', this.onExportComplete);
  },

  methods: {
    async loadConfig() {
      try {
        const config = await this.$classtop.plugins.getData('com.example.schedule_export', 'config');
        if (config) {
          this.config = config;
          this.exportFormat = config.default_format;
        }
      } catch (error) {
        console.error('Failed to load config:', error);
      }
    },

    async saveConfig() {
      try {
        await this.$classtop.plugins.setData('com.example.schedule_export', 'config', this.config);
        mdui.snackbar({ message: 'Configuration saved' });
      } catch (error) {
        mdui.snackbar({ message: 'Failed to save configuration: ' + error.message });
      }
    },

    async exportSchedule() {
      try {
        this.exporting = true;

        // Call plugin export method
        const filepath = await this.$classtop.plugins.invoke(
          'com.example.schedule_export',
          'export_schedule',
          {
            export_format: this.exportFormat,
            week: this.exportWeek
          }
        );

        mdui.snackbar({
          message: `Exported successfully to: ${filepath}`,
          action: 'Open Folder',
          onActionClick: () => {
            // Open file location (requires shell command)
            this.openExportFolder();
          }
        });

      } catch (error) {
        mdui.snackbar({ message: 'Export failed: ' + error.message });
      } finally {
        this.exporting = false;
      }
    },

    openExportFolder() {
      // This would require a Tauri command to open the folder
      // For now, just show the path
      const exportPath = `${this.getHomePath()}/.classtop/exports`;
      mdui.snackbar({ message: `Export folder: ${exportPath}` });
    },

    getHomePath() {
      // Platform-specific home directory
      return navigator.platform.startsWith('Win') ? '%USERPROFILE%' : '~';
    },

    onExportComplete(data) {
      this.lastExport = {
        format: data.format,
        filename: data.filename,
        week: data.week,
        timestamp: new Date().toLocaleString()
      };
    }
  },

  template: `
    <div class="schedule-export-plugin">
      <h3>Schedule Export</h3>
      <p>Export your class schedule to various formats</p>

      <!-- Export Form -->
      <mdui-card style="margin: 16px 0; padding: 16px;">
        <h4>Export Settings</h4>

        <mdui-select
          label="Export Format"
          v-model="exportFormat"
          style="width: 100%; margin-bottom: 16px;"
        >
          <mdui-menu-item value="csv">CSV (Comma-Separated Values)</mdui-menu-item>
          <mdui-menu-item value="json">JSON (JavaScript Object Notation)</mdui-menu-item>
          <mdui-menu-item value="ical">iCal (Calendar Format)</mdui-menu-item>
        </mdui-select>

        <mdui-text-field
          label="Week Number"
          v-model.number="exportWeek"
          type="number"
          min="1"
          max="52"
          helper="Leave empty for current week"
          style="width: 100%; margin-bottom: 16px;"
        ></mdui-text-field>

        <mdui-button
          variant="filled"
          @click="exportSchedule"
          :loading="exporting"
          style="width: 100%;"
        >
          Export Schedule
        </mdui-button>
      </mdui-card>

      <!-- Last Export Info -->
      <mdui-card v-if="lastExport" style="margin: 16px 0; padding: 16px; background: var(--mdui-color-surface-container);">
        <h4>Last Export</h4>
        <mdui-list>
          <mdui-list-item>
            <mdui-list-item-text>
              Format: {{ lastExport.format.toUpperCase() }}
            </mdui-list-item-text>
          </mdui-list-item>
          <mdui-list-item>
            <mdui-list-item-text>
              Filename: {{ lastExport.filename }}
            </mdui-list-item-text>
          </mdui-list-item>
          <mdui-list-item>
            <mdui-list-item-text>
              Week: {{ lastExport.week }}
            </mdui-list-item-text>
          </mdui-list-item>
          <mdui-list-item>
            <mdui-list-item-text>
              Time: {{ lastExport.timestamp }}
            </mdui-list-item-text>
          </mdui-list-item>
        </mdui-list>
      </mdui-card>

      <!-- Configuration -->
      <h4>Plugin Configuration</h4>

      <mdui-select
        label="Default Export Format"
        v-model="config.default_format"
        style="width: 100%; margin-bottom: 16px;"
      >
        <mdui-menu-item value="csv">CSV</mdui-menu-item>
        <mdui-menu-item value="json">JSON</mdui-menu-item>
        <mdui-menu-item value="ical">iCal</mdui-menu-item>
      </mdui-select>

      <mdui-switch v-model="config.include_teacher" style="margin: 8px 0;">
        Include Teacher Information
      </mdui-switch>

      <mdui-switch v-model="config.include_location" style="margin: 8px 0;">
        Include Location Information
      </mdui-switch>

      <mdui-button variant="outlined" @click="saveConfig" style="margin-top: 16px;">
        Save Configuration
      </mdui-button>

      <!-- Export Location Info -->
      <mdui-card style="margin-top: 24px; padding: 16px; background: var(--mdui-color-tertiary-container);">
        <h4 style="margin-top: 0;">Export Location</h4>
        <p style="font-family: monospace; font-size: 0.9em;">
          {{ getHomePath() }}/.classtop/exports/
        </p>
        <p style="font-size: 0.85em; color: var(--mdui-color-on-surface-variant);">
          Exported files are saved to this directory on your computer.
        </p>
      </mdui-card>
    </div>
  `
};
