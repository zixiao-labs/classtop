/**
 * TopBar Theme Presets and Utilities
 * TopBar 主题预设和工具函数
 */

// TopBar 主题预设
export const topbarThemePresets = {
  default: {
    name: '默认',
    description: '经典蓝色主题',
    background_color: '#1976d2',
    background_opacity: '90',
    text_color: '#ffffff',
    blur_strength: '10',
    border_radius: '12',
    shadow_enabled: 'true',
    font_family: 'system-ui',
    font_weight: '400',
    font_size_multiplier: '1.0',
    layout: 'default',
    show_icons: 'true',
    component_spacing: '16'
  },
  dark: {
    name: '深色模式',
    description: '深邃黑色主题',
    background_color: '#1c1c1e',
    background_opacity: '95',
    text_color: '#ffffff',
    blur_strength: '20',
    border_radius: '16',
    shadow_enabled: 'true',
    font_family: 'system-ui',
    font_weight: '300',
    font_size_multiplier: '1.0',
    layout: 'default',
    show_icons: 'true',
    component_spacing: '16'
  },
  light: {
    name: '浅色模式',
    description: '明亮清新主题',
    background_color: '#f5f5f7',
    background_opacity: '85',
    text_color: '#1c1c1e',
    blur_strength: '15',
    border_radius: '12',
    shadow_enabled: 'true',
    font_family: 'system-ui',
    font_weight: '400',
    font_size_multiplier: '1.0',
    layout: 'default',
    show_icons: 'true',
    component_spacing: '16'
  },
  eyecare: {
    name: '护眼模式',
    description: '温和绿色主题',
    background_color: '#c7edcc',
    background_opacity: '90',
    text_color: '#2d5016',
    blur_strength: '5',
    border_radius: '8',
    shadow_enabled: 'false',
    font_family: 'system-ui',
    font_weight: '400',
    font_size_multiplier: '1.1',
    layout: 'default',
    show_icons: 'true',
    component_spacing: '20'
  },
  neon: {
    name: '霓虹灯',
    description: '炫彩渐变主题',
    background_color: '#6200ea',
    background_opacity: '85',
    text_color: '#00e5ff',
    blur_strength: '25',
    border_radius: '20',
    shadow_enabled: 'true',
    font_family: 'system-ui',
    font_weight: '500',
    font_size_multiplier: '1.0',
    layout: 'default',
    show_icons: 'true',
    component_spacing: '18'
  },
  minimal: {
    name: '极简',
    description: '简洁透明主题',
    background_color: '#ffffff',
    background_opacity: '50',
    text_color: '#000000',
    blur_strength: '30',
    border_radius: '0',
    shadow_enabled: 'false',
    font_family: 'system-ui',
    font_weight: '300',
    font_size_multiplier: '0.9',
    layout: 'minimal',
    show_icons: 'false',
    component_spacing: '12'
  }
};

/**
 * 应用 MDUI 动态主题配色到 TopBar
 * 从 MDUI 的 CSS 变量中提取主题色
 */
export function applyMDUIThemeToTopBar() {
  // 获取 MDUI 主色调
  const mduiPrimary = getComputedStyle(document.documentElement)
    .getPropertyValue('--mdui-color-primary')
    .trim();

  if (mduiPrimary) {
    return {
      name: 'MDUI动态配色',
      description: '与MDUI主题色保持一致',
      background_color: mduiPrimary,
      background_opacity: '90',
      text_color: '#ffffff',
      blur_strength: '10',
      border_radius: '12',
      shadow_enabled: 'true',
      font_family: 'system-ui',
      font_weight: '400',
      font_size_multiplier: '1.0',
      layout: 'default',
      show_icons: 'true',
      component_spacing: '16'
    };
  }

  return topbarThemePresets.default;
}

/**
 * 导出主题配置为 JSON
 * @param {Object} settings - 当前设置对象
 * @returns {string} JSON 字符串
 */
export function exportTheme(settings) {
  const theme = {
    name: 'Custom Theme',
    version: '1.0',
    exported_at: new Date().toISOString(),
    background_color: settings.topbar_background_color,
    background_opacity: settings.topbar_background_opacity,
    text_color: settings.topbar_text_color,
    blur_strength: settings.topbar_blur_strength,
    border_radius: settings.topbar_border_radius,
    shadow_enabled: settings.topbar_shadow_enabled,
    font_family: settings.topbar_font_family,
    font_weight: settings.topbar_font_weight,
    font_size_multiplier: settings.topbar_font_size_multiplier,
    layout: settings.topbar_layout,
    show_icons: settings.topbar_show_icons,
    component_spacing: settings.topbar_component_spacing
  };

  return JSON.stringify(theme, null, 2);
}

/**
 * 从 JSON 导入主题配置
 * @param {string} jsonString - JSON 字符串
 * @returns {Object|null} 主题对象或 null（解析失败）
 */
export function importTheme(jsonString) {
  try {
    const theme = JSON.parse(jsonString);

    // 验证必需字段
    const requiredFields = [
      'background_color',
      'background_opacity',
      'text_color',
      'blur_strength',
      'border_radius',
      'shadow_enabled'
    ];

    for (const field of requiredFields) {
      if (!(field in theme)) {
        console.error(`Missing required field: ${field}`);
        return null;
      }
    }

    return theme;
  } catch (error) {
    console.error('Failed to parse theme JSON:', error);
    return null;
  }
}

/**
 * 验证颜色值是否有效
 * @param {string} color - 颜色值（hex 格式）
 * @returns {boolean} 是否有效
 */
export function isValidColor(color) {
  return /^#[0-9A-Fa-f]{6}$/.test(color);
}

/**
 * 将透明度值转换为 hex 格式
 * @param {number|string} opacity - 透明度 (0-100)
 * @returns {string} hex 格式的透明度 (00-FF)
 */
export function opacityToHex(opacity) {
  const opacityNum = typeof opacity === 'string' ? parseInt(opacity) : opacity;
  const alpha = Math.round((opacityNum / 100) * 255);
  return alpha.toString(16).padStart(2, '0').toUpperCase();
}

/**
 * 获取主题预设列表（用于 UI 显示）
 * @returns {Array} 预设列表
 */
export function getThemePresetList() {
  return Object.keys(topbarThemePresets).map(key => ({
    key,
    ...topbarThemePresets[key]
  }));
}
