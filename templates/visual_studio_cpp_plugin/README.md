# ClassTop C++ 插件模板 (Visual Studio)

这是一个用于 ClassTop 的 C++ 插件项目模板,使用 Visual Studio 2019/2022 开发。

## 功能特性

- ✅ 基于 C++17 标准
- ✅ 完整的生命周期管理 (OnEnable, OnDisable, OnSave, OnRestore)
- ✅ 事件订阅系统
- ✅ 热重载支持
- ✅ 类型安全的 API 接口
- ✅ 详细的代码注释和示例

## 系统要求

- **操作系统**: Windows 10/11 (x64)
- **开发工具**: Visual Studio 2019 或 2022
- **C++ 标准**: C++17 或更高
- **ClassTop SDK**: 2.0.0 或更高版本

## 快速开始

### 1. 安装依赖

#### 安装 ClassTop SDK

下载并安装 ClassTop SDK:

```powershell
# 使用 vcpkg 安装(推荐)
vcpkg install classtop-sdk:x64-windows

# 或手动下载
# https://github.com/Zixiao-System/classtop-sdk/releases
```

#### 安装 nlohmann/json 库

```powershell
vcpkg install nlohmann-json:x64-windows
```

### 2. 配置项目

1. 将此模板复制到你的工作目录
2. 使用 Visual Studio 打开 `ClassTopPlugin.vcxproj`
3. 修改项目属性 → C/C++ → 常规 → 附加包含目录:
   - 添加 ClassTop SDK 头文件目录
   - 添加 nlohmann/json 头文件目录
4. 修改项目属性 → 链接器 → 常规 → 附加库目录:
   - 添加 ClassTop SDK 库目录

### 3. 自定义插件

#### 修改插件 ID 和元数据

编辑 `plugin.yaml`:

```yaml
metadata:
  id: "com.yourcompany.yourplugin"  # 修改为你的插件 ID
  name: "Your Plugin Name"
  author: "your-email@example.com"
```

编辑 `include/plugin.h`:

```cpp
std::string GetId() const override {
    return "com.yourcompany.yourplugin";  // 与 plugin.yaml 保持一致
}
```

#### 实现插件逻辑

在 `src/plugin.cpp` 中实现你的插件功能:

```cpp
void MyPlugin::OnEnable() {
    // 插件启用时的初始化代码
    api_->LogInfo("Plugin enabled");

    // 订阅事件
    api_->On("schedule_update", [this](const std::string& data) {
        // 处理事件
    });
}

void MyPlugin::OnDisable() {
    // 插件禁用时的清理代码
    api_->LogInfo("Plugin disabled");
}
```

### 4. 编译插件

在 Visual Studio 中:

1. 选择配置: Release | x64
2. 生成 → 生成解决方案 (Ctrl+Shift+B)
3. 编译后的 DLL 位于: `bin\x64\Release\plugin.dll`

### 5. 部署插件

将以下文件复制到 ClassTop 插件目录:

```
~/.classtop/plugins/yourplugin/
├── plugin.dll          # 编译后的动态库
├── plugin.yaml         # 插件元数据
├── plugin_ui.js        # (可选) 前端组件
└── plugin.crt          # (生产环境) 开发者证书
```

## 项目结构

```
ClassTopPlugin/
├── ClassTopPlugin.vcxproj    # Visual Studio 项目文件
├── include/
│   └── plugin.h              # 插件头文件
├── src/
│   └── plugin.cpp            # 插件实现
├── third_party/              # 第三方依赖
│   └── classtop_sdk/
│       ├── include/
│       └── lib/
├── plugin.yaml               # 插件元数据
└── README.md                 # 本文件
```

## API 使用示例

### 获取课程列表

```cpp
auto courses = api_->GetCourses();
for (const auto& course : courses) {
    api_->LogInfo("Course: " + course.name);
}
```

### 添加课程

```cpp
int course_id = api_->AddCourse(
    "Math",          // 课程名称
    "Dr. Smith",     // 教师
    "Room 101",      // 地点
    "#FF5733"        // 颜色
);
```

### 订阅事件

```cpp
api_->On("schedule_update", [this](const std::string& data) {
    api_->LogInfo("Schedule updated: " + data);
});
```

### 发送事件

```cpp
api_->EmitEvent("custom_event", R"({"key": "value"})");
```

### 读写配置

```cpp
// 读取
std::string value = api_->GetSetting("my_key");

// 写入
api_->SetSetting("my_key", "my_value");
```

## 调试

### 使用 Visual Studio 调试器

1. 设置 ClassTop 主应用为调试启动程序:
   - 项目属性 → 调试 → 命令: `C:\Path\To\ClassTop.exe`
2. 在代码中设置断点
3. 按 F5 开始调试

### 日志输出

使用 `api_->LogInfo()` 和 `api_->LogError()` 输出日志:

```cpp
api_->LogInfo("This is an info message");
api_->LogError("This is an error message");
```

日志文件位置: `~/.classtop/logs/plugin_<plugin_id>.log`

## 热重载

插件支持热重载,无需重启 ClassTop:

### 实现状态保存/恢复

```cpp
std::string MyPlugin::OnSave() {
    json state;
    state["counter"] = counter_;
    return state.dump();
}

void MyPlugin::OnRestore(const std::string& state) {
    json j = json::parse(state);
    counter_ = j["counter"];
}
```

### 触发热重载

在 ClassTop 主应用中:
- 进入插件管理页面
- 点击插件右上角的刷新按钮

## 常见问题

### Q: 编译时提示找不到 classtop/plugin.h

A: 检查项目属性 → C/C++ → 常规 → 附加包含目录,确保包含 ClassTop SDK 的 include 目录。

### Q: 链接时提示找不到 classtop_sdk.lib

A: 检查项目属性 → 链接器 → 常规 → 附加库目录,确保包含 ClassTop SDK 的 lib 目录。

### Q: 插件加载失败

A: 检查以下几点:
1. `plugin.yaml` 中的 `id` 与代码中的 `GetId()` 返回值一致
2. 插件编译为 x64 架构
3. 所有依赖的 DLL 都在系统路径或插件目录中
4. 查看 ClassTop 日志文件获取详细错误信息

### Q: 如何使用共享内存传输大数据?

A: 参考 ClassTop SDK 文档中的共享内存章节:

```cpp
#include "classtop/shared_memory.h"

auto shm = classtop::SharedMemory::Create("data", 1024*1024);
memcpy(shm->GetBuffer(), large_data, data_size);
api_->NotifySharedMemoryReady("data", data_size);
```

## 进阶开发

### 添加前端组件

创建 `plugin_ui.js`:

```javascript
export default {
  name: 'MyPluginUI',
  template: `
    <div class="my-plugin">
      <h3>My Plugin Settings</h3>
      <mdui-button @click="callBackend">Call Backend</mdui-button>
    </div>
  `,
  methods: {
    async callBackend() {
      // 调用插件后端
      await this.$classtop.plugins.invoke('com.yourcompany.yourplugin', 'custom_command');
    }
  }
};
```

### 使用特权 API

需要申请开发者证书并在 `plugin.yaml` 中声明:

```yaml
privileged_permissions:
  - privileged:management_sync
  - privileged:analytics

certificate:
  required: true
  path: "./plugin.crt"
```

## 相关文档

- [ClassTop 插件 IPC 规范](../../docs/PLUGIN_IPC_SPECIFICATION.md)
- [C++ 插件开发指南](../../docs/CPP_PLUGIN_GUIDE.md)
- [ClassTop API 参考](../../docs/PLUGIN_API_REFERENCE.md)

## 许可证

本模板使用 MIT 许可证。

## 支持

如有问题,请在 [GitHub Issues](https://github.com/Zixiao-System/classtop/issues) 中提出。
