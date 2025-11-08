/**
 * Global Reactive Variables
 * 全局响应式变量，用于在整个应用中共享状态
 */

import { reactive, watch } from 'vue';
import { setTheme, setColorScheme } from 'mdui';
import { pyInvoke } from 'tauri-plugin-pytauri-api';

// 全局设置状态
export const settings = reactive({
  // 通用设置
  client_uuid: '',
  server_url: '',

  // 外观设置
  theme_mode: 'auto', // 'auto' | 'dark' | 'light'
  theme_color: '#6750A4',

  topbar_height: '3', // 顶栏高度(rem)
  font_size: '16', // 全局字体大小(px)

  // 控制模式: 'touch' | 'mouse'
  control_mode: 'touch',

  // 组件设置
  show_clock: true,
  show_schedule: true,
  show_sync_status: true,

  // 监控（摄像头）设置
  camera_enabled: false,

  // 课程设置
  semester_start_date: '',

  // 课程提醒设置
  reminder_enabled: false,
  reminder_minutes: '10',
  reminder_sound: false,

  // 同步设置
  sync_enabled: 'false',
  sync_interval: '300',
  client_name: '',
  sync_direction: 'upload', // 'upload' | 'download' | 'bidirectional'
  sync_strategy: 'server_wins', // 'server_wins' | 'local_wins' | 'newest_wins'

  // TopBar 主题设置
  topbar_background_color: '#1976d2',
  topbar_background_opacity: '90',
  topbar_text_color: '#ffffff',
  topbar_blur_strength: '10',
  topbar_border_radius: '12',
  topbar_shadow_enabled: 'true',
  topbar_font_family: 'system-ui',
  topbar_font_weight: '400',
  topbar_font_size_multiplier: '1.0',
  topbar_layout: 'default',
  topbar_show_icons: 'true',
  topbar_component_spacing: '16',

  // 动态计算的值（不持久化）
  current_week: 1,

  // 加载状态
  loaded: false,
});

/**
 * 计算当前周数
 */
async function calculateCurrentWeek() {
  try {
    const weekNum = await pyInvoke('get_calculated_week_number');
    return weekNum || 1;
  } catch (error) {
    console.error('Failed to calculate current week:', error);
    return 1;
  }
}

/**
 * 从后端加载所有设置
 */
export async function loadSettings() {
  try {
    const allSettings = await pyInvoke('get_all_settings');

    // 更新设置对象
    settings.client_uuid = allSettings.client_uuid || '';
    settings.server_url = allSettings.server_url || '';
    settings.theme_mode = allSettings.theme_mode || 'auto';
    settings.theme_color = allSettings.theme_color || '#6750A4';
    settings.topbar_height = allSettings.topbar_height || '3';
    settings.font_size = allSettings.font_size || '16';
    settings.show_clock = allSettings.show_clock === 'true';
    settings.show_schedule = allSettings.show_schedule === 'true';
    settings.show_sync_status = allSettings.show_sync_status === 'true';
    // camera_enabled 存储为 'true'/'false'
    settings.camera_enabled = allSettings.camera_enabled === 'true';
    // control_mode 存储为字符串 'touch' 或 'mouse'
    settings.control_mode = allSettings.control_mode || 'touch';
    settings.semester_start_date = allSettings.semester_start_date || '';

    // 课程提醒设置（转换为布尔值以保持一致性）
    settings.reminder_enabled = allSettings.reminder_enabled === 'true';
    settings.reminder_minutes = allSettings.reminder_minutes || '10';
    settings.reminder_sound = allSettings.reminder_sound === 'true';

    // 同步设置
    settings.sync_enabled = allSettings.sync_enabled || 'false';
    settings.sync_interval = allSettings.sync_interval || '300';
    settings.client_name = allSettings.client_name || '';
    settings.sync_direction = allSettings.sync_direction || 'upload';
    settings.sync_strategy = allSettings.sync_strategy || 'server_wins';

    // TopBar 主题设置
    settings.topbar_background_color = allSettings.topbar_background_color || '#1976d2';
    settings.topbar_background_opacity = allSettings.topbar_background_opacity || '90';
    settings.topbar_text_color = allSettings.topbar_text_color || '#ffffff';
    settings.topbar_blur_strength = allSettings.topbar_blur_strength || '10';
    settings.topbar_border_radius = allSettings.topbar_border_radius || '12';
    settings.topbar_shadow_enabled = allSettings.topbar_shadow_enabled || 'true';
    settings.topbar_font_family = allSettings.topbar_font_family || 'system-ui';
    settings.topbar_font_weight = allSettings.topbar_font_weight || '400';
    settings.topbar_font_size_multiplier = allSettings.topbar_font_size_multiplier || '1.0';
    settings.topbar_layout = allSettings.topbar_layout || 'default';
    settings.topbar_show_icons = allSettings.topbar_show_icons || 'true';
    settings.topbar_component_spacing = allSettings.topbar_component_spacing || '16';

    settings.loaded = true;

    // 动态计算当前周数
    settings.current_week = await calculateCurrentWeek();

    console.log('Settings loaded:', allSettings);

    // 应用主题设置
    applyTheme();
  } catch (error) {
    console.error('Failed to load settings:', error);
  }
}

/**
 * 保存单个设置到后端
 */
export async function saveSetting(key, value) {
  // 禁止保存 current_week（应该通过 semester_start_date 计算）
  if (key === 'current_week') {
    console.warn('current_week is calculated from semester_start_date and cannot be set directly');
    return false;
  }

  try {
    // 转换布尔值为字符串
    const stringValue = typeof value === 'boolean' ? (value ? 'true' : 'false') : String(value);

    await pyInvoke('set_config', { key, value: stringValue });

    // 更新本地状态
    if (key in settings) {
      settings[key] = value;
    }

    // 如果更新了 semester_start_date，重新计算 current_week
    if (key === 'semester_start_date') {
      settings.current_week = await calculateCurrentWeek();
    }

    console.log(`Setting saved: ${key} = ${value}`);
    return true;
  } catch (error) {
    console.error(`Failed to save setting ${key}:`, error);
    return false;
  }
}

/**
 * 批量保存设置到后端
 */
export async function saveSettings(settingsToSave) {
  try {
    // 过滤掉 current_week
    const filteredSettings = { ...settingsToSave };
    delete filteredSettings.current_week;

    // 转换所有值为字符串
    const stringSettings = {};
    for (const [key, value] of Object.entries(filteredSettings)) {
      stringSettings[key] = typeof value === 'boolean' ? (value ? 'true' : 'false') : String(value);
    }

    const result = await pyInvoke('update_settings', { settings: stringSettings });

    if (result.success) {
      // 更新本地状态
      Object.assign(settings, filteredSettings);

      // 如果更新了 semester_start_date，重新计算 current_week
      if ('semester_start_date' in filteredSettings) {
        settings.current_week = await calculateCurrentWeek();
      }

      console.log('Settings saved successfully');
      return true;
    }

    return false;
  } catch (error) {
    console.error('Failed to save settings:', error);
    return false;
  }
}

/**
 * 重新生成 UUID
 */
export async function regenerateUUID() {
  try {
    const result = await pyInvoke('regenerate_uuid');
    if (result.success) {
      settings.client_uuid = result.uuid;
      return result.uuid;
    }
    return null;
  } catch (error) {
    console.error('Failed to regenerate UUID:', error);
    return null;
  }
}

/**
 * 重置设置为默认值
 */
export async function resetSettings(excludeKeys = []) {
  try {
    const result = await pyInvoke('reset_settings', { exclude: excludeKeys });
    if (result.success) {
      // 重新加载设置
      await loadSettings();
      return true;
    }
    return false;
  } catch (error) {
    console.error('Failed to reset settings:', error);
    return false;
  }
}

/**
 * 应用主题设置
 */
export function applyTheme() {
  // 应用主题模式
  if (settings.theme_mode === 'auto') {
    setTheme('auto');
  } else if (settings.theme_mode === 'dark') {
    setTheme('dark');
  } else if (settings.theme_mode === 'light') {
    setTheme('light');
  }

  // 应用主题颜色
  if (settings.theme_color && settings.theme_color !== '#6750A4') {
    applyColorScheme();
  }

  // 应用字体大小
  applyFontSize();
}

/**
 * 应用字体大小设置
 */
export function applyFontSize() {
  try {
    const fontSize = settings.font_size || '16';
    document.documentElement.style.fontSize = `${fontSize}px`;
    console.log(`Font size applied: ${fontSize}px`);
  } catch (error) {
    console.error('Failed to apply font size:', error);
  }
}

/**
 * 应用颜色主题（限流，避免频繁调用）
 */
export const applyColorScheme = async () => {
  try {
    if (settings.theme_color && settings.theme_color !== '#6750A4') {
      setColorScheme(settings.theme_color);
    }
  } catch (error) {
    console.error('Failed to apply color scheme:', error);
  }
}

/**
 * 切换主题模式
 */
export async function setThemeMode(mode) {
  settings.theme_mode = mode;
  applyTheme();
  await saveSetting('theme_mode', mode);
}

// 监听主题变化，自动应用
watch(() => settings.theme_mode, () => {
  if (settings.loaded) {
    applyTheme();
  }
});
watch(() => settings.theme_color, () => {
  if (settings.loaded) {
    applyColorScheme();
  }
});
watch(() => settings.font_size, () => {
  if (settings.loaded) {
    applyFontSize();
  }
});

// 其他全局状态（非持久化）
export const appState = reactive({
  // 窗口状态
  isMainWindowVisible: true,
  isTopBarVisible: false,

  // 网络状态
  isOnline: true,

  // 加载状态
  isLoading: false,
});