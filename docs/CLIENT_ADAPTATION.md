# ClassTop 客户端适配指南

本文档说明如何将 ClassTop 客户端与集中管理服务器（Classtop-Management-Server）进行集成对接。

## 📋 目录

- [概述](#概述)
- [架构说明](#架构说明)
- [数据模型映射](#数据模型映射)
- [客户端需要实现的功能](#客户端需要实现的功能)
- [API 对接说明](#api-对接说明)
- [配置管理](#配置管理)
- [数据同步流程](#数据同步流程)
- [UI 集成建议](#ui-集成建议)
- [测试指南](#测试指南)

---

## 概述

### 项目关系

```
┌─────────────────────────────────────────┐
│  Classtop-Management-Server (服务端)    │
│  - Rust + Actix-Web + PostgreSQL       │
│  - 集中管理多个客户端                    │
│  - 提供 REST API 和 Web 管理界面        │
└─────────────────┬───────────────────────┘
                  │
                  │ HTTP API (同步数据)
                  │
┌─────────────────▼───────────────────────┐
│  ClassTop Client (客户端)              │
│  - Tauri + Vue 3 + PyTauri + SQLite    │
│  - 本地课程管理和进度显示                │
│  - 定期向服务器同步数据                  │
└─────────────────────────────────────────┘
```

### 集成目标

1. **客户端注册**: ClassTop 客户端启动时自动向服务器注册
2. **数据同步**: 定期将本地课程和课程表数据同步到服务器
3. **远程管理**: 服务器可以查看客户端状态和数据
4. **双向更新**: 支持从服务器拉取配置和数据（可选）

---

## 架构说明

### 客户端项目结构

```
classtop/ (客户端)
├── src-tauri/python/tauri_app/
│   ├── __init__.py              # 主初始化文件
│   ├── db.py                    # SQLite 数据库操作
│   ├── schedule_manager.py      # 课程管理逻辑
│   ├── settings_manager.py      # 设置管理
│   └── sync_client.py           # 【新增】服务器同步客户端
└── src/
    └── pages/
        └── Settings.vue          # 设置页面（添加服务器配置）
```

### 服务端项目结构

```
Classtop-Management-Server/ (服务端)
├── src/
│   ├── main.rs                  # 入口
│   ├── handlers.rs              # API 处理器
│   ├── models.rs                # 数据模型
│   ├── db.rs                    # PostgreSQL 操作
│   └── routes.rs                # 路由配置
├── migrations/
│   └── 001_initial_postgresql.sql  # 数据库迁移
└── frontend/                    # Vue 3 管理界面
    └── src/
        ├── components/
        └── views/
```

---

## 数据模型映射

### 客户端 SQLite → 服务端 PostgreSQL

#### 1. 课程 (Courses)

**客户端表结构** (`classtop.db`):
```sql
CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    teacher TEXT,
    color TEXT,
    note TEXT
);
```

**服务端表结构** (`PostgreSQL`):
```sql
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id),
    course_id_on_client INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    teacher VARCHAR(255),
    location VARCHAR(255),
    color VARCHAR(7),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, course_id_on_client)
);
```

**映射关系**:
| 客户端字段 | 服务端字段 | 说明 |
|-----------|-----------|------|
| `id` | `course_id_on_client` | 客户端本地 ID |
| `name` | `name` | 课程名称 |
| `teacher` | `teacher` | 教师姓名 |
| `note` | - | 客户端备注（暂不同步） |
| `color` | `color` | 课程颜色 |
| - | `client_id` | 服务端自动分配（客户端 UUID） |
| - | `location` | 教室地点（客户端需添加） |

**差异说明**:
- ⚠️ 客户端缺少 `location` 字段，需要添加到客户端数据库
- 客户端的 `note` 字段暂不同步到服务器

#### 2. 课程表 (Schedule Entries)

**客户端表结构**:
```sql
CREATE TABLE schedule (
    id INTEGER PRIMARY KEY,
    course_id INTEGER,
    day_of_week INTEGER,      -- 1=周一, 7=周日
    start_time TEXT,          -- HH:MM 格式
    end_time TEXT,
    weeks TEXT,               -- JSON 数组: "[1,2,3,...]"
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
```

**服务端表结构**:
```sql
CREATE TABLE schedule_entries (
    id SERIAL PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id),
    entry_id_on_client INTEGER NOT NULL,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    day_of_week INTEGER NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    weeks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, entry_id_on_client)
);
```

**映射关系**:
| 客户端字段 | 服务端字段 | 说明 |
|-----------|-----------|------|
| `id` | `entry_id_on_client` | 客户端本地 ID |
| `course_id` | - | 需映射到服务端 course_id |
| `day_of_week` | `day_of_week` | 星期几（1-7） |
| `start_time` | `start_time` | 开始时间 |
| `end_time` | `end_time` | 结束时间 |
| `weeks` | `weeks` | JSON 数组字符串 |
| - | `client_id` | 服务端自动分配 |

#### 3. 客户端注册信息

**服务端表结构** (客户端需提供的信息):
```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    api_url VARCHAR(512),
    status VARCHAR(50) DEFAULT 'offline',
    last_sync TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**客户端需提供**:
- `name`: 客户端设备名称（建议使用主机名或用户自定义名称）
- `api_url`: 客户端 API 地址（如果启用了客户端 API 服务器）

---

## 客户端需要实现的功能

### 1. 数据库 Schema 更新

#### 添加 `location` 字段到 `courses` 表

**迁移 SQL**:
```sql
-- 检查字段是否存在，不存在则添加
ALTER TABLE courses ADD COLUMN IF NOT EXISTS location TEXT;
```

**在 `db.py` 中添加迁移逻辑**:
```python
def migrate_database(conn):
    """数据库迁移：添加新字段"""
    cursor = conn.cursor()

    # 检查 location 字段是否存在
    cursor.execute("PRAGMA table_info(courses)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'location' not in columns:
        cursor.execute("ALTER TABLE courses ADD COLUMN location TEXT")
        conn.commit()
        print("✓ 添加 location 字段到 courses 表")
```

#### 添加 `server_url` 和 `client_uuid` 到 `settings` 表

这些设置应该已经存在于客户端的 settings 表中。如果没有，需要添加：

```python
# 在 settings_manager.py 中
DEFAULT_SETTINGS = {
    "client_uuid": str(uuid.uuid4()),  # 自动生成唯一 UUID
    "server_url": "",                  # 服务器地址
    "sync_enabled": "false",           # 是否启用同步
    "sync_interval": "300",            # 同步间隔（秒）
    # ... 其他设置
}
```

---

### 2. 创建服务器同步客户端模块

在 `src-tauri/python/tauri_app/sync_client.py` 创建新文件：

```python
"""
服务器同步客户端
负责与 Classtop-Management-Server 通信
"""

import requests
import threading
import time
import json
from typing import Optional, Dict, List
from .logger import AppLogger
from .settings_manager import SettingsManager
from .schedule_manager import ScheduleManager


class SyncClient:
    """服务器同步客户端"""

    def __init__(self, settings_manager: SettingsManager,
                 schedule_manager: ScheduleManager, logger: AppLogger):
        self.settings_manager = settings_manager
        self.schedule_manager = schedule_manager
        self.logger = logger
        self.sync_thread = None
        self.is_running = False

    def start_auto_sync(self):
        """启动自动同步（后台线程）"""
        sync_enabled = self.settings_manager.get_setting("sync_enabled", "false")
        if sync_enabled.lower() != "true":
            self.logger.log_message("info", "同步功能未启用")
            return

        if self.is_running:
            self.logger.log_message("warning", "同步线程已在运行")
            return

        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        self.logger.log_message("info", "启动自动同步线程")

    def stop_auto_sync(self):
        """停止自动同步"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        self.logger.log_message("info", "停止自动同步线程")

    def _sync_loop(self):
        """同步循环"""
        while self.is_running:
            try:
                interval = int(self.settings_manager.get_setting("sync_interval", "300"))

                # 执行同步
                success = self.sync_to_server()
                if success:
                    self.logger.log_message("info", f"同步成功，等待 {interval} 秒")
                else:
                    self.logger.log_message("error", "同步失败，将在下次重试")

                # 等待指定间隔
                for _ in range(interval):
                    if not self.is_running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.log_message("error", f"同步循环异常: {e}")
                time.sleep(60)  # 出错后等待 1 分钟

    def register_client(self) -> bool:
        """向服务器注册客户端"""
        try:
            server_url = self.settings_manager.get_setting("server_url", "")
            if not server_url:
                self.logger.log_message("warning", "未配置服务器地址")
                return False

            # 获取客户端信息
            client_uuid = self.settings_manager.get_setting("client_uuid", "")
            if not client_uuid:
                import uuid
                client_uuid = str(uuid.uuid4())
                self.settings_manager.set_setting("client_uuid", client_uuid)

            # 获取客户端 API 地址（如果启用）
            api_enabled = self.settings_manager.get_setting("api_server_enabled", "false")
            api_url = ""
            if api_enabled.lower() == "true":
                api_host = self.settings_manager.get_setting("api_server_host", "0.0.0.0")
                api_port = self.settings_manager.get_setting("api_server_port", "8765")
                # 如果是 0.0.0.0，尝试获取本机 IP
                if api_host == "0.0.0.0":
                    import socket
                    api_host = socket.gethostbyname(socket.gethostname())
                api_url = f"http://{api_host}:{api_port}"

            # 构造注册数据
            import socket
            client_name = self.settings_manager.get_setting("client_name", socket.gethostname())

            data = {
                "uuid": client_uuid,
                "name": client_name,
                "api_url": api_url
            }

            # 发送注册请求
            url = f"{server_url.rstrip('/')}/api/clients/register"
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("success"):
                self.logger.log_message("info", f"客户端注册成功: {client_name}")
                return True
            else:
                self.logger.log_message("error", f"客户端注册失败: {result}")
                return False

        except Exception as e:
            self.logger.log_message("error", f"注册客户端失败: {e}")
            return False

    def sync_to_server(self) -> bool:
        """同步数据到服务器"""
        try:
            server_url = self.settings_manager.get_setting("server_url", "")
            client_uuid = self.settings_manager.get_setting("client_uuid", "")

            if not server_url or not client_uuid:
                self.logger.log_message("warning", "服务器地址或客户端 UUID 未配置")
                return False

            # 获取所有课程
            courses = self.schedule_manager.get_all_courses()

            # 获取所有课程表条目
            schedule_entries = self.schedule_manager.get_all_schedule_entries()

            # 构造同步数据
            sync_data = {
                "client_uuid": client_uuid,
                "courses": [
                    {
                        "id_on_client": course["id"],
                        "name": course["name"],
                        "teacher": course.get("teacher", ""),
                        "location": course.get("location", ""),
                        "color": course.get("color", "#6750A4")
                    }
                    for course in courses
                ],
                "schedule_entries": [
                    {
                        "id_on_client": entry["id"],
                        "course_id_on_client": entry["course_id"],
                        "day_of_week": entry["day_of_week"],
                        "start_time": entry["start_time"],
                        "end_time": entry["end_time"],
                        "weeks": json.loads(entry["weeks"]) if entry.get("weeks") else []
                    }
                    for entry in schedule_entries
                ]
            }

            # 发送同步请求
            url = f"{server_url.rstrip('/')}/api/sync"
            response = requests.post(url, json=sync_data, timeout=30)
            response.raise_for_status()

            result = response.json()
            if result.get("success"):
                sync_info = result.get("data", {})
                courses_synced = sync_info.get("courses_synced", 0)
                entries_synced = sync_info.get("schedule_entries_synced", 0)
                self.logger.log_message(
                    "info",
                    f"同步成功: {courses_synced} 门课程, {entries_synced} 个课程表条目"
                )
                return True
            else:
                self.logger.log_message("error", f"同步失败: {result}")
                return False

        except Exception as e:
            self.logger.log_message("error", f"同步到服务器失败: {e}")
            return False

    def test_connection(self) -> Dict:
        """测试服务器连接"""
        try:
            server_url = self.settings_manager.get_setting("server_url", "")
            if not server_url:
                return {"success": False, "message": "未配置服务器地址"}

            url = f"{server_url.rstrip('/')}/api/health"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            result = response.json()
            if result.get("success"):
                return {"success": True, "message": "连接成功", "data": result.get("data")}
            else:
                return {"success": False, "message": "服务器响应异常"}

        except requests.exceptions.Timeout:
            return {"success": False, "message": "连接超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "无法连接到服务器"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}
```

---

### 3. 更新 `schedule_manager.py`

添加获取所有数据的方法（用于同步）：

```python
def get_all_courses(self) -> List[Dict]:
    """获取所有课程（用于同步）"""
    cursor = self.conn.cursor()
    cursor.execute("""
        SELECT id, name, teacher, location, color, note
        FROM courses
        ORDER BY id
    """)

    courses = []
    for row in cursor.fetchall():
        courses.append({
            "id": row[0],
            "name": row[1],
            "teacher": row[2],
            "location": row[3],
            "color": row[4],
            "note": row[5]
        })

    return courses

def get_all_schedule_entries(self) -> List[Dict]:
    """获取所有课程表条目（用于同步）"""
    cursor = self.conn.cursor()
    cursor.execute("""
        SELECT s.id, s.course_id, s.day_of_week, s.start_time, s.end_time, s.weeks,
               c.name, c.teacher, c.location, c.color
        FROM schedule s
        JOIN courses c ON s.course_id = c.id
        ORDER BY s.day_of_week, s.start_time
    """)

    entries = []
    for row in cursor.fetchall():
        entries.append({
            "id": row[0],
            "course_id": row[1],
            "day_of_week": row[2],
            "start_time": row[3],
            "end_time": row[4],
            "weeks": row[5],
            "course_name": row[6],
            "teacher": row[7],
            "location": row[8],
            "color": row[9]
        })

    return entries
```

---

### 4. 集成到 `__init__.py`

在应用初始化时启动同步客户端：

```python
# 在 src-tauri/python/tauri_app/__init__.py

from .sync_client import SyncClient

# 全局变量
sync_client = None

def init():
    """应用初始化"""
    global logger, db_manager, settings_manager, schedule_manager, sync_client

    # ... 现有初始化代码 ...

    # 初始化同步客户端
    sync_client = SyncClient(settings_manager, schedule_manager, logger)

    # 启动时尝试注册客户端
    sync_enabled = settings_manager.get_setting("sync_enabled", "false")
    if sync_enabled.lower() == "true":
        sync_client.register_client()
        sync_client.start_auto_sync()

    logger.log_message("info", "应用初始化完成")

# 添加 Tauri 命令
@export_pyfunction(run_async=True)
def test_server_connection():
    """测试服务器连接"""
    if sync_client:
        return sync_client.test_connection()
    return {"success": False, "message": "同步客户端未初始化"}

@export_pyfunction(run_async=True)
def sync_now():
    """立即同步到服务器"""
    if sync_client:
        success = sync_client.sync_to_server()
        return {"success": success}
    return {"success": False, "message": "同步客户端未初始化"}

@export_pyfunction(run_async=True)
def register_to_server():
    """注册到服务器"""
    if sync_client:
        success = sync_client.register_client()
        return {"success": success}
    return {"success": False, "message": "同步客户端未初始化"}
```

---

## API 对接说明

### 服务端 API 端点

客户端需要调用的服务端 API：

#### 1. 客户端注册

**POST** `/api/clients/register`

**请求体**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "name": "教室电脑-01",
  "api_url": "http://192.168.1.100:8765"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "教室电脑-01",
    "status": "online"
  }
}
```

#### 2. 数据同步

**POST** `/api/sync`

**请求体**:
```json
{
  "client_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "courses": [
    {
      "id_on_client": 1,
      "name": "高等数学",
      "teacher": "张三",
      "location": "教学楼A101",
      "color": "#FF5722"
    }
  ],
  "schedule_entries": [
    {
      "id_on_client": 1,
      "course_id_on_client": 1,
      "day_of_week": 1,
      "start_time": "08:00",
      "end_time": "09:40",
      "weeks": [1, 2, 3, 4, 5, 6, 7, 8]
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "courses_synced": 1,
    "schedule_entries_synced": 1,
    "sync_time": "2025-10-09T10:30:00Z"
  }
}
```

#### 3. 健康检查

**GET** `/api/health`

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-10-09T10:30:00Z",
    "version": "0.1.0"
  }
}
```

---

## 配置管理

### 客户端设置项

在 `settings_manager.py` 中添加以下默认设置：

```python
DEFAULT_SETTINGS = {
    # ... 现有设置 ...

    # 服务器同步相关
    "client_uuid": "",           # 客户端唯一标识（首次启动自动生成）
    "client_name": "",           # 客户端名称（默认使用主机名）
    "server_url": "",            # 服务器地址，如 http://192.168.1.10:8765
    "sync_enabled": "false",     # 是否启用同步
    "sync_interval": "300",      # 同步间隔（秒），默认 5 分钟
}
```

### 前端设置界面

在 `src/pages/Settings.vue` 中添加服务器配置部分：

```vue
<template>
  <div class="settings-page">
    <!-- ... 现有设置 ... -->

    <!-- 服务器同步设置 -->
    <mdui-card variant="outlined" class="setting-card">
      <div class="card-header">
        <mdui-icon name="cloud_sync">cloud_sync</mdui-icon>
        <h3>服务器同步</h3>
      </div>

      <div class="card-content">
        <mdui-text-field
          v-model="serverUrl"
          label="服务器地址"
          placeholder="http://192.168.1.10:8765"
          helper="输入集中管理服务器的地址"
        ></mdui-text-field>

        <mdui-text-field
          v-model="clientName"
          label="客户端名称"
          placeholder="教室电脑-01"
          helper="在服务器上显示的名称"
        ></mdui-text-field>

        <mdui-switch
          v-model="syncEnabled"
          @change="handleSyncToggle"
        >启用自动同步</mdui-switch>

        <mdui-text-field
          v-if="syncEnabled"
          v-model="syncInterval"
          type="number"
          label="同步间隔（秒）"
          helper="数据同步的时间间隔"
        ></mdui-text-field>

        <div class="button-group">
          <mdui-button
            @click="testConnection"
            variant="outlined"
          >测试连接</mdui-button>

          <mdui-button
            @click="registerClient"
            variant="outlined"
          >注册到服务器</mdui-button>

          <mdui-button
            @click="syncNow"
            variant="filled"
            :disabled="!syncEnabled"
          >立即同步</mdui-button>
        </div>

        <div v-if="syncStatus" class="sync-status">
          <mdui-icon :name="syncStatus.success ? 'check_circle' : 'error'">
            {{ syncStatus.success ? 'check_circle' : 'error' }}
          </mdui-icon>
          <span>{{ syncStatus.message }}</span>
        </div>
      </div>
    </mdui-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { invoke } from '@tauri-apps/api/core';

const serverUrl = ref('');
const clientName = ref('');
const syncEnabled = ref(false);
const syncInterval = ref(300);
const syncStatus = ref(null);

// 加载设置
onMounted(async () => {
  const settings = await invoke('get_all_settings');
  serverUrl.value = settings.server_url || '';
  clientName.value = settings.client_name || '';
  syncEnabled.value = settings.sync_enabled === 'true';
  syncInterval.value = parseInt(settings.sync_interval || '300');
});

// 保存设置
const saveSettings = async () => {
  await invoke('set_setting', { key: 'server_url', value: serverUrl.value });
  await invoke('set_setting', { key: 'client_name', value: clientName.value });
  await invoke('set_setting', { key: 'sync_enabled', value: syncEnabled.value.toString() });
  await invoke('set_setting', { key: 'sync_interval', value: syncInterval.value.toString() });
};

// 测试连接
const testConnection = async () => {
  await saveSettings();
  syncStatus.value = { success: false, message: '正在测试...' };

  try {
    const result = await invoke('test_server_connection');
    syncStatus.value = result;
  } catch (error) {
    syncStatus.value = { success: false, message: `错误: ${error}` };
  }
};

// 注册客户端
const registerClient = async () => {
  await saveSettings();
  syncStatus.value = { success: false, message: '正在注册...' };

  try {
    const result = await invoke('register_to_server');
    if (result.success) {
      syncStatus.value = { success: true, message: '注册成功' };
    } else {
      syncStatus.value = { success: false, message: '注册失败' };
    }
  } catch (error) {
    syncStatus.value = { success: false, message: `错误: ${error}` };
  }
};

// 立即同步
const syncNow = async () => {
  await saveSettings();
  syncStatus.value = { success: false, message: '正在同步...' };

  try {
    const result = await invoke('sync_now');
    if (result.success) {
      syncStatus.value = { success: true, message: '同步成功' };
    } else {
      syncStatus.value = { success: false, message: '同步失败' };
    }
  } catch (error) {
    syncStatus.value = { success: false, message: `错误: ${error}` };
  }
};

// 切换同步开关
const handleSyncToggle = async () => {
  await saveSettings();
  // 可以在这里重启同步线程
};
</script>

<style scoped>
.setting-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-bottom: 1px solid var(--mdui-color-surface-variant);
}

.card-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.button-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.sync-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 4px;
  background: var(--mdui-color-surface-container);
}

.sync-status mdui-icon {
  font-size: 20px;
}
</style>
```

---

## 数据同步流程

### 同步时序图

```
┌─────────┐                  ┌──────────────┐                ┌─────────┐
│ 客户端   │                  │  同步线程     │                │ 服务器   │
└────┬────┘                  └──────┬───────┘                └────┬────┘
     │                              │                             │
     │ 1. 启动应用                   │                             │
     ├─────────────────────────────>│                             │
     │                              │                             │
     │                              │ 2. 注册客户端                │
     │                              ├────────────────────────────>│
     │                              │                             │
     │                              │<────────────────────────────┤
     │                              │    UUID + 初始状态            │
     │                              │                             │
     │                              │ 3. 等待同步间隔               │
     │                              │ (5 分钟)                     │
     │                              │                             │
     │                              │ 4. 收集本地数据               │
     │                              │ - 所有课程                   │
     │                              │ - 所有课程表                 │
     │                              │                             │
     │                              │ 5. 发送同步请求               │
     │                              ├────────────────────────────>│
     │                              │                             │
     │                              │                             │ 6. UPSERT 数据
     │                              │                             │    - 更新已存在
     │                              │                             │    - 插入新数据
     │                              │                             │
     │                              │<────────────────────────────┤
     │                              │    同步结果                   │
     │                              │                             │
     │                              │ 7. 记录日志                  │
     │<─────────────────────────────┤                             │
     │    触发事件（可选）             │                             │
     │                              │                             │
     └──────────────────────────────┴─────────────────────────────┘
```

### 同步策略

1. **注册阶段**:
   - 客户端启动时生成或读取 UUID
   - 向服务器发送注册请求
   - 服务器记录客户端信息和状态

2. **定期同步**:
   - 默认每 5 分钟同步一次
   - 可在设置中调整间隔
   - 后台线程异步执行，不阻塞 UI

3. **数据更新策略 (UPSERT)**:
   - 服务器使用 `(client_id, id_on_client)` 作为唯一键
   - 已存在的记录会被更新
   - 新记录会被插入
   - 客户端删除的数据不会自动从服务器删除（需要额外实现）

4. **错误处理**:
   - 网络错误：记录日志，等待下次同步
   - 数据错误：记录详细错误信息，跳过问题数据
   - 服务器不可用：降级运行，本地功能不受影响

---

## UI 集成建议

### 1. 状态指示器

在 TopBar 或主界面显示同步状态：

```vue
<div class="sync-indicator">
  <mdui-icon :name="syncIcon" :color="syncColor"></mdui-icon>
  <span>{{ syncStatus }}</span>
</div>
```

状态类型：
- 🟢 `已同步` (绿色) - 最近一次同步成功
- 🟡 `同步中` (黄色) - 正在同步数据
- 🔴 `同步失败` (红色) - 最近一次同步失败
- ⚪ `未配置` (灰色) - 未启用同步功能

### 2. 同步日志查看

在设置页面添加同步历史：

```vue
<mdui-list>
  <mdui-list-item v-for="log in syncLogs" :key="log.id">
    <mdui-icon :name="log.success ? 'check' : 'close'"></mdui-icon>
    <div>
      <div>{{ log.timestamp }}</div>
      <div>{{ log.message }}</div>
    </div>
  </mdui-list-item>
</mdui-list>
```

### 3. 手动同步按钮

在合适的位置添加手动同步触发：

```vue
<mdui-button
  icon="sync"
  @click="manualSync"
  :loading="isSyncing"
>
  立即同步
</mdui-button>
```

---

## 测试指南

### 本地测试步骤

#### 1. 启动服务端

```bash
cd Classtop-Management-Server

# 配置数据库
cp .env.example .env
# 编辑 .env 设置 PostgreSQL 连接

# 启动服务器
cargo run --release
```

访问 http://localhost:8765 确认服务器运行。

#### 2. 配置客户端

1. 启动 ClassTop 客户端
2. 进入设置页面
3. 填写服务器地址：`http://localhost:8765`
4. 设置客户端名称：`测试客户端-01`
5. 点击"测试连接"，确认连接成功
6. 点击"注册到服务器"
7. 启用"自动同步"开关
8. 设置同步间隔：`60`（1 分钟，方便测试）

#### 3. 添加测试数据

在客户端添加几门课程和课程表：

1. 课程：高等数学、大学英语
2. 课程表：周一 08:00-09:40 高等数学

#### 4. 触发同步

- 点击"立即同步"按钮
- 或等待自动同步（1 分钟后）

#### 5. 验证同步结果

访问服务器管理界面：
- http://localhost:8765
- 进入"客户端"页面
- 查看客户端状态和最后同步时间
- 进入"数据查看"页面
- 选择客户端，查看同步的课程和课程表

### 测试清单

- [ ] 客户端成功注册到服务器
- [ ] 课程数据正确同步
- [ ] 课程表数据正确同步
- [ ] 周次数据正确处理（JSON 数组）
- [ ] 更新课程后再次同步，服务端数据被更新
- [ ] 删除课程后同步，服务端数据保留（预期行为）
- [ ] 断网情况下客户端正常运行
- [ ] 恢复网络后自动同步成功
- [ ] 服务器不可用时客户端不崩溃
- [ ] 同步日志正确记录
- [ ] 多个客户端可以同时同步到同一服务器

---

## 注意事项

### 安全考虑

⚠️ **当前版本未实现身份验证**

生产环境建议：
1. 使用 HTTPS 加密传输
2. 添加 API Key 或 Token 认证
3. 限制服务器仅在内网访问
4. 使用防火墙规则限制访问

### 数据一致性

- 客户端数据为主要数据源
- 服务器仅用于集中查看和管理
- 当前不支持从服务器反向同步到客户端（未来功能）
- 客户端删除的数据不会从服务器删除

### 性能优化

- 仅在数据变化时同步（可选优化）
- 使用增量同步而非全量同步（可选优化）
- 限制同步频率，避免过度请求
- 使用连接池复用 HTTP 连接

---

## 故障排查

### 常见问题

#### 1. 无法连接到服务器

**检查清单**:
- [ ] 服务器是否正在运行？
- [ ] 服务器地址是否正确？
- [ ] 网络是否可达？（ping 测试）
- [ ] 防火墙是否允许端口 8765？

**解决方法**:
```bash
# 测试服务器健康状态
curl http://服务器地址:8765/api/health

# 检查防火墙（Linux）
sudo ufw allow 8765
```

#### 2. 注册失败

**可能原因**:
- UUID 格式错误
- 客户端名称为空
- 服务器数据库连接失败

**解决方法**:
- 检查客户端日志
- 检查服务器日志
- 重新生成 UUID

#### 3. 同步数据不完整

**可能原因**:
- 数据格式错误（如 weeks 字段）
- 外键约束失败
- 字段类型不匹配

**解决方法**:
- 检查客户端数据库 Schema
- 确保 location 字段已添加
- 验证 JSON 格式正确

#### 4. 同步性能问题

**可能原因**:
- 数据量过大
- 同步间隔过短
- 网络延迟高

**解决方法**:
- 增加同步间隔
- 实现增量同步
- 使用批量操作

---

## 下一步计划

### 短期目标

- [ ] 实现基础同步功能
- [ ] 添加客户端设置界面
- [ ] 完成测试验证

### 中期目标

- [ ] 实现增量同步
- [ ] 添加同步冲突解决
- [ ] 支持从服务器拉取配置

### 长期目标

- [ ] 双向数据同步
- [ ] 实时数据推送（WebSocket）
- [ ] 客户端远程控制
- [ ] 批量配置部署

---

## 相关文档

- [服务端 API 文档](./ClassTop-Client-API.md)
- [客户端 API 文档](https://github.com/Zixiao-System/classtop/tree/main/docs)
- [数据库 Schema 说明](../migrations/001_initial_postgresql.sql)

---

**版本**: 1.0.0
**最后更新**: 2025-10-29
**维护者**: Amiya167