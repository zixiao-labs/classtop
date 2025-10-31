/**
 * Theme utilities for dynamic color scheme management
 */
import { getColorFromImage } from 'mdui/functions/getColorFromImage.js';
import { setColorScheme } from 'mdui/functions/setColorScheme.js';
import { downloadRandomThemeImage } from './schedule.js';
import { pyInvoke } from 'tauri-plugin-pytauri-api';

/**
 * Initialize theme from a random GitHub image
 */
export async function initThemeFromGitHub() {
  try {
    console.log('Initializing theme from GitHub...');

    // Download random image from GitHub
    const result = await downloadRandomThemeImage();

    if (!result.success || !result.image_data) {
      console.error('Failed to download theme image:', result.message);
      return { success: false, message: result.message };
    }

    console.log(`Downloaded theme image: ${result.image_name}`);

    // Convert base64 to Image object
    const image = new Image();
    const imageDataUrl = `data:image/png;base64,${result.image_data}`;

    // Wait for image to load
    await new Promise((resolve, reject) => {
      image.onload = resolve;
      image.onerror = reject;
      image.src = imageDataUrl;
    });

    console.log('Image loaded, extracting color...');

    // Extract color from image
    const color = await getColorFromImage(image);

    console.log(`Extracted color: ${color}`);

    // Apply theme
    setColorScheme(color);

    // Save theme color to settings
    await pyInvoke('set_config', { key: 'theme_color', value: color });
    await pyInvoke('set_config', { key: 'theme_image_name', value: result.image_name });

    console.log('Theme applied successfully');

    return {
      success: true,
      color,
      imageName: result.image_name,
      message: 'Theme applied successfully'
    };
  } catch (error) {
    console.error('Failed to initialize theme:', error);
    return {
      success: false,
      message: `Failed to initialize theme: ${error.message}`
    };
  }
}

/**
 * Apply theme from a color value
 */
export function applyTheme(color) {
  try {
    setColorScheme(color);
    return { success: true, color };
  } catch (error) {
    console.error('Failed to apply theme:', error);
    return { success: false, message: error.message };
  }
}

/**
 * Get saved theme color from settings
 */
export async function getSavedThemeColor() {
  try {
    const result = await pyInvoke('get_config', { key: 'theme_color' });
    return result.value || null;
  } catch (error) {
    console.error('Failed to get saved theme color:', error);
    return null;
  }
}

/**
 * Check if automatic theme download is enabled
 */
export async function isAutoThemeEnabled() {
  try {
    const result = await pyInvoke('get_config', { key: 'auto_theme_download' });
    return result.value === 'true';
  } catch (error) {
    console.error('Failed to check auto theme setting:', error);
    return true; // Default to enabled
  }
}

/**
 * Set automatic theme download preference
 */
export async function setAutoThemeEnabled(enabled) {
  try {
    await pyInvoke('set_config', {
      key: 'auto_theme_download',
      value: enabled ? 'true' : 'false'
    });
    return { success: true };
  } catch (error) {
    console.error('Failed to set auto theme preference:', error);
    return { success: false, message: error.message };
  }
}

/**
 * Initialize theme on app startup
 * - If auto theme is enabled and no theme is saved, download from GitHub
 * - If theme is saved, apply it
 */
export async function initThemeOnStartup() {
  try {
    const autoEnabled = await isAutoThemeEnabled();
    const savedColor = await getSavedThemeColor();

    if (savedColor) {
      // Apply saved theme
      console.log('Applying saved theme color:', savedColor);
      applyTheme(savedColor);
      return { success: true, color: savedColor, source: 'saved' };
    } else if (autoEnabled) {
      // Download and apply new theme
      console.log('Auto theme enabled, downloading from GitHub...');
      return await initThemeFromGitHub();
    } else {
      console.log('No theme configured');
      return { success: false, message: 'No theme configured' };
    }
  } catch (error) {
    console.error('Failed to initialize theme on startup:', error);
    return { success: false, message: error.message };
  }
}
