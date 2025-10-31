<script setup>
import { onMounted } from 'vue';
import { initReminderNotifications } from './utils/notifications';
import { initThemeOnStartup } from './utils/theme';

// Initialize on app start
onMounted(async () => {
  try {
    // Initialize theme first for better UX
    await initThemeOnStartup();
  } catch (error) {
    console.error('Failed to initialize theme:', error);
  }

  try {
    await initReminderNotifications();
  } catch (error) {
    console.error('Failed to initialize reminder notifications:', error);
  }
});
</script>

<template>
  <router-view />
</template>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow: hidden;
}

#app {
  width: 100%;
  height: 100%;
}

/* 防止文本选择 */
* {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

/* 允许输入框文本选择 */
input, textarea, [contenteditable] {
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
}
</style>
