<template>
  <div class="audio-monitor">
    <mdui-card variant="outlined" class="monitor-card">
      <div class="card-header">
        <h2>Audio Monitor</h2>
      </div>

      <div class="controls">
        <mdui-button
          variant="filled"
          @click="handleStartMonitoring('microphone')"
          :disabled="microphoneActive"
        >
          Start Microphone
        </mdui-button>
        <mdui-button
          variant="filled"
          @click="handleStartMonitoring('system')"
          :disabled="systemActive"
        >
          Start System Audio
        </mdui-button>
        <mdui-button
          variant="outlined"
          @click="handleStopMonitoring('all')"
          :disabled="!microphoneActive && !systemActive"
        >
          Stop All
        </mdui-button>
      </div>

      <div class="audio-levels">
        <div class="level-section">
          <h3>Microphone</h3>
          <div class="level-display">
            <div class="level-info">
              <span>RMS: {{ formatValue(microphoneLevel.rms) }}</span>
              <span>dB: {{ formatDb(microphoneLevel.db) }}</span>
              <span>Peak: {{ formatValue(microphoneLevel.peak) }}</span>
            </div>
            <mdui-linear-progress
              :value="calculatePercentage(microphoneLevel.peak)"
              class="level-bar"
            ></mdui-linear-progress>
          </div>
        </div>

        <div class="level-section">
          <h3>System Audio</h3>
          <div class="level-display">
            <div class="level-info">
              <span>RMS: {{ formatValue(systemLevel.rms) }}</span>
              <span>dB: {{ formatDb(systemLevel.db) }}</span>
              <span>Peak: {{ formatValue(systemLevel.peak) }}</span>
            </div>
            <mdui-linear-progress
              :value="calculatePercentage(systemLevel.peak) * 0.015"
              class="level-bar"
            ></mdui-linear-progress>
          </div>
        </div>
      </div>

      <div class="log-section">
        <h3>Activity Log</h3>
        <div class="log-container">
          <div
            v-for="(log, index) in logs"
            :key="index"
            class="log-entry"
          >
            {{ log }}
          </div>
        </div>
      </div>
    </mdui-card>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue';
import { useAudioMonitor, MonitorType, formatValue, calculatePercentage } from '../utils/audioMonitor';

// 使用音频监控工具集
const {
  microphoneActive,
  systemActive,
  microphoneLevel,
  systemLevel,
  startMonitoring,
  stopMonitoring,
  formatDb,
  cleanup
} = useAudioMonitor();

const logs = ref([]);

const addLog = (message) => {
  const timestamp = new Date().toLocaleTimeString();
  logs.value.unshift(`[${timestamp}] ${message}`);
  if (logs.value.length > 50) {
    logs.value.pop();
  }
};

const handleStartMonitoring = async (type) => {
  try {
    const response = await startMonitoring(type);
    if (response.success) {
      addLog(response.message);
    } else {
      addLog(`Error: ${response.message}`);
    }
  } catch (error) {
    addLog(`Failed to start monitoring: ${error.message}`);
  }
};

const handleStopMonitoring = async (type) => {
  try {
    const response = await stopMonitoring(type);
    if (response.success) {
      addLog(response.message);
    } else {
      addLog(`Error: ${response.message}`);
    }
  } catch (error) {
    addLog(`Failed to stop monitoring: ${error.message}`);
  }
};

// 清理资源
onUnmounted(() => {
  cleanup();
});
</script>

<style scoped>
.audio-monitor {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.monitor-card {
  padding: 24px;
}

.card-header {
  margin-bottom: 24px;
}

.card-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.controls {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.audio-levels {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 32px;
}

.level-section h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 500;
}

.level-display {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.level-info {
  display: flex;
  gap: 16px;
  font-family: monospace;
  font-size: 14px;
}

.level-bar {
  width: 100%;
}

.log-section h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 500;
}

.log-container {
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 12px;
}

.log-entry {
  padding: 4px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.log-entry:last-child {
  border-bottom: none;
}
</style>
