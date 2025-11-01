# ClassTop Python 插件开发指南

## 目录

1. [快速入门](#快速入门)
2. [环境配置](#环境配置)
3. [插件结构](#插件结构)
4. [生命周期管理](#生命周期管理)
5. [API 使用](#api-使用)
6. [事件系统](#事件系统)
7. [配置管理](#配置管理)
8. [前端集成](#前端集成)
9. [调试技巧](#调试技巧)
10. [最佳实践](#最佳实践)
11. [常见问题](#常见问题)
12. [示例插件](#示例插件)

---

## 快速入门

### 5 分钟创建你的第一个插件

#### 1. 创建插件目录

```bash
mkdir -p ~/.classtop/plugins/hello_plugin
cd ~/.classtop/plugins/hello_plugin
```

#### 2. 创建插件元数据文件 `plugin.yaml`

```yaml
metadata:
  id: "com.example.hello"
  name: "Hello Plugin"
  version: "1.0.0"
  author: "your-email@example.com"
  description: "My first ClassTop plugin"
  language: "python"

dependencies:
  classtop_version: ">=2.0.0"

permissions:
  - read:courses
  - emit:events
```

#### 3. 创建插件主文件 `plugin.py`

```python
from tauri_app.plugin_system.base import Plugin

class HelloPlugin(Plugin):
    """我的第一个 ClassTop 插件"""

    async def on_enable(self):
        """插件启用时调用"""
        self.plugin_api.log_info("Hello, ClassTop!")

        # 获取课程列表
        courses = await self.plugin_api.get_courses()
        self.plugin_api.log_info(f"找到 {len(courses)} 门课程")

    async def on_disable(self):
        """插件禁用时调用"""
        self.plugin_api.log_info("Goodbye, ClassTop!")
```

#### 4. 启动 ClassTop

打开 ClassTop，进入 **设置 → 插件管理**，你的插件应该会自动显示。点击启用按钮即可激活插件！

---

## 环境配置

### 开发环境准备

#### Python 版本

ClassTop 需要 **Python 3.10 或更高版本**。

```bash
# 检查 Python 版本
python --version

# 或
python3 --version
```

#### 推荐的 IDE

1. **Visual Studio Code** (推荐)
   - 安装 Python 扩展
   - 安装 YAML 扩展
   - 配置 Python 解释器为 ClassTop 使用的版本

2. **PyCharm**
   - Professional 或 Community 版本均可
   - 配置项目 SDK 为 ClassTop Python 环境

#### 开发依赖

虽然插件运行时不需要额外安装依赖，但开发时建议安装以下工具：

```bash
# 类型提示和代码补全
pip install --user typing-extensions

# 代码格式化
pip install --user black

# 代码检查
pip install --user pylint
```

---

## 插件结构

### 标准插件目录结构

```
hello_plugin/
├── plugin.yaml           # 插件元数据 (必需)
├── plugin.py             # 插件主文件 (必需)
├── plugin_ui.js          # 前端组件 (可选)
├── config.json           # 用户配置 (自动生成)
├── plugin.crt            # 开发者证书 (生产环境)
├── README.md             # 说明文档
└── utils/                # 辅助模块 (可选)
    ├── __init__.py
    └── helpers.py
```

### plugin.yaml 详解

```yaml
# ========== 基本信息 ==========
metadata:
  id: "com.example.hello"        # 插件唯一 ID (必需)
  name: "Hello Plugin"            # 显示名称 (必需)
  version: "1.0.0"                # 版本号 (必需)
  author: "your@email.com"        # 作者邮箱 (必需)
  description: "插件描述"         # 描述 (必需)
  homepage: "https://github.com/..." # 主页 (可选)
  language: "python"              # 语言类型 (必需)

# ========== 依赖关系 ==========
dependencies:
  classtop_version: ">=2.0.0"     # ClassTop 最低版本
  python_packages:                # Python 依赖包 (可选)
    - requests>=2.28.0
    - numpy>=1.24.0

# ========== 权限声明 ==========
permissions:
  - read:courses                  # 读取课程
  - modify:courses                # 修改课程
  - read:schedules                # 读取日程
  - modify:schedules              # 修改日程
  - access:settings               # 访问设置
  - emit:events                   # 发送事件

# ========== 特权权限 (需要证书) ==========
privileged_permissions:
  - privileged:management_sync    # 同步到 Management-Server
  - privileged:analytics          # 上报分析数据

# ========== 证书配置 ==========
certificate:
  required: false                 # 是否需要证书
  path: "./plugin.crt"            # 证书路径
```

### plugin.py 基础结构

```python
from tauri_app.plugin_system.base import Plugin
from typing import Dict, Any

class MyPlugin(Plugin):
    """插件类必须继承自 Plugin 基类"""

    def __init__(self, plugin_api):
        super().__init__(plugin_api)
        # 初始化插件状态
        self.counter = 0

    async def on_enable(self):
        """
        插件启用时调用
        在此方法中初始化资源、订阅事件等
        """
        self.plugin_api.log_info(f"{self.id} enabled")

    async def on_disable(self):
        """
        插件禁用时调用
        在此方法中清理资源、取消事件订阅等
        """
        self.plugin_api.log_info(f"{self.id} disabled")

    async def on_save(self) -> Dict[str, Any]:
        """
        保存插件状态 (用于热重载)
        返回可序列化为 JSON 的字典
        """
        return {
            "counter": self.counter,
            "version": "1.0.0"
        }

    async def on_restore(self, state: Dict[str, Any]):
        """
        恢复插件状态 (用于热重载)
        state: on_save() 返回的状态字典
        """
        self.counter = state.get("counter", 0)
        self.plugin_api.log_info(f"State restored: counter={self.counter}")
```

---

## 生命周期管理

### 插件状态流转

```
DISCOVERED → LOADED → INITIALIZED → ENABLED
                                       ↕
                                   DISABLED → UNLOADED

热重载流程:
ENABLED → on_save() → on_disable() → RELOADING →
reload module → on_restore() → on_enable() → ENABLED
```

### 生命周期钩子

#### 1. `__init__(self, plugin_api)`

```python
def __init__(self, plugin_api):
    super().__init__(plugin_api)
    # 初始化成员变量
    self.data = {}
    self.callbacks = []
```

**调用时机**: 插件加载到内存时
**注意事项**:
- 不要在此处进行耗时操作
- 不要在此处订阅事件
- 仅用于初始化成员变量

#### 2. `async def on_enable(self)`

```python
async def on_enable(self):
    """插件启用"""
    # 1. 加载配置
    self.config = await self.load_config()

    # 2. 订阅事件
    self.plugin_api.on("schedule_update", self.on_schedule_update)

    # 3. 初始化资源
    self.database = await self.init_database()

    # 4. 启动后台任务
    asyncio.create_task(self.background_task())
```

**调用时机**: 用户启用插件或 ClassTop 启动时
**适用场景**:
- 加载配置
- 订阅事件
- 初始化数据库连接
- 启动后台任务

#### 3. `async def on_disable(self)`

```python
async def on_disable(self):
    """插件禁用"""
    # 1. 取消事件订阅
    self.plugin_api.off("schedule_update", self.on_schedule_update)

    # 2. 关闭数据库连接
    if hasattr(self, 'database'):
        await self.database.close()

    # 3. 停止后台任务
    if hasattr(self, 'task'):
        self.task.cancel()

    # 4. 保存配置
    await self.save_config()
```

**调用时机**: 用户禁用插件或 ClassTop 关闭时
**注意事项**:
- 必须释放所有资源
- 必须取消所有事件订阅
- 不要抛出异常

#### 4. `async def on_save(self) -> Dict[str, Any]`

```python
async def on_save(self) -> Dict[str, Any]:
    """保存插件状态"""
    return {
        "counter": self.counter,
        "last_update": self.last_update.isoformat(),
        "cache": self.cache,
        "version": "1.0.0"
    }
```

**调用时机**: 热重载前
**返回值**: 可 JSON 序列化的字典
**注意事项**:
- 不要保存不可序列化的对象 (如文件句柄、数据库连接)
- 保持状态最小化
- 添加版本号以支持向后兼容

#### 5. `async def on_restore(self, state: Dict[str, Any])`

```python
async def on_restore(self, state: Dict[str, Any]):
    """恢复插件状态"""
    # 检查版本兼容性
    version = state.get("version", "0.0.0")
    if version != "1.0.0":
        self.plugin_api.log_error(f"Version mismatch: {version}")
        return

    # 恢复状态
    self.counter = state.get("counter", 0)
    self.last_update = datetime.fromisoformat(state.get("last_update"))
    self.cache = state.get("cache", {})
```

**调用时机**: 热重载后，`on_enable()` 之前
**注意事项**:
- 处理状态不存在的情况
- 检查版本兼容性
- 提供合理的默认值

---

## API 使用

### PluginAPI 完整参考

#### 课程服务

##### 获取所有课程

```python
courses = await self.plugin_api.get_courses()

# courses 是 List[Course]
for course in courses:
    print(f"课程: {course.name}")
    print(f"教师: {course.teacher}")
    print(f"地点: {course.location}")
    print(f"颜色: {course.color}")
```

##### 根据 ID 获取课程

```python
course = await self.plugin_api.get_course(course_id=1)
if course:
    print(f"课程名称: {course.name}")
else:
    print("课程不存在")
```

##### 添加课程

```python
course_id = await self.plugin_api.add_course(
    name="高等数学",
    teacher="张教授",
    location="A101",
    color="#FF5733"
)
self.plugin_api.log_info(f"创建课程, ID: {course_id}")
```

##### 更新课程

```python
await self.plugin_api.update_course(
    course_id=1,
    name="高等数学 I",  # 新名称
    teacher="李教授",  # 新教师
    location="B202",   # 新地点
    color="#33FF57"    # 新颜色
)
```

##### 删除课程

```python
success = await self.plugin_api.delete_course(course_id=1)
if success:
    self.plugin_api.log_info("课程删除成功")
```

#### 日程服务

##### 获取指定周的日程

```python
# 获取第 1 周的日程
schedule = await self.plugin_api.get_schedule_for_week(week=1)

# schedule 是 Dict[int, List[ScheduleEntry]]
# 键是星期几 (1-7, 1=周一)
for day, entries in schedule.items():
    print(f"星期{day}:")
    for entry in entries:
        print(f"  {entry.start_time} - {entry.end_time}: {entry.course.name}")
```

##### 添加日程条目

```python
entry_id = await self.plugin_api.add_schedule_entry(
    course_id=1,
    day_of_week=1,          # 周一
    start_time="08:00",
    end_time="09:40",
    weeks=[1, 2, 3, 4, 5]   # 第 1-5 周
)
```

##### 删除日程条目

```python
await self.plugin_api.delete_schedule_entry(entry_id=10)
```

#### 事件系统

##### 发送事件

```python
# 发送简单事件
await self.plugin_api.emit_event("custom_event", {
    "message": "Hello from plugin",
    "timestamp": datetime.now().isoformat()
})

# 发送复杂事件
await self.plugin_api.emit_event("data_processed", {
    "plugin_id": self.id,
    "data": {
        "total": 100,
        "processed": 95,
        "errors": 5
    },
    "status": "completed"
})
```

##### 订阅事件

```python
async def on_enable(self):
    # 订阅日程更新事件
    self.plugin_api.on("schedule_update", self.on_schedule_update)

    # 订阅课程更新事件
    self.plugin_api.on("course_update", self.on_course_update)

async def on_schedule_update(self, data):
    """处理日程更新"""
    action = data.get("action")  # "added", "updated", "deleted"
    entry_id = data.get("entry_id")

    self.plugin_api.log_info(f"Schedule {action}: ID={entry_id}")

async def on_course_update(self, data):
    """处理课程更新"""
    action = data.get("action")
    course_id = data.get("course_id")

    if action == "added":
        # 新课程添加
        course = await self.plugin_api.get_course(course_id)
        self.plugin_api.log_info(f"新课程: {course.name}")
```

##### 取消订阅

```python
async def on_disable(self):
    # 取消订阅
    self.plugin_api.off("schedule_update", self.on_schedule_update)
    self.plugin_api.off("course_update", self.on_course_update)
```

#### 系统事件列表

| 事件名称 | 触发时机 | 数据格式 |
|---------|---------|---------|
| `schedule_update` | 日程变更 | `{"action": "added/updated/deleted", "entry_id": int}` |
| `course_update` | 课程变更 | `{"action": "added/updated/deleted", "course_id": int}` |
| `setting_update` | 设置变更 | `{"key": str, "value": str}` |
| `week_changed` | 当前周变更 | `{"old_week": int, "new_week": int}` |

#### 配置服务

##### 读取设置

```python
# 读取单个设置
current_week = await self.plugin_api.get_setting("current_week")
semester_start = await self.plugin_api.get_setting("semester_start_date")

# 读取所有设置
all_settings = await self.plugin_api.get_all_settings()
```

##### 写入设置

```python
# 写入单个设置
await self.plugin_api.set_setting("custom_key", "custom_value")

# 批量写入
await self.plugin_api.set_settings({
    "key1": "value1",
    "key2": "value2"
})
```

#### 插件私有存储

```python
# 读取插件私有数据
cached_data = await self.plugin_api.get_plugin_data("cache_key")

# 写入插件私有数据
await self.plugin_api.set_plugin_data("cache_key", {
    "timestamp": datetime.now().isoformat(),
    "data": [1, 2, 3, 4, 5]
})

# 删除插件私有数据
await self.plugin_api.delete_plugin_data("cache_key")
```

**注意**: 插件私有存储与其他插件隔离，卸载插件时会自动清除。

#### 日志服务

```python
# 信息日志
self.plugin_api.log_info("这是一条信息")

# 警告日志
self.plugin_api.log_warning("这是一条警告")

# 错误日志
self.plugin_api.log_error("这是一条错误")

# 调试日志 (仅在开发模式显示)
self.plugin_api.log_debug("这是调试信息")
```

日志文件位置: `~/.classtop/logs/plugin_<plugin_id>.log`

---

## 事件系统

### 事件驱动架构

ClassTop 插件系统采用事件驱动架构，插件可以:
1. **订阅系统事件** - 响应 ClassTop 的状态变化
2. **发送自定义事件** - 与其他插件通信

### 完整示例：日程同步插件

```python
from tauri_app.plugin_system.base import Plugin
from datetime import datetime
import asyncio

class ScheduleSyncPlugin(Plugin):
    """日程同步插件 - 监听日程变化并同步到外部服务"""

    async def on_enable(self):
        """启用插件"""
        # 订阅日程更新事件
        self.plugin_api.on("schedule_update", self.on_schedule_update)
        self.plugin_api.on("course_update", self.on_course_update)

        # 加载配置
        self.sync_url = await self.plugin_api.get_plugin_data("sync_url")
        if not self.sync_url:
            self.sync_url = "https://example.com/api/sync"
            await self.plugin_api.set_plugin_data("sync_url", self.sync_url)

        self.plugin_api.log_info("ScheduleSyncPlugin enabled")

    async def on_disable(self):
        """禁用插件"""
        self.plugin_api.off("schedule_update", self.on_schedule_update)
        self.plugin_api.off("course_update", self.on_course_update)
        self.plugin_api.log_info("ScheduleSyncPlugin disabled")

    async def on_schedule_update(self, data):
        """处理日程更新事件"""
        action = data.get("action")
        entry_id = data.get("entry_id")

        self.plugin_api.log_info(f"Schedule {action}: entry_id={entry_id}")

        # 同步到外部服务
        try:
            await self.sync_to_external_service(action, entry_id)

            # 发送同步成功事件
            await self.plugin_api.emit_event("sync_completed", {
                "plugin": self.id,
                "action": action,
                "entry_id": entry_id,
                "status": "success"
            })
        except Exception as e:
            self.plugin_api.log_error(f"Sync failed: {e}")

            # 发送同步失败事件
            await self.plugin_api.emit_event("sync_failed", {
                "plugin": self.id,
                "action": action,
                "entry_id": entry_id,
                "error": str(e)
            })

    async def on_course_update(self, data):
        """处理课程更新事件"""
        action = data.get("action")
        course_id = data.get("course_id")

        self.plugin_api.log_info(f"Course {action}: course_id={course_id}")

    async def sync_to_external_service(self, action, entry_id):
        """同步到外部服务"""
        # 模拟网络请求
        await asyncio.sleep(0.5)

        # 这里实现实际的同步逻辑
        # 例如使用 requests 库发送 HTTP 请求
        self.plugin_api.log_info(f"Synced to {self.sync_url}")
```

### 跨插件通信

插件之间可以通过自定义事件通信:

**插件 A (发送方)**:
```python
class PluginA(Plugin):
    async def send_data_to_plugin_b(self):
        """向插件 B 发送数据"""
        await self.plugin_api.emit_event("plugin_a_data", {
            "source": "plugin_a",
            "data": {"value": 123}
        })
```

**插件 B (接收方)**:
```python
class PluginB(Plugin):
    async def on_enable(self):
        """订阅插件 A 的事件"""
        self.plugin_api.on("plugin_a_data", self.on_plugin_a_data)

    async def on_plugin_a_data(self, data):
        """处理来自插件 A 的数据"""
        value = data.get("data", {}).get("value")
        self.plugin_api.log_info(f"Received from Plugin A: {value}")
```

---

## 配置管理

### 插件配置最佳实践

#### 1. 使用 config.json 存储用户配置

```python
import json
from pathlib import Path

class MyPlugin(Plugin):
    def get_config_path(self):
        """获取配置文件路径"""
        # 配置文件位于插件目录
        return Path(__file__).parent / "config.json"

    async def load_config(self):
        """加载配置"""
        config_path = self.get_config_path()

        # 默认配置
        default_config = {
            "sync_interval": 60,
            "enable_notifications": True,
            "api_endpoint": "https://example.com/api"
        }

        # 如果配置文件不存在，使用默认值
        if not config_path.exists():
            await self.save_config(default_config)
            return default_config

        # 读取配置
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # 合并默认值 (处理新增配置项)
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        return config

    async def save_config(self, config):
        """保存配置"""
        config_path = self.get_config_path()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
```

#### 2. 使用插件私有存储

```python
class MyPlugin(Plugin):
    async def on_enable(self):
        # 读取配置
        self.config = await self.load_config_from_storage()

    async def load_config_from_storage(self):
        """从插件私有存储加载配置"""
        config = await self.plugin_api.get_plugin_data("config")

        if not config:
            # 默认配置
            config = {
                "sync_interval": 60,
                "enable_notifications": True
            }
            await self.plugin_api.set_plugin_data("config", config)

        return config

    async def update_config(self, key, value):
        """更新配置项"""
        self.config[key] = value
        await self.plugin_api.set_plugin_data("config", self.config)
```

#### 3. 提供配置界面 (通过前端)

创建 `plugin_ui.js`:

```javascript
export default {
  name: 'MyPluginSettings',
  data() {
    return {
      config: {
        syncInterval: 60,
        enableNotifications: true,
        apiEndpoint: ''
      }
    }
  },
  async mounted() {
    // 加载配置
    const config = await this.$classtop.plugins.getData('com.example.myplugin', 'config');
    if (config) {
      this.config = config;
    }
  },
  methods: {
    async saveConfig() {
      // 保存配置
      await this.$classtop.plugins.setData('com.example.myplugin', 'config', this.config);
      mdui.snackbar({ message: '配置已保存' });
    }
  },
  template: `
    <div class="plugin-settings">
      <h3>插件配置</h3>

      <mdui-text-field
        label="同步间隔 (秒)"
        v-model.number="config.syncInterval"
        type="number"
      ></mdui-text-field>

      <mdui-switch v-model="config.enableNotifications">
        启用通知
      </mdui-switch>

      <mdui-text-field
        label="API 端点"
        v-model="config.apiEndpoint"
      ></mdui-text-field>

      <mdui-button @click="saveConfig">保存配置</mdui-button>
    </div>
  `
};
```

---

## 前端集成

### 创建前端组件

#### 1. 基础组件结构

创建 `plugin_ui.js`:

```javascript
export default {
  name: 'MyPluginComponent',

  // 组件数据
  data() {
    return {
      message: 'Hello from plugin',
      courses: []
    }
  },

  // 生命周期钩子
  async mounted() {
    // 组件挂载后调用
    await this.loadCourses();
  },

  // 方法
  methods: {
    async loadCourses() {
      // 调用插件后端
      const courses = await this.$classtop.plugins.invoke(
        'com.example.myplugin',
        'get_courses'
      );
      this.courses = courses;
    },

    async handleClick() {
      // 处理用户点击
      mdui.snackbar({ message: '按钮被点击' });
    }
  },

  // 模板
  template: `
    <div class="my-plugin">
      <h3>{{ message }}</h3>
      <mdui-list>
        <mdui-list-item v-for="course in courses" :key="course.id">
          {{ course.name }}
        </mdui-list-item>
      </mdui-list>
      <mdui-button @click="handleClick">点击我</mdui-button>
    </div>
  `
};
```

#### 2. 在预设位置注册组件

在 `plugin.yaml` 中声明:

```yaml
frontend:
  components:
    - zone: "settings_page"       # 设置页面
      component: "MyPluginSettings"

    - zone: "home_footer"          # 首页底部
      component: "MyPluginHome"
```

#### 3. 与后端通信

```javascript
export default {
  methods: {
    async callBackend() {
      try {
        // 调用插件后端方法
        const result = await this.$classtop.plugins.invoke(
          'com.example.myplugin',  // 插件 ID
          'my_custom_command',      // 命令名称
          { param1: 'value1' }      // 参数
        );

        console.log('Result:', result);
      } catch (error) {
        mdui.snackbar({ message: '调用失败: ' + error.message });
      }
    },

    async subscribeEvents() {
      // 订阅插件事件
      this.$classtop.plugins.on('custom_event', (data) => {
        console.log('Event received:', data);
      });
    }
  }
};
```

#### 4. 使用 MDUI 组件

```javascript
template: `
  <div class="plugin-ui">
    <!-- 按钮 -->
    <mdui-button variant="filled" @click="handleClick">
      点击我
    </mdui-button>

    <!-- 文本框 -->
    <mdui-text-field
      label="输入文本"
      v-model="text"
    ></mdui-text-field>

    <!-- 开关 -->
    <mdui-switch v-model="enabled">
      启用功能
    </mdui-switch>

    <!-- 列表 -->
    <mdui-list>
      <mdui-list-item v-for="item in items" :key="item.id">
        <mdui-list-item-text>{{ item.name }}</mdui-list-item-text>
      </mdui-list-item>
    </mdui-list>

    <!-- 卡片 -->
    <mdui-card>
      <mdui-card-content>
        <h3>卡片标题</h3>
        <p>卡片内容</p>
      </mdui-card-content>
    </mdui-card>
  </div>
`
```

---

## 调试技巧

### 1. 使用日志

```python
class MyPlugin(Plugin):
    async def debug_function(self):
        # 不同级别的日志
        self.plugin_api.log_debug("调试信息 (仅开发模式)")
        self.plugin_api.log_info("普通信息")
        self.plugin_api.log_warning("警告信息")
        self.plugin_api.log_error("错误信息")
```

查看日志:
```bash
# 实时查看日志
tail -f ~/.classtop/logs/plugin_<plugin_id>.log

# 查看最近 50 行
tail -n 50 ~/.classtop/logs/plugin_<plugin_id>.log
```

### 2. 使用断点调试

#### VS Code 配置

创建 `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug ClassTop Plugin",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "~/.classtop/plugins/myplugin"
        }
      ]
    }
  ]
}
```

在插件中添加调试支持:

```python
# 安装 debugpy
# pip install debugpy

import debugpy

class MyPlugin(Plugin):
    async def on_enable(self):
        # 启用调试服务器
        debugpy.listen(("localhost", 5678))
        self.plugin_api.log_info("Debug server started on port 5678")

        # 等待调试器连接
        # debugpy.wait_for_client()
```

### 3. 异常处理

```python
class MyPlugin(Plugin):
    async def safe_operation(self):
        """安全的操作,带异常处理"""
        try:
            # 可能抛出异常的代码
            result = await self.risky_operation()
            return result
        except ValueError as e:
            self.plugin_api.log_error(f"ValueError: {e}")
            return None
        except Exception as e:
            self.plugin_api.log_error(f"Unexpected error: {e}")
            # 记录详细的堆栈跟踪
            import traceback
            self.plugin_api.log_error(traceback.format_exc())
            return None
```

### 4. 性能分析

```python
import time
from functools import wraps

def measure_time(func):
    """装饰器: 测量函数执行时间"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start

        # 记录耗时
        plugin_api = args[0].plugin_api  # 假设第一个参数是 self
        plugin_api.log_debug(f"{func.__name__} took {elapsed:.2f}s")

        return result
    return wrapper

class MyPlugin(Plugin):
    @measure_time
    async def slow_operation(self):
        """耗时操作"""
        await asyncio.sleep(1)
```

### 5. 热重载测试

```python
class MyPlugin(Plugin):
    async def on_save(self):
        """保存状态"""
        state = {
            "counter": self.counter,
            "data": self.data,
            "timestamp": datetime.now().isoformat()
        }

        # 记录保存的状态
        self.plugin_api.log_debug(f"Saving state: {state}")
        return state

    async def on_restore(self, state):
        """恢复状态"""
        self.plugin_api.log_debug(f"Restoring state: {state}")

        self.counter = state.get("counter", 0)
        self.data = state.get("data", {})

        # 验证状态恢复
        self.plugin_api.log_info(f"State restored: counter={self.counter}")
```

---

## 最佳实践

### 1. 代码组织

#### 模块化设计

```
my_plugin/
├── plugin.yaml
├── plugin.py              # 主入口
├── utils/
│   ├── __init__.py
│   ├── database.py        # 数据库操作
│   ├── api_client.py      # API 客户端
│   └── helpers.py         # 辅助函数
└── plugin_ui.js
```

```python
# plugin.py
from .utils.database import Database
from .utils.api_client import APIClient

class MyPlugin(Plugin):
    async def on_enable(self):
        self.db = Database(self.plugin_api)
        self.api_client = APIClient(self.plugin_api)
```

### 2. 异步编程

```python
import asyncio

class MyPlugin(Plugin):
    async def on_enable(self):
        # 并发执行多个任务
        await asyncio.gather(
            self.init_database(),
            self.load_config(),
            self.connect_api()
        )

    async def init_database(self):
        """初始化数据库"""
        await asyncio.sleep(0.1)  # 模拟异步操作

    async def load_config(self):
        """加载配置"""
        await asyncio.sleep(0.1)

    async def connect_api(self):
        """连接 API"""
        await asyncio.sleep(0.1)
```

### 3. 错误处理

```python
class MyPlugin(Plugin):
    async def on_enable(self):
        """启用插件时的错误处理"""
        try:
            await self.init_resources()
        except Exception as e:
            self.plugin_api.log_error(f"Failed to initialize: {e}")
            # 清理已初始化的资源
            await self.cleanup()
            # 重新抛出异常,让插件系统标记为错误状态
            raise
```

### 4. 资源管理

```python
class MyPlugin(Plugin):
    async def on_enable(self):
        """使用 context manager 管理资源"""
        # 打开文件
        self.data_file = open("data.txt", "w")

    async def on_disable(self):
        """确保资源释放"""
        if hasattr(self, 'data_file'):
            self.data_file.close()
```

### 5. 配置验证

```python
class MyPlugin(Plugin):
    async def validate_config(self, config):
        """验证配置"""
        required_keys = ["api_key", "endpoint"]

        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")

        # 验证 URL 格式
        if not config["endpoint"].startswith("https://"):
            raise ValueError("Endpoint must use HTTPS")

        return True

    async def load_config(self):
        """加载并验证配置"""
        config = await self.plugin_api.get_plugin_data("config")

        try:
            await self.validate_config(config)
            return config
        except ValueError as e:
            self.plugin_api.log_error(f"Invalid config: {e}")
            # 返回默认配置
            return self.get_default_config()
```

### 6. 防止内存泄漏

```python
class MyPlugin(Plugin):
    async def on_enable(self):
        """启用插件"""
        self.callbacks = []

        # 注册回调
        callback = lambda data: self.handle_event(data)
        self.plugin_api.on("event", callback)
        self.callbacks.append(("event", callback))

    async def on_disable(self):
        """清理所有回调"""
        for event_name, callback in self.callbacks:
            self.plugin_api.off(event_name, callback)

        # 清空列表
        self.callbacks.clear()
```

---

## 常见问题

### Q1: 插件加载失败

**症状**: 插件在插件管理页面显示为错误状态

**原因**:
1. `plugin.yaml` 格式错误
2. `plugin.py` 中有语法错误
3. 缺少必需的权限声明

**解决方案**:
```bash
# 检查日志
tail -f ~/.classtop/logs/classtop.log

# 验证 YAML 格式
python -c "import yaml; yaml.safe_load(open('plugin.yaml'))"

# 检查 Python 语法
python -m py_compile plugin.py
```

### Q2: 无法调用 API

**症状**: 调用 `plugin_api` 方法时抛出 `PermissionDeniedError`

**原因**: 未在 `plugin.yaml` 中声明权限

**解决方案**:
```yaml
permissions:
  - read:courses      # 添加所需权限
  - modify:courses
```

### Q3: 事件监听器未触发

**症状**: 订阅的事件没有被调用

**原因**:
1. 事件名称拼写错误
2. 未在 `on_enable()` 中订阅
3. 在 `on_disable()` 中被取消订阅

**解决方案**:
```python
async def on_enable(self):
    # 确保在 on_enable() 中订阅
    self.plugin_api.on("schedule_update", self.on_schedule_update)

    # 检查事件名称拼写
    self.plugin_api.log_info("Subscribed to schedule_update")

async def on_schedule_update(self, data):
    """确保回调函数签名正确"""
    self.plugin_api.log_info(f"Event received: {data}")
```

### Q4: 热重载后状态丢失

**症状**: 热重载后插件状态被重置

**原因**: 未实现 `on_save()` 和 `on_restore()`

**解决方案**:
```python
async def on_save(self):
    """保存重要状态"""
    return {
        "counter": self.counter,
        "cache": self.cache,
        "version": "1.0.0"
    }

async def on_restore(self, state):
    """恢复状态"""
    self.counter = state.get("counter", 0)
    self.cache = state.get("cache", {})
```

### Q5: 异步操作阻塞主线程

**症状**: 插件执行耗时操作时 UI 卡顿

**原因**: 使用了同步 I/O 或阻塞操作

**解决方案**:
```python
import asyncio

class MyPlugin(Plugin):
    async def long_running_operation(self):
        """使用 asyncio 避免阻塞"""
        # 错误: 阻塞操作
        # time.sleep(5)

        # 正确: 异步操作
        await asyncio.sleep(5)

        # 或使用线程池执行同步操作
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.sync_operation)

    def sync_operation(self):
        """同步操作 (在线程池中执行)"""
        import time
        time.sleep(5)
        return "Done"
```

---

## 示例插件

### 完整示例: 课程提醒插件

```python
# plugin.py
from tauri_app.plugin_system.base import Plugin
from datetime import datetime, timedelta
import asyncio

class CourseReminderPlugin(Plugin):
    """课程提醒插件 - 在上课前 10 分钟发送提醒"""

    async def on_enable(self):
        """启用插件"""
        self.plugin_api.log_info("CourseReminderPlugin enabled")

        # 加载配置
        self.config = await self.load_config()
        self.reminder_minutes = self.config.get("reminder_minutes", 10)

        # 启动后台任务
        self.task = asyncio.create_task(self.check_reminders_loop())

    async def on_disable(self):
        """禁用插件"""
        if hasattr(self, 'task'):
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        self.plugin_api.log_info("CourseReminderPlugin disabled")

    async def load_config(self):
        """加载配置"""
        config = await self.plugin_api.get_plugin_data("config")
        if not config:
            config = {
                "reminder_minutes": 10,
                "enabled": True
            }
            await self.plugin_api.set_plugin_data("config", config)
        return config

    async def check_reminders_loop(self):
        """定期检查是否需要提醒"""
        while True:
            try:
                await self.check_and_send_reminders()
                # 每分钟检查一次
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.plugin_api.log_error(f"Error in reminder loop: {e}")
                await asyncio.sleep(60)

    async def check_and_send_reminders(self):
        """检查并发送提醒"""
        if not self.config.get("enabled", True):
            return

        # 获取当前周数
        current_week_info = await self.plugin_api.get_current_week()
        current_week = current_week_info.get("week")

        # 获取当前周的日程
        schedule = await self.plugin_api.get_schedule_for_week(current_week)

        # 获取今天是星期几 (1-7)
        now = datetime.now()
        today = now.isoweekday()

        # 获取今天的课程
        today_classes = schedule.get(today, [])

        for entry in today_classes:
            # 解析上课时间
            start_time = datetime.strptime(entry.start_time, "%H:%M").time()
            class_datetime = datetime.combine(now.date(), start_time)

            # 计算提醒时间
            reminder_time = class_datetime - timedelta(minutes=self.reminder_minutes)

            # 检查是否需要提醒 (在提醒时间前后 1 分钟内)
            time_diff = abs((now - reminder_time).total_seconds())

            if time_diff < 60:  # 1 分钟内
                await self.send_reminder(entry)

    async def send_reminder(self, entry):
        """发送提醒"""
        course = entry.course
        message = f"⏰ 提醒: {course.name} 将在 {self.reminder_minutes} 分钟后开始"

        # 记录日志
        self.plugin_api.log_info(f"Reminder: {message}")

        # 发送事件 (前端可以监听此事件显示通知)
        await self.plugin_api.emit_event("course_reminder", {
            "course_name": course.name,
            "teacher": course.teacher,
            "location": course.location,
            "start_time": entry.start_time,
            "minutes_before": self.reminder_minutes
        })
```

对应的前端组件 `plugin_ui.js`:

```javascript
export default {
  name: 'CourseReminderSettings',
  data() {
    return {
      config: {
        reminderMinutes: 10,
        enabled: true
      }
    }
  },
  async mounted() {
    // 加载配置
    const config = await this.$classtop.plugins.getData('com.example.reminder', 'config');
    if (config) {
      this.config.reminderMinutes = config.reminder_minutes;
      this.config.enabled = config.enabled;
    }

    // 监听提醒事件
    this.$classtop.plugins.on('course_reminder', this.onReminder);
  },
  beforeUnmount() {
    // 取消监听
    this.$classtop.plugins.off('course_reminder', this.onReminder);
  },
  methods: {
    async saveConfig() {
      // 保存配置
      await this.$classtop.plugins.setData('com.example.reminder', 'config', {
        reminder_minutes: this.config.reminderMinutes,
        enabled: this.config.enabled
      });

      mdui.snackbar({ message: '配置已保存' });
    },

    onReminder(data) {
      // 显示通知
      mdui.snackbar({
        message: `⏰ ${data.course_name} 将在 ${data.minutes_before} 分钟后开始`,
        action: '查看',
        onActionClick: () => {
          // 跳转到日程页面
          this.$router.push('/schedule');
        }
      });
    }
  },
  template: `
    <div class="reminder-settings">
      <h3>课程提醒设置</h3>

      <mdui-switch v-model="config.enabled">
        启用课程提醒
      </mdui-switch>

      <mdui-text-field
        label="提前提醒时间 (分钟)"
        v-model.number="config.reminderMinutes"
        type="number"
        min="1"
        max="60"
        helper="在上课前多少分钟提醒"
      ></mdui-text-field>

      <mdui-button variant="filled" @click="saveConfig">
        保存配置
      </mdui-button>
    </div>
  `
};
```

---

## 相关文档

- [插件 IPC 规范](./PLUGIN_IPC_SPECIFICATION.md)
- [C++ 插件开发指南](./CPP_PLUGIN_GUIDE.md)
- [插件 API 参考](./PLUGIN_API_REFERENCE.md)

---

**文档版本**: 1.0.0
**最后更新**: 2025-11-01
**维护者**: ClassTop 开发团队
