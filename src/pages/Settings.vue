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

    <!-- 服务器同步设置 -->
    <mdui-card class="settings-group">
      <span class="group-title">服务器同步</span>
      <mdui-divider></mdui-divider>
      <mdui-list>
        <mdui-list-item icon="badge" rounded nonclickable>
          客户端名称
          <mdui-text-field style="height: 53px; min-width: 300px;" variant="filled" label="在服务器上显示的名称"
            :value="settings.client_name" @input="settings.client_name = $event.target.value"
            @blur="saveSetting('client_name', settings.client_name)" slot="end-icon"
            placeholder="留空则使用主机名">
          </mdui-text-field>
        </mdui-list-item>
        <mdui-list-item icon="cloud" rounded>
          启用自动同步
          <mdui-switch :checked="settings.sync_enabled" @change="handleSyncEnabledChange"
            slot="end-icon">
          </mdui-switch>
        </mdui-list-item>
        <mdui-list-item icon="timer" rounded nonclickable :disabled="settings.sync_enabled !== 'true'">
          同步间隔
          <mdui-segmented-button-group selects="single" :value="settings.sync_interval || '300'"
            @change="handleSyncIntervalChange" slot="end-icon">
            <mdui-segmented-button value="60">1分钟</mdui-segmented-button>
            <mdui-segmented-button value="300">5分钟</mdui-segmented-button>
            <mdui-segmented-button value="600">10分钟</mdui-segmented-button>
            <mdui-segmented-button value="1800">30分钟</mdui-segmented-button>
          </mdui-segmented-button-group>
        </mdui-list-item>
        <mdui-list-item icon="lan" rounded nonclickable>
          Management Server 地址
          <mdui-text-field style="height: 53px; min-width: 300px;" type="url" variant="filled"
            label="Management Server URL"
            :value="managementServerUrl" @input="managementServerUrl = $event.target.value"
            @blur="saveManagementServerUrl" slot="end-icon"
            placeholder="http://192.168.1.100:8765">
          </mdui-text-field>
        </mdui-list-item>

        <!-- Sync Direction Selector -->
        <mdui-list-item icon="sync_alt" rounded nonclickable>
          同步方向
          <mdui-segmented-button-group selects="single" :value="settings.sync_direction"
            @change="handleSyncDirectionChange" slot="end-icon">
            <mdui-segmented-button value="upload">
              <mdui-icon slot="icon" name="upload"></mdui-icon>
              上传
            </mdui-segmented-button>
            <mdui-segmented-button value="download">
              <mdui-icon slot="icon" name="download"></mdui-icon>
              下载
            </mdui-segmented-button>
            <mdui-segmented-button value="bidirectional">
              <mdui-icon slot="icon" name="sync"></mdui-icon>
              双向
            </mdui-segmented-button>
          </mdui-segmented-button-group>
        </mdui-list-item>

        <!-- Conflict Resolution Strategy (only for bidirectional) -->
        <mdui-list-item v-if="settings.sync_direction === 'bidirectional'" icon="rule" rounded nonclickable>
          冲突解决策略
          <mdui-select variant="filled" :value="settings.sync_strategy" @change="handleSyncStrategyChange"
            slot="end-icon" style="width: 200px;">
            <mdui-menu-item value="server_wins">服务器优先</mdui-menu-item>
            <mdui-menu-item value="local_wins">本地优先</mdui-menu-item>
            <mdui-menu-item value="newest_wins">最新优先</mdui-menu-item>
          </mdui-select>
        </mdui-list-item>

        <!-- Sync Buttons -->
        <mdui-list-item rounded nonclickable>
          <div style="display: flex; flex-wrap: wrap; gap: 8px; width: 100%;">
            <mdui-button variant="outlined" icon="wifi_find" @click="testConnection"
              :loading="isTestingConnection">
              测试连接
            </mdui-button>
            <mdui-button variant="outlined" icon="app_registration" @click="registerClient"
              :loading="isRegistering">
              注册客户端
            </mdui-button>
            <mdui-button variant="filled" :icon="syncButtonIcon" @click="performSync"
              :loading="isSyncing" :disabled="settings.sync_enabled !== 'true'">
              {{ syncButtonText }}
            </mdui-button>
            <mdui-button variant="outlined" icon="search" @click="checkConflicts"
              :loading="isCheckingConflicts">
              检查冲突
            </mdui-button>
            <mdui-button variant="outlined" icon="refresh" @click="forceSyncNow"
              :loading="isForceSyncing">
              强制完整同步
            </mdui-button>
          </div>
        </mdui-list-item>

        <!-- Sync Status Display -->
        <mdui-list-item v-if="syncStatus" rounded nonclickable>
          <div style="display: flex; align-items: center; gap: 8px; padding: 8px; border-radius: 8px;"
            :style="{ backgroundColor: syncStatusColor }">
            <mdui-icon :name="syncStatusIcon" :style="{ color: syncStatusIconColor }"></mdui-icon>
            <div style="flex: 1;">
              <div :style="{ color: syncStatusTextColor, fontWeight: 500 }">
                {{ syncStatus.message }}
              </div>
              <div v-if="lastSyncTime" style="font-size: 0.875rem; opacity: 0.7; margin-top: 4px;">
                {{ lastSyncTime }}
              </div>
            </div>
          </div>
        </mdui-list-item>
      </mdui-list>

      <!-- Sync History Section -->
      <div style="margin-top: 24px;">
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 0 16px;">
          <span class="group-title" style="font-size: 1.25rem;">同步历史</span>
          <mdui-button-icon icon="refresh" @click="loadSyncHistory" :loading="isLoadingHistory"></mdui-button-icon>
        </div>
        <mdui-divider style="margin: 0.3rem 0 0.8rem 0;"></mdui-divider>

        <mdui-list v-if="syncHistory.length > 0">
          <mdui-collapse accordion>
            <mdui-collapse-item v-for="entry in syncHistory" :key="entry.id">
              <div slot="header" style="display: flex; align-items: center; gap: 12px; width: 100%; padding: 8px 0;">
                <mdui-icon :name="getSyncDirectionIcon(entry.direction)"
                  :style="{ color: 'var(--mdui-color-primary)' }"></mdui-icon>
                <div style="flex: 1; min-width: 0;">
                  <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <span style="font-weight: 500;">{{ formatTimestamp(entry.timestamp) }}</span>
                    <mdui-badge :variant="getSyncStatusVariant(entry.status)">
                      {{ getSyncStatusText(entry.status) }}
                    </mdui-badge>
                  </div>
                  <div style="font-size: 0.875rem; opacity: 0.7; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {{ entry.message }}
                  </div>
                </div>
                <div style="text-align: right; font-size: 0.875rem; opacity: 0.7;">
                  <div>课程: {{ entry.courses_synced }}</div>
                  <div>条目: {{ entry.schedule_synced }}</div>
                  <div v-if="entry.conflicts_found > 0" style="color: var(--mdui-color-warning);">
                    冲突: {{ entry.conflicts_found }}
                  </div>
                </div>
              </div>

              <!-- Expanded detail view -->
              <div style="padding: 12px; background-color: var(--mdui-color-surface-container); border-radius: 8px; margin: 8px 0;">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; font-size: 0.875rem;">
                  <div>
                    <div style="opacity: 0.7; margin-bottom: 4px;">时间戳</div>
                    <div>{{ entry.timestamp }}</div>
                  </div>
                  <div>
                    <div style="opacity: 0.7; margin-bottom: 4px;">同步方向</div>
                    <div>{{ getSyncDirectionText(entry.direction) }}</div>
                  </div>
                  <div>
                    <div style="opacity: 0.7; margin-bottom: 4px;">同步课程数</div>
                    <div>{{ entry.courses_synced }}</div>
                  </div>
                  <div>
                    <div style="opacity: 0.7; margin-bottom: 4px;">同步条目数</div>
                    <div>{{ entry.schedule_synced }}</div>
                  </div>
                  <div v-if="entry.conflicts_found > 0" style="grid-column: span 2;">
                    <div style="opacity: 0.7; margin-bottom: 4px;">发现冲突</div>
                    <div style="color: var(--mdui-color-warning);">{{ entry.conflicts_found }} 个冲突</div>
                  </div>
                  <div style="grid-column: span 2;">
                    <div style="opacity: 0.7; margin-bottom: 4px;">消息</div>
                    <div>{{ entry.message || '无' }}</div>
                  </div>
                </div>
              </div>
            </mdui-collapse-item>
          </mdui-collapse>
        </mdui-list>

        <div v-else style="padding: 24px; text-align: center; opacity: 0.5;">
          暂无同步历史记录
        </div>
      </div>
    </mdui-card>

    <!-- Conflict Resolution Dialog -->
    <mdui-dialog :open="showConflictDialog" @closed="showConflictDialog = false"
      style="--mdui-shape-corner-large: 16px; max-width: 800px; width: 90vw;">
      <div slot="headline">检测到同步冲突</div>
      <div slot="description" style="max-height: 60vh; overflow-y: auto;">
        <div v-if="conflicts.hasConflicts">
          <!-- Course Conflicts -->
          <div v-if="conflicts.courses.length > 0" style="margin-bottom: 24px;">
            <h3 style="margin: 0 0 12px 0; font-size: 1.1rem; font-weight: 500;">课程冲突 ({{ conflicts.courses.length }})</h3>
            <div v-for="(conflict, idx) in conflicts.courses" :key="`course-${idx}`"
              style="margin-bottom: 16px; padding: 12px; background-color: var(--mdui-color-surface-container); border-radius: 8px;">
              <div style="font-weight: 500; margin-bottom: 8px;">课程 ID: {{ conflict.id }}</div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div style="padding: 8px; background-color: var(--mdui-color-surface); border-radius: 4px;">
                  <div style="font-weight: 500; margin-bottom: 4px; color: var(--mdui-color-primary);">本地版本</div>
                  <div style="font-size: 0.875rem;">
                    <div><strong>名称:</strong> {{ conflict.local.name }}</div>
                    <div><strong>教师:</strong> {{ conflict.local.teacher || '无' }}</div>
                    <div><strong>地点:</strong> {{ conflict.local.location || '无' }}</div>
                    <div><strong>颜色:</strong> <span :style="{ color: conflict.local.color }">{{ conflict.local.color }}</span></div>
                  </div>
                </div>

                <div style="padding: 8px; background-color: var(--mdui-color-surface); border-radius: 4px;">
                  <div style="font-weight: 500; margin-bottom: 4px; color: var(--mdui-color-secondary);">服务器版本</div>
                  <div style="font-size: 0.875rem;">
                    <div><strong>名称:</strong> {{ conflict.server.name }}</div>
                    <div><strong>教师:</strong> {{ conflict.server.teacher || '无' }}</div>
                    <div><strong>地点:</strong> {{ conflict.server.location || '无' }}</div>
                    <div><strong>颜色:</strong> <span :style="{ color: conflict.server.color }">{{ conflict.server.color }}</span></div>
                  </div>
                </div>
              </div>

              <mdui-segmented-button-group selects="single" v-model="conflictResolutions.courses[conflict.id]"
                style="margin-top: 8px; width: 100%;">
                <mdui-segmented-button value="server">使用服务器</mdui-segmented-button>
                <mdui-segmented-button value="local">使用本地</mdui-segmented-button>
                <mdui-segmented-button value="skip">跳过</mdui-segmented-button>
              </mdui-segmented-button-group>
            </div>
          </div>

          <!-- Schedule Entry Conflicts -->
          <div v-if="conflicts.entries.length > 0">
            <h3 style="margin: 0 0 12px 0; font-size: 1.1rem; font-weight: 500;">课表条目冲突 ({{ conflicts.entries.length }})</h3>
            <div v-for="(conflict, idx) in conflicts.entries" :key="`entry-${idx}`"
              style="margin-bottom: 16px; padding: 12px; background-color: var(--mdui-color-surface-container); border-radius: 8px;">
              <div style="font-weight: 500; margin-bottom: 8px;">条目 ID: {{ conflict.id }}</div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div style="padding: 8px; background-color: var(--mdui-color-surface); border-radius: 4px;">
                  <div style="font-weight: 500; margin-bottom: 4px; color: var(--mdui-color-primary);">本地版本</div>
                  <div style="font-size: 0.875rem;">
                    <div><strong>星期:</strong> {{ getDayOfWeekText(conflict.local.day_of_week) }}</div>
                    <div><strong>时间:</strong> {{ conflict.local.start_time }} - {{ conflict.local.end_time }}</div>
                    <div><strong>周次:</strong> {{ formatWeeks(conflict.local.weeks) }}</div>
                    <div v-if="conflict.local.note"><strong>备注:</strong> {{ conflict.local.note }}</div>
                  </div>
                </div>

                <div style="padding: 8px; background-color: var(--mdui-color-surface); border-radius: 4px;">
                  <div style="font-weight: 500; margin-bottom: 4px; color: var(--mdui-color-secondary);">服务器版本</div>
                  <div style="font-size: 0.875rem;">
                    <div><strong>星期:</strong> {{ getDayOfWeekText(conflict.server.day_of_week) }}</div>
                    <div><strong>时间:</strong> {{ conflict.server.start_time }} - {{ conflict.server.end_time }}</div>
                    <div><strong>周次:</strong> {{ formatWeeks(conflict.server.weeks) }}</div>
                    <div v-if="conflict.server.note"><strong>备注:</strong> {{ conflict.server.note }}</div>
                  </div>
                </div>
              </div>

              <mdui-segmented-button-group selects="single" v-model="conflictResolutions.entries[conflict.id]"
                style="margin-top: 8px; width: 100%;">
                <mdui-segmented-button value="server">使用服务器</mdui-segmented-button>
                <mdui-segmented-button value="local">使用本地</mdui-segmented-button>
                <mdui-segmented-button value="skip">跳过</mdui-segmented-button>
              </mdui-segmented-button-group>
            </div>
          </div>
        </div>

        <div v-else style="padding: 24px; text-align: center;">
          未发现冲突
        </div>
      </div>
      <div slot="action">
        <mdui-button @click="showConflictDialog = false">取消</mdui-button>
        <mdui-button variant="filled" @click="resolveConflicts" :disabled="!conflicts.hasConflicts">
          应用解决方案
        </mdui-button>
      </div>
    </mdui-dialog>

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
        <mdui-list-item icon="cloud_sync" rounded>
          同步状态
          <mdui-switch :checked="settings.show_sync_status" @change="handleSwitchChange('show_sync_status', $event)"
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
        <mdui-list-item icon="schedule" rounded nonclickable :disabled="!settings.reminder_enabled">
          提前提醒时间
          <mdui-segmented-button-group selects="single" :value="settings.reminder_minutes || '10'"
            @change="handleReminderTimeChange" slot="end-icon">
            <mdui-segmented-button value="5">5分钟</mdui-segmented-button>
            <mdui-segmented-button value="10">10分钟</mdui-segmented-button>
            <mdui-segmented-button value="15">15分钟</mdui-segmented-button>
            <mdui-segmented-button value="30">30分钟</mdui-segmented-button>
          </mdui-segmented-button-group>
        </mdui-list-item>
        <mdui-list-item icon="volume_up" rounded :disabled="!settings.reminder_enabled">
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

    <!-- 彩蛋区域 -->
    <mdui-card class="settings-group" style="background: linear-gradient(135deg, rgba(139, 0, 0, 0.05), rgba(0, 0, 0, 0.05));">
      <span class="group-title" style="opacity: 0.6;">???</span>
      <mdui-divider></mdui-divider>
      <mdui-list>
        <mdui-list-item icon="warning" rounded nonclickable>
          <div style="display: flex; justify-content: center; width: 100%; padding: 1rem 0;">
            <mdui-button
              variant="outlined"
              style="color: var(--mdui-color-error); border-color: var(--mdui-color-error); min-width: 200px;"
              @click="handleHorrorMode"
            >
              {{ appState.horrorMode ? '关闭恐怖模式' : '千万别点' }}
            </mdui-button>
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
import { settings, saveSetting, saveSettings, regenerateUUID, resetSettings, setThemeMode, applyColorScheme, appState } from '../utils/globalVars';
import { exportScheduleData, importScheduleData } from '../utils/schedule';
import { initThemeFromGitHub } from '../utils/theme';
import { onMounted, ref, computed, reactive } from 'vue';
import { pyInvoke } from 'tauri-plugin-pytauri-api';

// Reactive state for theme download
const isDownloadingTheme = ref(false);

// Reactive state for sync operations
const managementServerUrl = ref(settings.server_url || '');
const isTestingConnection = ref(false);
const isRegistering = ref(false);
const isSyncing = ref(false);
const isForceSyncing = ref(false);
const syncStatus = ref(null);

// Sync history
const syncHistory = ref([]);
const isLoadingHistory = ref(false);

// Conflict detection
const isCheckingConflicts = ref(false);
const conflicts = reactive({
  hasConflicts: false,
  courses: [],
  entries: []
});
const showConflictDialog = ref(false);
const conflictResolutions = reactive({
  courses: {},
  entries: {}
});

// Computed properties for sync UI
const syncButtonText = computed(() => {
  switch (settings.sync_direction) {
    case 'upload':
      return '上传到服务器';
    case 'download':
      return '从服务器下载';
    case 'bidirectional':
      return '双向同步';
    default:
      return '立即同步';
  }
});

const syncButtonIcon = computed(() => {
  switch (settings.sync_direction) {
    case 'upload':
      return 'upload';
    case 'download':
      return 'download';
    case 'bidirectional':
      return 'sync';
    default:
      return 'sync';
  }
});

const syncStatusColor = computed(() => {
  if (!syncStatus.value) return '';
  if (syncStatus.value.success) {
    return 'var(--mdui-color-surface-container)';
  }
  return 'var(--mdui-color-error-container)';
});

const syncStatusIcon = computed(() => {
  if (!syncStatus.value) return '';
  if (syncStatus.value.success) {
    return 'check_circle';
  }
  return 'error';
});

const syncStatusIconColor = computed(() => {
  if (!syncStatus.value) return '';
  if (syncStatus.value.success) {
    return 'var(--mdui-color-primary)';
  }
  return 'var(--mdui-color-error)';
});

const syncStatusTextColor = computed(() => {
  if (!syncStatus.value) return '';
  if (syncStatus.value.success) {
    return 'var(--mdui-color-on-surface)';
  }
  return 'var(--mdui-color-on-error-container)';
});

const lastSyncTime = computed(() => {
  if (!syncHistory.value || syncHistory.value.length === 0) return '';
  const lastSync = syncHistory.value[0];
  return `上次同步: ${formatTimestamp(lastSync.timestamp)}`;
});

// Helper functions for sync history
function getSyncDirectionIcon(direction) {
  switch (direction) {
    case 'upload':
      return 'upload';
    case 'download':
      return 'download';
    case 'bidirectional':
      return 'sync';
    default:
      return 'sync_alt';
  }
}

function getSyncDirectionText(direction) {
  switch (direction) {
    case 'upload':
      return '上传';
    case 'download':
      return '下载';
    case 'bidirectional':
      return '双向同步';
    default:
      return direction;
  }
}

function getSyncStatusVariant(status) {
  switch (status) {
    case 'success':
      return 'filled';
    case 'failure':
      return 'filled';
    case 'conflict':
      return 'filled';
    default:
      return 'outlined';
  }
}

function getSyncStatusText(status) {
  switch (status) {
    case 'success':
      return '成功';
    case 'failure':
      return '失败';
    case 'conflict':
      return '冲突';
    default:
      return status;
  }
}

function formatTimestamp(timestamp) {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) {
      return '刚刚';
    } else if (diffMins < 60) {
      return `${diffMins} 分钟前`;
    } else if (diffHours < 24) {
      return `${diffHours} 小时前`;
    } else if (diffDays < 7) {
      return `${diffDays} 天前`;
    } else {
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  } catch (e) {
    return timestamp;
  }
}

function getDayOfWeekText(dayNum) {
  const days = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'];
  return days[dayNum] || dayNum;
}

function formatWeeks(weeksStr) {
  try {
    const weeks = JSON.parse(weeksStr);
    if (Array.isArray(weeks) && weeks.length > 0) {
      return weeks.join(', ');
    }
    return weeksStr;
  } catch (e) {
    return weeksStr;
  }
}

// Load sync history
async function loadSyncHistory() {
  isLoadingHistory.value = true;
  try {
    const response = await pyInvoke('get_sync_history', { limit: 10 });
    if (response.success) {
      syncHistory.value = response.history;
    }
  } catch (error) {
    console.error('Failed to load sync history:', error);
    snackbar({ message: '加载同步历史失败: ' + error, placement: 'top' });
  } finally {
    isLoadingHistory.value = false;
  }
}

// Check for conflicts
async function checkConflicts() {
  isCheckingConflicts.value = true;
  try {
    const response = await pyInvoke('check_sync_conflicts');
    if (response.success && response.has_conflicts) {
      conflicts.courses = response.conflicted_courses;
      conflicts.entries = response.conflicted_entries;
      conflicts.hasConflicts = true;

      // Initialize conflict resolutions to 'skip'
      conflicts.courses.forEach(c => {
        conflictResolutions.courses[c.id] = 'skip';
      });
      conflicts.entries.forEach(e => {
        conflictResolutions.entries[e.id] = 'skip';
      });

      showConflictDialog.value = true;
    } else if (response.success && !response.has_conflicts) {
      snackbar({ message: '未发现冲突', placement: 'top' });
    } else {
      snackbar({ message: response.message || '检测冲突失败', placement: 'top' });
    }
  } catch (error) {
    console.error('Check conflicts error:', error);
    snackbar({ message: '检测冲突失败: ' + error, placement: 'top' });
  } finally {
    isCheckingConflicts.value = false;
  }
}

// Resolve conflicts
async function resolveConflicts() {
  // This would need a backend command to apply the resolutions
  // For now, just close the dialog and show a message
  snackbar({
    message: '冲突解决功能需要后端支持（待实现）',
    placement: 'top'
  });
  showConflictDialog.value = false;
}

// Perform sync based on direction
async function performSync() {
  isSyncing.value = true;
  syncStatus.value = null;

  try {
    const direction = settings.sync_direction;
    let result;

    if (direction === 'upload') {
      result = await pyInvoke('sync_now');
    } else if (direction === 'download') {
      result = await pyInvoke('pull_from_server');
    } else if (direction === 'bidirectional') {
      result = await pyInvoke('bidirectional_sync_now', {
        strategy: settings.sync_strategy
      });
    }

    syncStatus.value = {
      success: result.success,
      message: result.message
    };

    if (result.success) {
      snackbar({ message: '同步成功', placement: 'top' });
      // Reload history after sync
      await loadSyncHistory();
    } else {
      snackbar({ message: `同步失败: ${result.message}`, placement: 'top' });
    }
  } catch (error) {
    console.error('Sync error:', error);
    syncStatus.value = {
      success: false,
      message: `同步失败: ${error}`
    };
    snackbar({ message: `同步失败: ${error}`, placement: 'top' });
  } finally {
    isSyncing.value = false;
  }
}

// Force full sync
async function forceSyncNow() {
  isForceSyncing.value = true;
  syncStatus.value = null;

  try {
    const result = await pyInvoke('bidirectional_sync_now', {
      strategy: settings.sync_strategy
    });

    syncStatus.value = {
      success: result.success,
      message: result.message
    };

    if (result.success) {
      snackbar({
        message: `强制同步成功！冲突: ${result.conflicts_found}, 课程更新: ${result.courses_updated}, 条目更新: ${result.entries_updated}`,
        placement: 'top'
      });
      await loadSyncHistory();
    } else {
      snackbar({ message: `强制同步失败: ${result.message}`, placement: 'top' });
    }
  } catch (error) {
    console.error('Force sync error:', error);
    syncStatus.value = {
      success: false,
      message: `强制同步失败: ${error}`
    };
    snackbar({ message: `强制同步失败: ${error}`, placement: 'top' });
  } finally {
    isForceSyncing.value = false;
  }
}

// Sync direction change handler
async function handleSyncDirectionChange(event) {
  const value = event.target.value || settings.sync_direction;
  settings.sync_direction = value;
  await saveSetting('sync_direction', value);
  snackbar({ message: `同步方向已设置为：${getSyncDirectionText(value)}`, placement: 'top' });
}

// Sync strategy change handler
async function handleSyncStrategyChange(event) {
  const value = event.target.value || settings.sync_strategy;
  settings.sync_strategy = value;
  await saveSetting('sync_strategy', value);

  const strategyText = {
    'server_wins': '服务器优先',
    'local_wins': '本地优先',
    'newest_wins': '最新优先'
  }[value] || value;

  snackbar({ message: `冲突策略已设置为：${strategyText}`, placement: 'top' });
}

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

// ============= 服务器同步相关函数 =============

// URL 验证函数
function isValidUrl(urlString) {
  if (!urlString || urlString.trim() === '') {
    return true; // 允许空 URL（表示未配置）
  }

  try {
    const url = new URL(urlString);
    // 只允许 http 和 https 协议
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch (error) {
    return false;
  }
}

// 保存 Management Server URL
async function saveManagementServerUrl() {
  // 验证 URL 格式
  if (!isValidUrl(managementServerUrl.value)) {
    snackbar({
      message: 'URL 格式无效，请输入有效的 HTTP 或 HTTPS 地址（如：http://localhost:8000）',
      placement: 'top'
    });
    return;
  }

  // 安全提示：HTTP URL 警告（非 localhost）
  if (managementServerUrl.value && managementServerUrl.value.trim()) {
    try {
      const url = new URL(managementServerUrl.value);
      const isLocalhost = url.hostname === 'localhost' || url.hostname === '127.0.0.1' || url.hostname === '[::1]';

      if (url.protocol === 'http:' && !isLocalhost) {
        snackbar({
          message: '⚠️ 警告：使用 HTTP 而非 HTTPS，数据将以明文传输。仅建议在受信任的局域网中使用。',
          placement: 'top'
        });
      }
    } catch (e) {
      // URL 验证已在 isValidUrl 中完成，这里忽略解析错误
    }
  }

  // 同时保存到 server_url（兼容旧的 WebSocket 客户端）
  settings.server_url = managementServerUrl.value;
  await saveSetting('server_url', managementServerUrl.value);
  snackbar({ message: 'Management Server 地址已保存', placement: 'top' });
}

// 启用/禁用自动同步
async function handleSyncEnabledChange(event) {
  const checked = event.target.checked;
  settings.sync_enabled = checked;
  await saveSetting('sync_enabled', checked);

  if (checked) {
    snackbar({ message: '自动同步已启用', placement: 'top' });
  } else {
    snackbar({ message: '自动同步已禁用', placement: 'top' });
  }
}

// 同步间隔切换
async function handleSyncIntervalChange(event) {
  const value = event.target.value || settings.sync_interval;
  settings.sync_interval = value;
  await saveSetting('sync_interval', value);

  const minutes = Math.floor(value / 60);
  snackbar({ message: `同步间隔已设置为${minutes}分钟`, placement: 'top' });
}

// 测试服务器连接
async function testConnection() {
  isTestingConnection.value = true;
  syncStatus.value = null;

  try {
    // 先保存 URL
    await saveManagementServerUrl();

    // 调用 Python 命令测试连接
    const result = await pyInvoke('test_server_connection');

    syncStatus.value = {
      success: result.success,
      message: result.message
    };

    if (result.success) {
      snackbar({
        message: '连接成功！服务器运行正常',
        placement: 'top'
      });
    } else {
      snackbar({
        message: `连接失败: ${result.message}`,
        placement: 'top'
      });
    }
  } catch (error) {
    console.error('Test connection error:', error);
    syncStatus.value = {
      success: false,
      message: `连接失败: ${error}`
    };
    snackbar({
      message: `连接失败: ${error}`,
      placement: 'top'
    });
  } finally {
    isTestingConnection.value = false;
  }
}

// 注册客户端
async function registerClient() {
  isRegistering.value = true;
  syncStatus.value = null;

  try {
    // 先保存 URL 和客户端名称
    await saveManagementServerUrl();
    if (settings.client_name) {
      await saveSetting('client_name', settings.client_name);
    }

    // 调用 Python 命令注册客户端
    const result = await pyInvoke('register_to_server');

    syncStatus.value = {
      success: result.success,
      message: result.message
    };

    if (result.success) {
      snackbar({
        message: '客户端注册成功！',
        placement: 'top'
      });
    } else {
      snackbar({
        message: `注册失败: ${result.message}`,
        placement: 'top'
      });
    }
  } catch (error) {
    console.error('Register client error:', error);
    syncStatus.value = {
      success: false,
      message: `注册失败: ${error}`
    };
    snackbar({
      message: `注册失败: ${error}`,
      placement: 'top'
    });
  } finally {
    isRegistering.value = false;
  }
}

// 立即同步 (deprecated - use performSync instead)
async function syncNow() {
  await performSync();
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
    sync_direction: settings.sync_direction,
    sync_strategy: settings.sync_strategy,
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

// ============= 恐怖模式彩蛋 =============
async function handleHorrorMode() {
  appState.horrorMode = !appState.horrorMode;

  if (appState.horrorMode) {
    snackbar({
      message: '你不应该点这个按钮的...',
      placement: 'top'
    });
  } else {
    snackbar({
      message: '恐怖模式已关闭',
      placement: 'top'
    });
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

  // Load sync history on mount
  loadSyncHistory();
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