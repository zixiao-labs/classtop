# ClassTop C++ 插件模板 (CMake)

这是一个用于 ClassTop 的跨平台 C++ 插件项目模板,使用 CMake 构建系统。

## 功能特性

- ✅ 跨平台支持 (Windows, Linux, macOS)
- ✅ 基于 C++17 标准
- ✅ 使用 CMake 构建系统
- ✅ 完整的生命周期管理
- ✅ 事件订阅系统
- ✅ 热重载支持
- ✅ 详细的代码注释

## 系统要求

- **CMake**: 3.15 或更高版本
- **C++ 编译器**:
  - GCC 7+ (Linux)
  - Clang 6+ (macOS/Linux)
  - MSVC 19.14+ (Visual Studio 2017+, Windows)
- **ClassTop SDK**: 2.0.0 或更高版本

## 快速开始

### 1. 安装依赖

#### Linux (Ubuntu/Debian)

```bash
# 安装构建工具
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# 安装 ClassTop SDK
# 下载并解压到 /usr/local
sudo tar -xzf classtop-sdk-linux-x64.tar.gz -C /usr/local

# 安装 nlohmann/json
sudo apt-get install nlohmann-json3-dev
```

#### macOS

```bash
# 使用 Homebrew
brew install cmake
brew install nlohmann-json

# 安装 ClassTop SDK
# 下载并解压到 /usr/local
sudo tar -xzf classtop-sdk-macos.tar.gz -C /usr/local
```

#### Windows

```powershell
# 使用 vcpkg
vcpkg install classtop-sdk:x64-windows
vcpkg install nlohmann-json:x64-windows

# 或使用 Chocolatey 安装 CMake
choco install cmake
```

### 2. 配置项目

```bash
# 克隆模板
git clone https://github.com/your-repo/classtop-cmake-plugin-template.git my-plugin
cd my-plugin

# 创建构建目录
mkdir build
cd build

# 配置 CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# 如果 ClassTop SDK 安装在自定义位置
cmake .. -DCMAKE_BUILD_TYPE=Release -DClassTopSDK_DIR=/path/to/sdk
```

### 3. 编译插件

```bash
# 在 build 目录中
cmake --build . --config Release

# 或使用 make (Linux/macOS)
make

# 或使用 MSBuild (Windows)
msbuild ClassTopPlugin.sln /p:Configuration=Release
```

编译后的插件位于:
- Linux/macOS: `build/bin/libplugin.so`
- Windows: `build/bin/Release/plugin.dll`

### 4. 安装插件

```bash
# 方式 1: 使用 CMake 安装
cmake --install . --prefix ~/.classtop/plugins/myplugin

# 方式 2: 手动复制
cp build/bin/libplugin.so ~/.classtop/plugins/myplugin/
cp plugin.yaml ~/.classtop/plugins/myplugin/
```

## 项目结构

```
cmake_cpp_plugin/
├── CMakeLists.txt        # CMake 构建脚本
├── include/
│   └── plugin.h          # 插件头文件
├── src/
│   └── plugin.cpp        # 插件实现
├── cmake/                # CMake 辅助脚本
│   └── Packaging.cmake   # 打包配置
├── plugin.yaml           # 插件元数据
└── README.md             # 本文件
```

## 自定义插件

### 修改插件 ID

编辑 `plugin.yaml`:

```yaml
metadata:
  id: "com.yourcompany.yourplugin"
  name: "Your Plugin Name"
```

编辑 `include/plugin.h` 和 `src/plugin.cpp`:

```cpp
std::string GetId() const override {
    return "com.yourcompany.yourplugin";
}
```

### 实现插件功能

在 `src/plugin.cpp` 中实现:

```cpp
void MyPlugin::OnEnable() {
    api_->LogInfo("Plugin enabled");

    // 订阅事件
    api_->On("schedule_update", [this](const std::string& data) {
        api_->LogInfo("Received event: " + data);
    });
}
```

## CMake 选项

### 构建选项

```bash
# Debug 构建
cmake .. -DCMAKE_BUILD_TYPE=Debug

# Release 构建
cmake .. -DCMAKE_BUILD_TYPE=Release

# 启用测试
cmake .. -DBUILD_TESTING=ON

# 启用打包
cmake .. -DBUILD_PACKAGE=ON
```

### 安装选项

```bash
# 指定安装前缀
cmake .. -DCMAKE_INSTALL_PREFIX=/opt/classtop/plugins

# 安装
cmake --install .
```

## 跨平台编译

### Linux → Windows (交叉编译)

```bash
# 使用 MinGW
cmake .. -DCMAKE_TOOLCHAIN_FILE=cmake/mingw-w64.cmake
cmake --build .
```

### 通用二进制 (macOS)

```bash
# Apple Silicon + Intel
cmake .. -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64"
cmake --build .
```

## 调试

### 使用 GDB (Linux)

```bash
# Debug 构建
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build .

# 运行 GDB
gdb --args /path/to/classtop --debug-plugin
```

### 使用 LLDB (macOS)

```bash
lldb /path/to/classtop -- --debug-plugin
```

### 使用 Visual Studio (Windows)

1. 生成 Visual Studio 解决方案:
   ```bash
   cmake .. -G "Visual Studio 17 2022"
   ```
2. 打开 `ClassTopPlugin.sln`
3. 设置断点并按 F5 调试

## API 使用示例

### 获取课程列表

```cpp
auto courses = api_->GetCourses();
for (const auto& course : courses) {
    api_->LogInfo("Course: " + course.name);
}
```

### 订阅事件

```cpp
api_->On("schedule_update", [this](const std::string& data) {
    api_->LogInfo("Event: " + data);
});
```

### 发送事件

```cpp
#include <nlohmann/json.hpp>

json data;
data["key"] = "value";
api_->EmitEvent("custom_event", data.dump());
```

## 打包插件

### 创建可分发包

```bash
# 配置时启用打包
cmake .. -DBUILD_PACKAGE=ON

# 构建
cmake --build .

# 打包
cpack

# 输出文件
# - ClassTopPlugin-1.0.0-Linux.tar.gz (Linux)
# - ClassTopPlugin-1.0.0-Darwin.tar.gz (macOS)
# - ClassTopPlugin-1.0.0-win64.zip (Windows)
```

### 自定义打包配置

编辑 `cmake/Packaging.cmake`:

```cmake
set(CPACK_PACKAGE_NAME "MyPlugin")
set(CPACK_PACKAGE_VENDOR "Your Company")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "My awesome plugin")
```

## 常见问题

### Q: CMake 找不到 ClassTopSDK

A: 设置 `ClassTopSDK_DIR`:

```bash
cmake .. -DClassTopSDK_DIR=/usr/local/lib/cmake/ClassTopSDK
```

### Q: 编译时提示找不到 nlohmann/json.hpp

A: 安装 nlohmann-json 或使用 FetchContent:

```cmake
include(FetchContent)
FetchContent_Declare(json
    URL https://github.com/nlohmann/json/releases/download/v3.11.2/json.tar.xz
)
FetchContent_MakeAvailable(json)
```

### Q: 如何在 Visual Studio Code 中开发?

A: 安装以下扩展:
- C/C++ Extension Pack
- CMake Tools

配置 `.vscode/settings.json`:

```json
{
    "cmake.configureArgs": [
        "-DClassTopSDK_DIR=/path/to/sdk"
    ],
    "cmake.buildDirectory": "${workspaceFolder}/build"
}
```

### Q: 如何使用共享内存?

A: 参考 SDK 文档:

```cpp
#include "classtop/shared_memory.h"

auto shm = classtop::SharedMemory::Create("data", 1024*1024);
memcpy(shm->GetBuffer(), data, size);
api_->NotifySharedMemoryReady("data", size);
```

## 性能优化

### 启用链接时优化 (LTO)

```cmake
# CMakeLists.txt
include(CheckIPOSupported)
check_ipo_supported(RESULT ipo_supported)

if(ipo_supported)
    set_target_properties(plugin PROPERTIES
        INTERPROCEDURAL_OPTIMIZATION TRUE
    )
endif()
```

### 优化编译选项

```cmake
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(plugin PRIVATE
        -O3 -march=native -flto
    )
elseif(MSVC)
    target_compile_options(plugin PRIVATE
        /O2 /GL
    )
endif()
```

## 相关文档

- [ClassTop 插件 IPC 规范](../../docs/PLUGIN_IPC_SPECIFICATION.md)
- [C++ 插件开发指南](../../docs/CPP_PLUGIN_GUIDE.md)
- [CMake 官方文档](https://cmake.org/documentation/)

## 许可证

MIT License

## 支持

如有问题,请提交 [GitHub Issues](https://github.com/Zixiao-System/classtop/issues)。
