# ClassTop

一个基于 Tauri + Vue 3 + PyTauri 的桌面课程管理与显示工具，提供置顶进度条和全功能管理界面。

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MPL_v2-green)

## 📝 应用Logo

应用使用的Logo文件位于以下目录：

- **源文件**: `icons/Icon-iOS-Default-1024x1024@1x.png` (1024x1024)
- **应用图标**: `src-tauri/icons/` 目录包含各平台所需的多种尺寸图标
  - PNG 文件：32x32, 128x128, 256x256 (128x128@2x), 512x512
  - macOS 图标：icon.icns
  - Windows 图标：icon.ico
  - Windows Store 图标：Square*.png 系列

## ✨ 特性

### 置顶进度条 (TopBar)

- 🎯 **实时课程显示**：显示当前课程名称、地点和时间
- 📊 **进度可视化**：实时更新课程进度条
- ⏰ **课间倒计时**：课间时显示下一节课信息和剩余时间
- 🕐 **时钟组件**：显示当前时间
- 📌 **始终置顶**：窗口始终保持在屏幕顶部
- 🪟 **透明窗口**：无边框透明设计，融入桌面

### 课程管理

- 📅 **完整课程表管理**：添加、编辑、删除课程
- 📝 **详细信息记录**：课程名、教师、地点、时间、周次
- 🎨 **自定义颜色**：为每门课程设置独特颜色
- 📖 **周次管理**：支持学期周数设置和自动计算
- 🔄 **实时同步**：课程数据变化立即反映到 TopBar

### 系统功能

- 🔔 **系统托盘**：最小化到系统托盘，快速访问
- 💾 **本地存储**：使用 SQLite 数据库持久化数据
- 🚀 **高性能**：Rust + Python 混合架构，响应迅速
- 🎨 **Material Design**：基于 MDUI 2.x 的现代化界面

## 🏗️ 技术栈

### 前端

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite 6
- **路由**: Vue Router 4
- **UI 组件**: MDUI 2.1.4 (Material Design)
- **样式**: Less

### 后端

- **框架**: Tauri 2
- **Python 集成**: PyTauri 0.8
- **数据库**: SQLite
- **语言**: Rust + Python 3

## 📦 项目结构

```text
classtop/
├── src/                          # 前端源代码
│   ├── pages/                    # 页面组件
│   │   ├── Home.vue             # 主页
│   │   ├── Settings.vue         # 设置页
│   │   └── SchedulePage.vue     # 课程表管理页
│   ├── TopBar/                   # 置顶栏组件
│   │   ├── TopBar.vue           # 顶部栏主组件
│   │   └── components/
│   │       ├── Clock.vue        # 时钟组件
│   │       └── Schedule.vue     # 课程进度组件
│   ├── utils/                    # 工具函数
│   │   ├── schedule.js          # 课程相关工具函数
│   │   ├── globalVars.js        # 全局响应式变量管理
│   │   ├── collapse.js          # 控制TopBar的折叠
│   │   └── config.js            # 设置操作接口
│   ├── App.vue                   # 主应用组件
│   ├── Main.vue                  # 主窗口组件
│   └── main.js                   # 入口文件
├── src-tauri/                    # Tauri 后端
│   ├── python/tauri_app/        # Python 后端模块
│   │   ├── __init__.py          # 初始化
│   │   ├── commands.py          # Tauri 命令处理
│   │   ├── db.py                # 数据库操作
│   │   ├── schedule_manager.py  # 课程管理逻辑
│   │   ├── events.py            # 事件系统
│   │   ├── tray.py              # 系统托盘
│   │   └── logger.py            # 日志系统
│   ├── src/                      # Rust 源代码
│   ├── capabilities/             # 权限配置
│   └── tauri.conf.json          # Tauri 配置
├── public/                       # 静态资源
├── package.json                  # 项目配置
└── vite.config.js               # Vite 配置
```

## 📚 开发文档

### 平台开发指南

- **[Linux 开发环境搭建](./docs/LINUX_SETUP.md)** - Ubuntu/Debian/Fedora/Arch Linux 开发环境配置
- **[macOS 开发环境搭建](./docs/MACOS_SETUP.md)** - macOS 开发环境配置（Intel/Apple Silicon）
- **[Windows 开发环境搭建](#windows-开发环境)** - Windows 开发环境配置（见下文）

### IDE/编辑器配置

- **[VSCode 配置指南](./docs/VSCODE_SETUP.md)** - 全平台推荐，完整的扩展和配置说明
- **[Xcode 配置指南](./docs/XCODE_SETUP.md)** - macOS 专用，用于高级调试和性能分析
- **[Visual Studio 配置指南](./docs/VISUAL_STUDIO_SETUP.md)** - Windows 专用，用于高级调试和性能分析

### 管理服务器文档

- **[管理服务器改进方案](./docs/MANAGEMENT_SERVER_IMPROVEMENT_PLAN.md)** - admin-server 和 Management-Server 的对比和改进计划
- **[快速同步指南](./docs/QUICK_START_SYNC.md)** - 5 步完成客户端与 Management-Server 的数据同步
- **[客户端适配指南](./docs/CLIENT_ADAPTATION.md)** - 详细的客户端集成说明
- **[集成任务清单](./docs/CLIENT_INTEGRATION_TODO.md)** - 集成 Management-Server 的完整任务列表

### 其他文档

- **[项目架构说明](./CLAUDE.md)** - 详细的项目架构和开发指南
- **[API 文档](./docs/API.md)** - HTTP API 接口说明
- **[API 快速开始](./docs/API_QUICKSTART.md)** - API 使用示例

## 🚀 快速开始

### 前置要求

- **Node.js** >= 18
- **Python** >= 3.10
- **Rust** (通过 rustup 安装)
- **npm** 或 **pnpm**

> 💡 **提示**: 完整的开发环境搭建指南请参考上方的 [平台开发指南](#平台开发指南)

### Windows 开发环境

Windows 开发环境常用步骤（已知项目使用 Node.js、Python 与 Rust）：

```powershell
# 安装前端依赖

npm install

# （可选）安装 Tauri CLI 以便进行打包
npm install -g @tauri-apps/cli

# 创建一个虚拟环境
uv venv --python-preference only-system

# 激活虚拟环境
& .venv/Scripts/Activate.ps1

# 安装依赖项
uv pip install -e src-tauri
```

### 开发模式（本地调试）

项目使用 Tauri + Vite，常见的开发命令：

```powershell
# 启动前端开发服务器并在 Tauri 中运行（依赖 package.json 中的脚本）
npm run tauri dev
```

运行时通常会打开 TopBar 与主窗口（TopBar 用于置顶显示，主窗口用于完整管理界面）。

### 构建生产版本

使用 Tauri 的打包命令：

- 首先根据 [PyTauri - Build Standalone Binary](https://pytauri.github.io/pytauri/latest/usage/tutorial/build-standalone/) 正确下载CPython到 `src-tauri\pyembed` 中

```powershell
# 构建并打包为可安装的桌面应用
./Build.ps1
```

构建产物通常位于 `src-tauri/target/bundle-release/` 下。
 
## 📖 核心功能说明

### 1. 课程进度显示

**文件**: `src/TopBar/components/Schedule.vue`

实时显示当前课程进度，支持：

- 课程进行中：显示进度百分比
- 课间休息：显示倒计时和下一节课信息
- 跨天查询：今日课程结束后显示明天的课程

**关键算法**:

- 基于实际课间时长（上一节课结束到下一节课开始）计算倒计时进度
- 使用 ISO weekday 格式 (1=周一, 7=周日) 统一日期处理
- 每秒更新显示，每 10 秒刷新数据

### 2. 课程管理

**文件**: `src-tauri/python/tauri_app/schedule_manager.py`

提供完整的 CRUD 操作：

```python
- add_course(name, teacher, color, note)        # 添加课程
- add_schedule_entry(course_id, day, start, end, weeks)  # 添加课程表条目
- update_schedule_entry(id, ...)                # 更新课程表
- delete_schedule_entry(id)                     # 删除课程表
- get_current_class(week)                       # 获取当前课程
- get_next_class(week)                          # 获取下一节课
- get_last_class(week)                          # 获取上一节课
```

### 3. 周数计算

支持两种模式：

1. **手动设置**: 在设置页手动指定当前周数 ( **已废弃** )
2. **自动计算**: 设置学期开始日期，自动计算当前周数

**文件**: `src-tauri/python/tauri_app/schedule_manager.py`

```python
def calculate_week_number(semester_start_date):
    # 从学期开始日期计算当前周数
    # 支持 ISO 8601 格式日期
```

### 4. 系统托盘

**文件**: `src-tauri/python/tauri_app/tray.py`

托盘菜单功能：

- 显示/隐藏主窗口
- 显示/隐藏顶部栏
- 退出应用程序

### 5. 数据库结构

**SQLite Schema** (`classtop.db`):

```sql
-- 课程表
CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    teacher TEXT,
    color TEXT,
    note TEXT
);

-- 课程表条目
CREATE TABLE schedule (
    id INTEGER PRIMARY KEY,
    course_id INTEGER,
    day_of_week INTEGER,  -- 1=周一, 7=周日
    start_time TEXT,      -- HH:MM 格式
    end_time TEXT,
    weeks TEXT,           -- JSON 数组: [1,2,3,...]
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- 配置表
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

## 🔄 管理服务器集成

ClassTop 支持两种管理服务器方案：

### 1. admin-server (内置)

**位置**: `admin-server/` 目录

**功能**:
- 🔌 WebSocket 实时控制
- ⚙️ 远程设置管理
- 📹 CCTV 监控管理

**快速开始**:
```bash
cd admin-server
pip install -r requirements.txt
python main.py
```

访问 http://localhost:8000 查看管理界面。

详见 [admin-server/README.md](./admin-server/README.md)

### 2. Classtop-Management-Server (企业级)

**仓库**: [Classtop-Management-Server](https://github.com/Zixiao-System/Classtop-Management-Server)

**功能**:
- 📊 多客户端数据同步
- 📈 统计分析和可视化
- 🗄️ PostgreSQL 数据持久化
- 🎨 Vue 3 + MDUI 2 管理界面

**集成指南**:
- [快速同步指南](./docs/QUICK_START_SYNC.md) - 5 步完成数据同步
- [客户端适配指南](./docs/CLIENT_ADAPTATION.md) - 完整集成说明

## 🎨 界面说明

### 主窗口

- **首页**: 欢迎页面
- **课程表**: 完整的课程管理界面，支持添加、编辑、删除课程
- **设置**: 周数管理、学期设置

### TopBar (置顶栏)

- 左侧：时钟显示
- 右侧：课程进度条
  - 正常上课：`课程名 @ 地点 (开始-结束)`
  - 课间休息：`下一节: 课程名 @ 地点 (X分钟后)`
  - 今日结束：`今日课程结束 - 下一节: 周X 课程名`

## 🔧 配置说明

### Tauri 配置 (`src-tauri/tauri.conf.json`)

```json
{
  "app": {
    "windows": [
      {
        "label": "topbar",
        "alwaysOnTop": true,    // 始终置顶
        "transparent": true,     // 透明窗口
        "decorations": false,    // 无边框
        "closable": false,       // 禁止关闭
        "skipTaskbar": false     // 显示在任务栏
      }
    ]
  }
}
```

### 权限配置 (`src-tauri/capabilities/default.json`)

配置了前端可访问的 Tauri 命令和 Python 函数调用权限。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可

本项目采用 Mozilla Public License 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [Tauri](https://tauri.app/) - 桌面应用框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [MDUI](https://www.mdui.org/) - Material Design UI 组件库
- [PyTauri](https://pytauri.github.io/) - Python-Tauri 集成

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://gitee.com/HwlloChen/classtop/issues)
- 发送邮件至：<hwllochen@qq.com>

---

Made with ❤️ by Classtop Team
