<template>
    <main class="top-bar-container" id="top-bar-container" v-show="topbarType === 'full'" :style="topbarStyles">
        <div class="top-bar-content" :style="contentStyles">
            <div class="left-section" v-if="settings.show_schedule">
                <Schedule :key="scheduleKey" type="full" @classStart="handleClassStart" @classEnd="handleClassEnd" />
            </div>

            <div class="center-section" v-if="settings.show_clock">
                <Clock />
            </div>

            <div class="right-section">
                <!--<span v-show="mouseOn">MouseOn</span>-->
                <div class="sync-status" v-if="settings.show_sync_status && syncStatus">
                    <mdui-tooltip :content="syncStatusTooltip">
                        <mdui-icon
                            :name="syncStatus.connected ? 'cloud_done' : 'cloud_off'"
                            :style="{ color: syncStatus.connected ? 'var(--mdui-color-primary)' : 'var(--mdui-color-error)' }"
                        ></mdui-icon>
                    </mdui-tooltip>
                </div>
                <div class="control-buttons">
                    <mdui-button-icon id="pin-button" selectable icon="push_pin--outlined" selected-icon="push_pin"
                        @click="handlePin"></mdui-button-icon>
                    <mdui-button-icon icon="close" @click="handleClose"></mdui-button-icon>
                </div>
            </div>
        </div>
    </main>
    <Schedule :key="scheduleKey" type="mini" v-if="topbarType === 'thin' && settings.show_schedule" />
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { pyInvoke } from 'tauri-plugin-pytauri-api';
import Clock from './components/Clock.vue';
import Schedule, { progress as classProgress } from './components/Schedule.vue';
import { loadSettings, settings } from '../utils/globalVars';
import { mouseOn, init as initCollapse, reset as resetCollapse } from '../utils/collapse';
import { opacityToHex } from '../utils/topbarThemes';

// 用于强制重载 Schedule 组件的 key
const scheduleKey = ref(Date.now());

// 同步状态
const syncStatus = ref(null);
let syncStatusInterval = null;

// TopBar 动态样式
const topbarStyles = computed(() => {
  // 将透明度转换为 hex
  const opacityHex = opacityToHex(settings.topbar_background_opacity);
  const backgroundColor = `${settings.topbar_background_color}${opacityHex}`;

  return {
    backgroundColor: backgroundColor,
    color: settings.topbar_text_color,
    backdropFilter: `blur(${settings.topbar_blur_strength}px)`,
    WebkitBackdropFilter: `blur(${settings.topbar_blur_strength}px)`,
    borderRadius: `0 0 ${settings.topbar_border_radius}px ${settings.topbar_border_radius}px`,
    boxShadow: settings.topbar_shadow_enabled === 'true'
      ? '0 4px 16px rgba(0,0,0,0.1)'
      : 'none',
    fontFamily: settings.topbar_font_family,
    fontWeight: settings.topbar_font_weight,
    fontSize: `calc(1rem * ${settings.topbar_font_size_multiplier})`
  };
});

// TopBar 内容区域样式
const contentStyles = computed(() => {
  const spacing = `${settings.topbar_component_spacing}px`;
  const halfSpacing = `${Math.round(parseInt(settings.topbar_component_spacing) / 2)}px`;

  return {
    padding: `${halfSpacing} ${spacing}`,
    gap: spacing
  };
});

// 是否显示图标
const showIcons = computed(() => settings.topbar_show_icons === 'true');

// 布局模式
const layoutMode = computed(() => settings.topbar_layout);

// 计算同步状态的工具提示文本
const syncStatusTooltip = computed(() => {
    if (!syncStatus.value) return '';

    if (syncStatus.value.connected) {
        return `Management Server 已连接\n${syncStatus.value.server_url}`;
    } else if (syncStatus.value.enabled) {
        return `Management Server 未连接\n${syncStatus.value.server_url || '未配置服务器地址'}`;
    } else {
        return 'Management Server 同步已禁用';
    }
});

// 获取同步状态
const fetchSyncStatus = async () => {
    try {
        const status = await pyInvoke('get_sync_status');
        syncStatus.value = status;
    } catch (error) {
        console.error('Failed to fetch sync status:', error);
        syncStatus.value = null;
    }
};

// 初始化顶栏窗口
onMounted(async () => {
    document.body.classList.add("topbar")
    try {
        // 计算顶栏高度的实际像素高度
        const d = document.createElement('div');
        d.style.height = `${settings.topbar_height}rem`;
        d.style.position = 'absolute';
        d.style.visibility = 'hidden';
        document.body.appendChild(d);
        height = d.clientHeight;
        d.remove();

        await invoke('setup_topbar_window', { height });
        console.log('Top bar window setup invoked successfully.', height);
        document.body.style.borderRadius = "0 0 15px 15px";

        setTimeout(() => {
            fullWidth = window.innerWidth
        }, 50);
    } catch (error) {
        console.error('Failed to setup top bar window:', error);
    }

    isPinned.value = false;

    initCollapse()

    // 监听设置更新事件
    try {
        await listen('setting-update', async (event) => {
            console.log('Setting update received in TopBar:', event.payload);
            let value = event.payload.value;
            // 对于字符串'boolean'类型的设置，需要转换为布尔值
            if (value === 'true' || value === 'false') {
                value = value === 'true';
            }
            // 更新对应的设置
            settings[event.payload.key] = value;

            switch (event.payload.key) {
                case 'topbar_height':
                    await updateTopbarWindowSize();
                    break;
                case 'font_size':
                    // 延时50ms以确保设置生效再更新窗口大小
                    setTimeout(() => {
                        updateTopbarWindowSize();
                    }, 50);
                    break;
                case 'control_mode':
                    await resetCollapse();
                    break;
                default:
                    break;

            }
        });

        // 监听批量设置更新事件 - 刷新 Schedule 组件
        await listen('settings-batch-update', (event) => {
            console.log('Batch settings update received in TopBar:', event.payload);

            // 检查是否更新了影响课表显示的设置
            const affectsSchedule = event.payload.updated_keys.some(key =>
                ['show_schedule', 'semester_start_date'].includes(key)
            );

            if (affectsSchedule) {
                console.log('Settings affecting schedule updated, reloading...');
                forceReloadSchedule();
            }
            // 重新加载所有设置以确保同步
            loadSettings();

            resetCollapse()
        });
    } catch (error) {
        console.error('Failed to setup setting update listener:', error);
    }

    // 初始化同步状态检查
    if (settings.show_sync_status) {
        await fetchSyncStatus();
        // 每 30 秒检查一次同步状态
        syncStatusInterval = setInterval(fetchSyncStatus, 30000);
    }
});

// 清理定时器
onUnmounted(() => {
    if (syncStatusInterval) {
        clearInterval(syncStatusInterval);
        syncStatusInterval = null;
    }
});

const handlePin = function (e) {
    setTimeout(() => {
        // 加上50ms延时确保获取真实数据
        isPinned.value = e.target.hasAttribute("selected")
        console.log(isPinned.value)
    }, 50);
};

const handleClose = async () => {
    try {
        // Pass the window name so the Rust command knows which window to toggle
        await invoke('toggle_window', { windowName: 'topbar' });
    } catch (error) {
        console.error('Failed to close window:', error);
    }
};

// 暴露给父组件的方法
const forceReloadSchedule = () => {
    // 通过改变 key 的值强制重新挂载 Schedule 组件
    scheduleKey.value = Date.now();
};

const handleClassStart = () => {
    if (!isPinned.value) {
        setThinTopbar()
    }
};

const handleClassEnd = () => {
    setFullTopbar()
};

defineExpose({
    toggleVisibility: handleClose,
    forceReloadSchedule
});
</script>

<script>
// 响应式数据
export const isPinned = ref(false);
export const topbarType = ref(["full", "thin"][0]) // 'full' or 'thin'
var fullWidth = 1024
var thinWidth = '10rem'
let height = 50

export const setFullTopbar = async () => {
    await invoke('resize_topbar_window', { width: fullWidth, height: height })
    document.body.style.width = `${fullWidth}px`
    document.body.style.height = `${height}px`
    document.body.style.borderRadius = "0 0 15px 15px";
    document.getElementById("app").style.backgroundColor = ""
    topbarType.value = 'full'
}

export const setThinTopbar = async () => {
    document.body.style.width = thinWidth
    document.body.style.height = `1.3rem`
    document.body.style.borderRadius = "0";
    topbarType.value = 'thin'
    document.getElementById("app").style.backgroundColor = "rgba(255, 255, 255, 0)"
    setTimeout(async () => {
        if (!mouseOn.value) await invoke('resize_topbar_window', { width: document.body.clientWidth, height: document.body.clientHeight })
    }, 700);

}

export const updateTopbarWindowSize = async () => {
    // 重新计算顶栏高度的实际像素高度
    const d = document.createElement('div');
    d.style.height = `${settings.topbar_height}rem`;
    d.style.position = 'absolute';
    d.style.visibility = 'hidden';
    document.body.appendChild(d);
    height = d.clientHeight;
    d.remove();

    await invoke('setup_topbar_window', { height });
    console.log('Top bar height updated:', height);

    // 同步 DOM 高度和样式
    if (topbarType.value === 'full') {
        // 如果当前是 full 状态，同步更新 DOM
        document.body.style.height = `${height}px`;
        // 强制重绘以确保圆角等样式正确渲染
        void document.body.offsetHeight;
        document.body.style.borderRadius = "0 0 15px 15px";
    }
}

</script>

<style lang="less" scoped>
.top-bar-container {
    width: 100%;
    height: 100vh;
    overflow: hidden;
    /* 动态样式通过 :style 绑定应用 */
    /* 不再在这里设置 backdrop-filter, border-radius, box-shadow */
}

.top-bar-content {
    display: flex;
    align-items: center;
    height: 100%;
    position: relative;
    /* padding 和 gap 通过 :style 动态应用 */
}

.left-section {
    position: absolute;
    left: 20px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 2;
}

.center-section {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    z-index: 1;
}

.right-section {
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    align-items: center;
    gap: 15px;
    z-index: 2;
}

.sync-status {
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.8;
    transition: opacity 0.2s;

    &:hover {
        opacity: 1;
    }

    mdui-icon {
        font-size: 1.25rem;
    }
}

.control-buttons {
    display: flex;
    gap: 8px;
}

.control-buttons mdui-button-icon {
    -webkit-app-region: no-drag;
}

@media (max-width: 800px) {
    .top-bar-content {
        padding: 0 15px;
    }

    .left-section {
        left: 15px;
    }

    .right-section {
        right: 15px;
        gap: 10px;
    }
}
</style>