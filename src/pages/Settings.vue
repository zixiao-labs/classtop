<template>
  <div class="settings mdui-prose">
    <h1>设置</h1>

    <!-- 通用设置 -->
    <mdui-card class="settings-group">
      <span class="group-title">通用</span>
      <mdui-divider></mdui-divider>
      <mdui-list>
        <mdui-list-item icon="perm_device_information" rounded nonclickable>
          客户端UUID
          <div style="display: flex; align-items: center; gap: 8px;" slot="end-icon">
            <code style="font-size: 0.875rem; user-select: all;">{{ settings.client_uuid }}</code>
            <mdui-button-icon icon="content_copy" @click="copyUUID"></mdui-button-icon>
            <mdui-button variant="text" @click="handleRegenerateUUID">重新生成</mdui-button>
          </div>
        </mdui-list-item>
        <mdui-list-item icon="dns" rounded nonclickable>
          服务器地址
          <mdui-text-field style="height: 53px; min-width: 300px;" type="url" variant="filled" label="后端服务器地址"
            :value="settings.server_url" @input="settings.server_url = $event.target.value"
            @blur="saveSetting('server_url', settings.server_url)" slot="end-icon">
          </mdui-text-field>
        </mdui-list-item>
        <mdui-list-item icon="mouse" rounded nonclickable>
          控制模式
          <mdui-segmented-button-group selects="single" :value="settings.control_mode" @change="handleControlModeChange"
            slot="end-icon">
            <mdui-segmented-button value="touch" icon="touch_app">触摸屏</mdui-segmented-button>
            <mdui-segmented-button value="mouse" icon="mouse">鼠标</mdui-segmented-button>
          </mdui-segmented-button-group>
        </mdui-list-item>
      </mdui-list>
    </mdui-card>

    <!-- 外观设置 -->
    <mdui-card class="settings-group">
      <span class="group-title">外观</span>
      <mdui-divider></mdui-divider>
      <mdui-list>
        <mdui-list-item icon="dark_mode" rounded nonclickable>
          明暗主题
          <mdui-segmented-button-group selects="single" :value="settings.theme_mode" @change="handleThemeModeChange"
            slot="end-icon">
            <mdui-segmented-button value="auto">跟随系统</mdui-segmented-button>
            <mdui-segmented-button value="dark">深色</mdui-segmented-button>
            <mdui-segmented-button value="light">浅色</mdui-segmented-button>
          </mdui-segmented-button-group>
        </mdui-list-item>
        <mdui-list-item icon="color_lens" rounded nonclickable>
          主题颜色
          <div slot="end-icon" style="display: flex; align-items: center; gap: 8px;">
            <input type="color" :value="settings.theme_color" @change="handleColorChange"
              style="width: 48px; height: 36px; border: none; border-radius: 4px; cursor: pointer;">
            <span style="font-family: monospace; font-size: 0.875rem;">{{ settings.theme_color }}</span>
          </div>
        </mdui-list-item>
        <mdui-list-item icon="image" rounded nonclickable>
          动态主题
          <div slot="end-icon" style="display: flex; align-items: center; gap: 8px;">
            <mdui-button variant="outlined" @click="handleDownloadTheme" :disabled="isDownloadingTheme">
              {{ isDownloadingTheme ? '下载中...' : '从GitHub随机下载' }}
            </mdui-button>
            <span v-if="settings.theme_image_name" style="font-size: 0.75rem; color: var(--mdui-color-on-surface-variant);">
              {{ settings.theme_image_name }}
            </span>
          </div>
        </mdui-list-item>
        <mdui-list-item icon="autorenew" rounded>
          启动时自动更新主题
          <mdui-switch :checked="settings.auto_theme_download" @change="handleSwitchChange('auto_theme_download', $event)"
            slot="end-icon">
          </mdui-switch>
        </mdui-list-item>
        <mdui-list-item icon="height" rounded nonclickable>
          顶栏高度
          <mdui-slider min="0" max="8" step="0.1" :value="settings.topbar_height" id="topbar-height-slider"
            @change="saveSetting('topbar_height', Number($event.target.value).toFixed(1))" style="width: 13rem;"
            slot="end-icon"></mdui-slider>
        </mdui-list-item>
        <mdui-list-item icon="format_size" rounded nonclickable>
          字体大小
          <mdui-slider min="0" max="12" step="1" :value="settings.font_size - 12" id="font-size-slider"
            @change="handleFontSizeChange(Number($event.target.value) + 12)" style="width: 13rem;"
            slot="end-icon"></mdui-slider>
        </mdui-list-item>
      </mdui-list>
    </mdui-card>

    <!-- 组件设置 -->
    <mdui-card class="settings-group">
      <span class="group-title">组件显示</span>
      <mdui-divider></mdui-divider>
      <mdui-list>
        <mdui-list-item icon="access_time" rounded>
          时间显示
          <mdui-switch :checked="settings.show_clock" @change="handleSwitchChange('show_clock', $event)"
            slot="end-icon">
          </mdui-switch>
        </mdui-list-item>
        <mdui-list-item icon="book" rounded>
          课程表
          <mdui-switch :checked="settings.show_schedule" @change="handleSwitchChange('show_schedule', $event)"
            slot="end-icon">
          </mdui-switch>
        </mdui-list-item>
      </mdui-list>
    </mdui-card>

    <!-- 监控设置 -->
    <mdui-card class="settings-group">
      <span class="group-title">监控设置</span>
      <mdui-divider></mdui-divider>
      <mdui-list>
        <mdui-list-item icon="videocam" rounded>
          启用摄像头功能
          <mdui-switch :checked="settings.camera_enabled" @change="handleSwitchChange('camera_enabled', $event)"
            slot="end-icon">
          </mdui-switch>
        </mdui-list-item>
      </mdui-list>
    </mdui-card>

    <!-- 课程设置 -->
    <mdui-card class="settings-group">
      <span class="group-title">课程</span>
      <mdui-divider></mdui-divider>
      <mdui-list>
        <mdui-list-item icon="event" rounded nonclickable>
          学期开始日期
          <mdui-text-field type="date" variant="filled" label="开始日期" :value="settings.semester_start_date"
            @input="settings.semester_start_date = $event.target.value"
            @blur="saveSetting('semester_start_date', settings.semester_start_date)" slot="end-icon"
            style="width: 200px;">
          </mdui-text-field>
        </mdui-list-item>
      </mdui-list>
    </mdui-card>

    <!-- 课程提醒设置 -->
    <mdui-card class="settings-group">
      <span class="group-title">课程提醒</span>
      <mdui-divider></mdui-divider>
      <mdui-list>
        <mdui-list-item icon="notifications" rounded>
          启用课程提醒
          <mdui-switch :checked="settings.reminder_enabled" @change="handleSwitchChange('reminder_enabled', $event)"
            slot="end-icon">
          </mdui-switch>
        </mdui-list-item>
        <mdui-list-item icon="schedule" rounded nonclickable :disabled="settings.reminder_enabled !== 'true'">
          提前提醒时间
          <mdui-segmented-button-group selects="single" :value="settings.reminder_minutes || '10'"
            @change="handleReminderTimeChange" slot="end-icon">
            <mdui-segmented-button value="5">5分钟</mdui-segmented-button>
            <mdui-segmented-button value="10">10分钟</mdui-segmented-button>
            <mdui-segmented-button value="15">15分钟</mdui-segmented-button>
            <mdui-segmented-button value="30">30分钟</mdui-segmented-button>
          </mdui-segmented-button-group>
        </mdui-list-item>
        <mdui-list-item icon="volume_up" rounded :disabled="settings.reminder_enabled !== 'true'">
          提示音
          <mdui-switch :checked="settings.reminder_sound" @change="handleSwitchChange('reminder_sound', $event)"
            slot="end-icon">
          </mdui-switch>
        </mdui-list-item>
      </mdui-list>
    </mdui-card>

    <!-- 数据导入/导出 -->
    <mdui-card class="settings-group">
      <span class="group-title">数据管理</span>
      <mdui-divider></mdui-divider>
      <mdui-list>
        <mdui-list-item icon="file_download" rounded nonclickable>
          导出课程表
          <div slot="end-icon" style="display: flex; gap: 8px;">
            <mdui-button variant="outlined" @click="handleExport('json')">导出为 JSON</mdui-button>
            <mdui-button variant="outlined" @click="handleExport('csv')">导出为 CSV</mdui-button>
          </div>
        </mdui-list-item>
        <mdui-list-item icon="file_upload" rounded nonclickable>
          导入课程表
          <div slot="end-icon" style="display: flex; gap: 8px;">
            <mdui-button variant="outlined" @click="handleImport('json')">从 JSON 导入</mdui-button>
            <mdui-button variant="outlined" @click="handleImport('csv')">从 CSV 导入</mdui-button>
          </div>
        </mdui-list-item>
      </mdui-list>
    </mdui-card>

    <!-- 操作按钮 -->
    <div class="actions">
      <mdui-button variant="outlined" @click="handleResetSettings">重置所有设置</mdui-button>
      <mdui-button @click="handleSaveAll">保存所有设置</mdui-button>
    </div>
  </div>
</template>

<script setup>
import { snackbar } from 'mdui';
import { writeText, readText } from '@tauri-apps/plugin-clipboard-manager';
import { save, open } from '@tauri-apps/plugin-dialog';
import { writeTextFile, readTextFile } from '@tauri-apps/plugin-fs';
import { settings, saveSetting, saveSettings, regenerateUUID, resetSettings, setThemeMode, applyColorScheme } from '../utils/globalVars';
import { exportScheduleData, importScheduleData } from '../utils/schedule';
import { initThemeFromGitHub } from '../utils/theme';
import { onMounted, ref } from 'vue';

// Reactive state for theme download
const isDownloadingTheme = ref(false);

// 控制模式切换处理（触摸/鼠标）
async function handleControlModeChange(event) {
  const value = event.target.value || settings.control_mode;
  settings.control_mode = value;
  await saveSetting('control_mode', value);
  snackbar({ message: `控制模式已切换为：${value === 'touch' ? '触摸屏' : '鼠标'}`, placement: 'top' });
}

// 复制 UUID
async function copyUUID() {
  try {
    await writeText(settings.client_uuid);
    snackbar({ message: 'UUID 已复制到剪贴板', placement: 'top' });
  } catch (error) {
    console.error('Failed to copy UUID:', error);
    snackbar({ message: '复制失败', placement: 'top' });
  }
}

// 重新生成 UUID
async function handleRegenerateUUID() {
  const newUUID = await regenerateUUID();
  if (newUUID) {
    snackbar({ message: 'UUID 已重新生成', placement: 'top' });
  } else {
    snackbar({ message: 'UUID 生成失败', placement: 'top' });
  }
}

// 主题模式切换
async function handleThemeModeChange(event) {
  if (event.target.value) {
    await setThemeMode(event.target.value);
  } else {
    await setThemeMode(settings.theme_mode);
  }

  snackbar({ message: `主题已切换为：${settings.theme_mode === 'auto' ? '跟随系统' : settings.theme_mode === 'dark' ? '深色' : '浅色'}`, placement: 'top' });
}

// 颜色选择
async function handleColorChange(event) {
  settings.theme_color = event.target.value;
  await saveSetting('theme_color', settings.theme_color);
  applyColorScheme(settings.theme_color);
  snackbar({ message: '主题颜色已更新', placement: 'top' });
}

// 从GitHub下载动态主题
async function handleDownloadTheme() {
  isDownloadingTheme.value = true;
  try {
    const result = await initThemeFromGitHub();

    if (result.success) {
      // Update settings with new theme info
      settings.theme_color = result.color;
      settings.theme_image_name = result.imageName;

      snackbar({
        message: `主题已更新！来自图片: ${result.imageName}`,
        placement: 'top'
      });
    } else {
      snackbar({
        message: `主题更新失败: ${result.message}`,
        placement: 'top'
      });
    }
  } catch (error) {
    console.error('Failed to download theme:', error);
    snackbar({
      message: `主题更新失败: ${error.message}`,
      placement: 'top'
    });
  } finally {
    isDownloadingTheme.value = false;
  }
}

// 字体大小调整
async function handleFontSizeChange(size) {
  await saveSetting('font_size', size);
  snackbar({ message: '字体大小已更新', placement: 'top' });
}

// 开关切换
async function handleSwitchChange(key, event) {
  const checked = event.target.checked;
  settings[key] = checked;
  await saveSetting(key, checked);
  snackbar({ message: '设置已更新', placement: 'top' });
}

// 提醒时间切换
async function handleReminderTimeChange(event) {
  const value = event.target.value || settings.reminder_minutes;
  settings.reminder_minutes = value;
  await saveSetting('reminder_minutes', value);
  snackbar({ message: `提醒时间已设置为提前${value}分钟`, placement: 'top' });
}


// 保存所有设置
async function handleSaveAll() {
  const success = await saveSettings({
    server_url: settings.server_url,
    theme_mode: settings.theme_mode,
    theme_color: settings.theme_color,
    topbar_height: settings.topbar_height,
    font_size: settings.font_size,
    show_clock: settings.show_clock,
    show_schedule: settings.show_schedule,
    camera_enabled: settings.camera_enabled,
    control_mode: settings.control_mode,
    semester_start_date: settings.semester_start_date,
    reminder_enabled: settings.reminder_enabled,
    reminder_minutes: settings.reminder_minutes,
    reminder_sound: settings.reminder_sound,
  });

  if (success) {
    snackbar({ message: '所有设置已保存', placement: 'top' });
  } else {
    snackbar({ message: '保存失败', placement: 'top' });
  }
}

// 重置所有设置
async function handleResetSettings() {
  // 排除 UUID，不重置
  const success = await resetSettings(['client_uuid']);
  if (success) {
    snackbar({ message: '设置已重置为默认值', placement: 'top' });
  } else {
    snackbar({ message: '重置失败', placement: 'top' });
  }
}

// 导出课程表
async function handleExport(format) {
  try {
    const result = await exportScheduleData(format, true, true, false);

    if (!result.success || !result.data) {
      snackbar({ message: result.message || '导出失败', placement: 'top' });
      return;
    }

    // 选择保存文件路径
    const extension = format === 'json' ? '.json' : '.csv';
    const defaultName = `课程表_${new Date().toISOString().split('T')[0]}${extension}`;

    const filePath = await save({
      defaultPath: defaultName,
      filters: [{
        name: format.toUpperCase(),
        extensions: [format]
      }]
    });

    if (!filePath) {
      // 用户取消了保存
      return;
    }

    // 写入文件
    await writeTextFile(filePath, result.data);
    snackbar({ message: `课程表已导出到: ${filePath}`, placement: 'top' });

  } catch (error) {
    console.error('Export error:', error);
    snackbar({ message: `导出失败: ${error.message}`, placement: 'top' });
  }
}

// 导入课程表
async function handleImport(format) {
  try {
    // 选择文件
    const filePath = await open({
      multiple: false,
      filters: [{
        name: format.toUpperCase(),
        extensions: [format]
      }]
    });

    if (!filePath) {
      // 用户取消了选择
      return;
    }

    // 读取文件内容
    const fileContent = await readTextFile(filePath);

    // 导入数据
    const result = await importScheduleData(format, fileContent, false);

    if (result.success) {
      snackbar({
        message: `${result.message}\n导入了 ${result.courses_imported} 门课程和 ${result.schedule_imported} 条课程表`,
        placement: 'top'
      });
      // 可选：刷新页面或重新加载数据
      setTimeout(() => {
        location.reload();
      }, 2000);
    } else {
      snackbar({ message: result.message || '导入失败', placement: 'top' });
    }

  } catch (error) {
    console.error('Import error:', error);
    snackbar({ message: `导入失败: ${error.message}`, placement: 'top' });
  }
}

onMounted(() => {
  const slider = document.getElementById('topbar-height-slider');
  if (slider) {
    slider.labelFormatter = (value) => {
      return `${Number(value).toFixed(1)} rem`;
    };
  }

  const fontSizeSlider = document.getElementById('font-size-slider');
  if (fontSizeSlider) {
    fontSizeSlider.labelFormatter = (value) => {
      return `${Number(value) + 12} px`;
    };
  }
})

</script>

<style lang="less" scoped>
.settings {
  padding: .8rem;
  max-width: 1200px;
  margin: 0 auto;
}

.settings-group {
  margin-top: 1rem;
  padding: 1rem;
  width: 100%;

  .group-title {
    font-size: 1.5rem;
    font-weight: 400;
  }

  mdui-divider {
    margin: .3rem 0 .8rem 0;
  }

  mdui-list {
    width: 100%;
  }

  mdui-list-item {
    margin-bottom: 0.5rem;
  }
}

.actions {
  margin-top: 2rem;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

code {
  background-color: rgba(var(--mdui-color-surface-variant), 0.5);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}
</style>