<script setup>
import { onMounted } from 'vue';
import { initReminderNotifications } from './utils/notifications';
import { initThemeOnStartup } from './utils/theme';
import { appState } from './utils/globalVars';

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
  <router-view :class="{ 'horror-mode-global': appState.horrorMode }" />
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

/* 恐怖模式全局样式 */
.horror-mode-global {
  animation: horror-glitch 5s ease-in-out infinite;
  filter: saturate(0.5) brightness(0.8);
}

.horror-mode-global * {
  text-shadow: 2px 2px 4px rgba(139, 0, 0, 0.5);
}

@keyframes horror-glitch {
  0%, 90%, 100% {
    filter: saturate(0.5) brightness(0.8);
  }
  92%, 96% {
    filter: saturate(0.5) brightness(0.8) hue-rotate(180deg);
    transform: skew(0.5deg);
  }
  94% {
    filter: saturate(0.5) brightness(1.2);
    transform: skew(-0.5deg);
  }
}
</style>
