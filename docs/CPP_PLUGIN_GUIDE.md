# ClassTop C++ 插件开发指南

## 目录

1. [快速入门](#快速入门)
2. [环境配置](#环境配置)
3. [项目创建](#项目创建)
4. [插件结构](#插件结构)
5. [生命周期管理](#生命周期管理)
6. [API 使用](#api-使用)
7. [高性能特性](#高性能特性)
8. [跨平台开发](#跨平台开发)
9. [调试技巧](#调试技巧)
10. [最佳实践](#最佳实践)
11. [常见问题](#常见问题)
12. [示例插件](#示例插件)

---

## 快速入门

### 10 分钟创建你的第一个 C++ 插件

#### 系统要求

- **Windows**: Visual Studio 2019/2022 或 MinGW
- **Linux**: GCC 7+ 或 Clang 6+
- **macOS**: Xcode 10+ 或 Clang 6+
- **CMake**: 3.15 或更高版本
- **ClassTop SDK**: 2.0.0 或更高版本

#### 快速开始 (使用 CMake)

```bash
# 1. 使用模板创建项目
cp -r templates/cmake_cpp_plugin my_plugin
cd my_plugin

# 2. 创建构建目录
mkdir build && cd build

# 3. 配置项目
cmake ..

# 4. 编译
cmake --build . --config Release

# 5. 安装到 ClassTop 插件目录
cmake --install . --prefix ~/.classtop/plugins/my_plugin
```

#### 验证插件

启动 ClassTop，进入 **设置 → 插件管理**，你应该能看到你的插件。

---

## 环境配置

### Windows 开发环境

#### Visual Studio

1. **安装 Visual Studio 2019/2022**
   - 工作负载: "使用 C++ 的桌面开发"
   - 组件: CMake 工具、Windows SDK

2. **安装 ClassTop SDK**

```powershell
# 使用 vcpkg (推荐)
vcpkg install classtop-sdk:x64-windows
vcpkg install nlohmann-json:x64-windows

# 或下载预编译版本
# https://github.com/Zixiao-System/classtop-sdk/releases
```

3. **设置环境变量**

```powershell
# 添加到系统环境变量
setx CLASSTOP_SDK_DIR "C:\path\to\classtop-sdk"
```

### Linux 开发环境

#### Ubuntu/Debian

```bash
# 安装构建工具
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# 安装 ClassTop SDK
# 方式 1: 从包管理器 (如果可用)
sudo apt-get install libclasst op-dev

# 方式 2: 手动安装
wget https://github.com/Zixiao-System/classtop-sdk/releases/download/v2.0.0/classtop-sdk-linux-x64.tar.gz
sudo tar -xzf classtop-sdk-linux-x64.tar.gz -C /usr/local

# 安装 nlohmann/json
sudo apt-get install nlohmann-json3-dev
```

#### Fedora

```bash
sudo dnf install gcc-c++ cmake git
sudo dnf install classtop-devel nlohmann-json-devel
```

### macOS 开发环境

```bash
# 安装 Xcode Command Line Tools
xcode-select --install

# 安装 Homebrew (如果没有)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install cmake
brew install nlohmann-json

# 安装 ClassTop SDK
# 下载并解压到 /usr/local
sudo tar -xzf classtop-sdk-macos.tar.gz -C /usr/local
```

---

## 项目创建

### 使用 Visual Studio 模板

1. 复制模板目录:
```powershell
cp -r templates/visual_studio_cpp_plugin my_plugin
```

2. 打开 `ClassTopPlugin.vcxproj`

3. 修改项目设置:
   - 项目属性 → C/C++ → 常规 → 附加包含目录
   - 项目属性 → 链接器 → 常规 → 附加库目录

### 使用 CMake 模板

1. 复制模板目录:
```bash
cp -r templates/cmake_cpp_plugin my_plugin
cd my_plugin
```

2. 编辑 `CMakeLists.txt`:
```cmake
project(MyPlugin
    VERSION 1.0.0
    DESCRIPTION "My ClassTop C++ plugin"
)
```

3. 编辑 `plugin.yaml`:
```yaml
metadata:
  id: "com.example.myplugin"
  name: "My Plugin"
  version: "1.0.0"
```

---

## 插件结构

### 目录结构

```
my_plugin/
├── CMakeLists.txt           # CMake 构建脚本
├── plugin.yaml              # 插件元数据
├── include/
│   └── plugin.h             # 插件头文件
├── src/
│   └── plugin.cpp           # 插件实现
├── third_party/             # 第三方依赖
│   └── classtop_sdk/
├── tests/                   # 单元测试 (可选)
│   └── plugin_test.cpp
└── README.md
```

### 插件基类

```cpp
// include/classtop/plugin.h (SDK 提供)

#pragma once

#include <string>
#include <memory>
#include "classtop/plugin_api.h"

namespace classtop {

class Plugin {
public:
    explicit Plugin(std::shared_ptr<PluginAPI> api) : api_(api) {}
    virtual ~Plugin() = default;

    // 生命周期钩子
    virtual void OnEnable() = 0;
    virtual void OnDisable() = 0;

    // 热重载支持
    virtual std::string OnSave() { return "{}"; }
    virtual void OnRestore(const std::string& state) {}

    // 获取插件 ID
    virtual std::string GetId() const = 0;

protected:
    std::shared_ptr<PluginAPI> api_;
};

} // namespace classtop
```

### 实现插件类

```cpp
// include/my_plugin.h

#pragma once

#include "classtop/plugin.h"

class MyPlugin : public classtop::Plugin {
public:
    explicit MyPlugin(std::shared_ptr<classtop::PluginAPI> api);

    void OnEnable() override;
    void OnDisable() override;
    std::string OnSave() override;
    void OnRestore(const std::string& state) override;
    std::string GetId() const override;

private:
    int counter_ = 0;
};
```

```cpp
// src/my_plugin.cpp

#include "my_plugin.h"
#include <nlohmann/json.hpp>

using json = nlohmann::json;

MyPlugin::MyPlugin(std::shared_ptr<classtop::PluginAPI> api)
    : classtop::Plugin(api) {
    // 构造函数
}

void MyPlugin::OnEnable() {
    api_->LogInfo("MyPlugin enabled");

    // 订阅事件
    api_->On("schedule_update", [this](const std::string& data) {
        api_->LogInfo("Schedule updated: " + data);
    });
}

void MyPlugin::OnDisable() {
    api_->LogInfo("MyPlugin disabled");
}

std::string MyPlugin::OnSave() {
    json state;
    state["counter"] = counter_;
    return state.dump();
}

void MyPlugin::OnRestore(const std::string& state) {
    json j = json::parse(state);
    counter_ = j.value("counter", 0);
}

std::string MyPlugin::GetId() const {
    return "com.example.myplugin";
}

// 导出函数
extern "C" {
    #ifdef _WIN32
        __declspec(dllexport)
    #else
        __attribute__((visibility("default")))
    #endif
    classtop::Plugin* CreatePlugin(std::shared_ptr<classtop::PluginAPI> api) {
        return new MyPlugin(api);
    }

    #ifdef _WIN32
        __declspec(dllexport)
    #else
        __attribute__((visibility("default")))
    #endif
    void DestroyPlugin(classtop::Plugin* plugin) {
        delete plugin;
    }
}
```

---

## 生命周期管理

### 生命周期钩子详解

#### OnEnable()

```cpp
void MyPlugin::OnEnable() {
    // 1. 初始化成员变量
    counter_ = 0;
    data_.clear();

    // 2. 加载配置
    std::string config_str = api_->GetPluginData("config");
    if (!config_str.empty()) {
        config_ = json::parse(config_str);
    }

    // 3. 订阅事件
    api_->On("schedule_update", [this](const std::string& data) {
        OnScheduleUpdate(data);
    });

    // 4. 初始化资源
    database_ = std::make_unique<Database>(api_);

    // 5. 启动后台线程 (如果需要)
    worker_thread_ = std::thread(&MyPlugin::BackgroundWorker, this);

    api_->LogInfo("Plugin initialization completed");
}
```

#### OnDisable()

```cpp
void MyPlugin::OnDisable() {
    // 1. 停止后台线程
    if (worker_thread_.joinable()) {
        stop_flag_ = true;
        worker_thread_.join();
    }

    // 2. 保存配置
    if (!config_.empty()) {
        api_->SetPluginData("config", config_.dump());
    }

    // 3. 释放资源
    database_.reset();

    // 4. 事件监听器会自动清理,但如果有手动管理的,需要显式清理

    api_->LogInfo("Plugin cleanup completed");
}
```

#### OnSave() / OnRestore()

```cpp
std::string MyPlugin::OnSave() {
    json state;
    state["counter"] = counter_;
    state["timestamp"] = std::time(nullptr);

    // 保存复杂数据结构
    state["cache"] = json::array();
    for (const auto& item : cache_) {
        state["cache"].push_back({
            {"key", item.first},
            {"value", item.second}
        });
    }

    api_->LogInfo("State saved: " + state.dump());
    return state.dump();
}

void MyPlugin::OnRestore(const std::string& state) {
    try {
        json j = json::parse(state);

        counter_ = j.value("counter", 0);

        // 恢复缓存
        if (j.contains("cache")) {
            for (const auto& item : j["cache"]) {
                cache_[item["key"]] = item["value"];
            }
        }

        api_->LogInfo("State restored successfully");
    } catch (const std::exception& e) {
        api_->LogError("Failed to restore state: " + std::string(e.what()));
    }
}
```

---

## API 使用

### PluginAPI 接口

```cpp
// include/classtop/plugin_api.h (SDK 提供)

namespace classtop {

class PluginAPI {
public:
    // ========== 课程服务 ==========
    virtual std::vector<Course> GetCourses() = 0;
    virtual Course GetCourse(int course_id) = 0;
    virtual int AddCourse(const std::string& name,
                          const std::string& teacher,
                          const std::string& location,
                          const std::string& color) = 0;
    virtual void UpdateCourse(int course_id,
                              const std::string& name,
                              const std::string& teacher,
                              const std::string& location,
                              const std::string& color) = 0;
    virtual bool DeleteCourse(int course_id) = 0;

    // ========== 日程服务 ==========
    virtual std::map<int, std::vector<ScheduleEntry>> GetScheduleForWeek(int week) = 0;
    virtual int AddScheduleEntry(int course_id,
                                  int day_of_week,
                                  const std::string& start_time,
                                  const std::string& end_time,
                                  const std::vector<int>& weeks) = 0;
    virtual bool DeleteScheduleEntry(int entry_id) = 0;

    // ========== 事件系统 ==========
    using EventCallback = std::function<void(const std::string&)>;
    virtual void EmitEvent(const std::string& event_name, const std::string& data) = 0;
    virtual void On(const std::string& event_name, EventCallback callback) = 0;
    virtual void Off(const std::string& event_name, EventCallback callback) = 0;

    // ========== 配置服务 ==========
    virtual std::string GetSetting(const std::string& key) = 0;
    virtual void SetSetting(const std::string& key, const std::string& value) = 0;

    // ========== 插件私有存储 ==========
    virtual std::string GetPluginData(const std::string& key) = 0;
    virtual void SetPluginData(const std::string& key, const std::string& value) = 0;

    // ========== 日志服务 ==========
    virtual void LogInfo(const std::string& message) = 0;
    virtual void LogWarning(const std::string& message) = 0;
    virtual void LogError(const std::string& message) = 0;
    virtual void LogDebug(const std::string& message) = 0;
};

} // namespace classtop
```

### 课程服务示例

```cpp
void MyPlugin::ProcessCourses() {
    // 获取所有课程
    auto courses = api_->GetCourses();

    api_->LogInfo("Total courses: " + std::to_string(courses.size()));

    for (const auto& course : courses) {
        std::stringstream ss;
        ss << "Course: " << course.name
           << " (Teacher: " << course.teacher
           << ", Location: " << course.location << ")";
        api_->LogInfo(ss.str());
    }

    // 添加新课程
    int course_id = api_->AddCourse(
        "Advanced Mathematics",  // name
        "Prof. Smith",           // teacher
        "A101",                  // location
        "#FF5733"                // color
    );

    api_->LogInfo("Added course with ID: " + std::to_string(course_id));

    // 更新课程
    api_->UpdateCourse(
        course_id,
        "Advanced Mathematics I",  // new name
        "Dr. Johnson",             // new teacher
        "B202",                    // new location
        "#33FF57"                  // new color
    );

    // 删除课程
    bool deleted = api_->DeleteCourse(course_id);
    if (deleted) {
        api_->LogInfo("Course deleted successfully");
    }
}
```

### 事件系统示例

```cpp
class EventDemoPlugin : public classtop::Plugin {
public:
    void OnEnable() override {
        // 订阅事件 - 使用 lambda
        api_->On("schedule_update", [this](const std::string& data) {
            OnScheduleUpdate(data);
        });

        // 订阅事件 - 使用成员函数指针需要包装
        auto callback = std::bind(&EventDemoPlugin::OnCourseUpdate, this, std::placeholders::_1);
        api_->On("course_update", callback);
    }

    void OnScheduleUpdate(const std::string& data) {
        api_->LogInfo("Schedule updated: " + data);

        // 解析 JSON 数据
        json event = json::parse(data);
        std::string action = event["action"];
        int entry_id = event["entry_id"];

        if (action == "added") {
            api_->LogInfo("New schedule entry ID: " + std::to_string(entry_id));
        }
    }

    void OnCourseUpdate(const std::string& data) {
        api_->LogInfo("Course updated: " + data);
    }

    void SendCustomEvent() {
        // 发送自定义事件
        json event_data;
        event_data["plugin"] = GetId();
        event_data["timestamp"] = std::time(nullptr);
        event_data["message"] = "Hello from C++ plugin";

        api_->EmitEvent("custom_event", event_data.dump());
    }
};
```

---

## 高性能特性

### 1. 共享内存 (零拷贝)

C++ 插件的最大优势之一是支持共享内存,适合处理大数据 (图像、视频、音频)。

```cpp
#include "classtop/shared_memory.h"

class ImageProcessingPlugin : public classtop::Plugin {
public:
    void ProcessLargeImage(const std::vector<uint8_t>& image_data) {
        // 创建共享内存区域 (1920x1080x3 = 6.2MB)
        auto shm = classtop::SharedMemory::Create("image_data", 1920 * 1080 * 3);

        // 写入数据 (零拷贝)
        void* buffer = shm->GetBuffer();
        std::memcpy(buffer, image_data.data(), image_data.size());

        // 通知主应用数据已就绪
        api_->NotifySharedMemoryReady("image_data", image_data.size());

        api_->LogInfo("Image data written to shared memory");
    }

    void ProcessImageFromSharedMemory() {
        // 读取共享内存
        auto shm = classtop::SharedMemory::Open("input_image");
        if (!shm) {
            api_->LogError("Failed to open shared memory");
            return;
        }

        uint8_t* data = static_cast<uint8_t*>(shm->GetBuffer());
        size_t size = shm->GetSize();

        // 处理图像数据
        ProcessImageData(data, size);

        api_->LogInfo("Processed image from shared memory");
    }

private:
    void ProcessImageData(uint8_t* data, size_t size) {
        // 图像处理逻辑
    }
};
```

### 2. 多线程处理

```cpp
#include <thread>
#include <atomic>
#include <queue>
#include <mutex>

class MultiThreadPlugin : public classtop::Plugin {
public:
    void OnEnable() override {
        stop_flag_ = false;

        // 启动工作线程
        for (int i = 0; i < 4; ++i) {
            workers_.emplace_back(&MultiThreadPlugin::WorkerThread, this, i);
        }

        api_->LogInfo("Started 4 worker threads");
    }

    void OnDisable() override {
        // 停止所有线程
        stop_flag_ = true;

        // 唤醒所有等待的线程
        cv_.notify_all();

        // 等待所有线程完成
        for (auto& worker : workers_) {
            if (worker.joinable()) {
                worker.join();
            }
        }

        api_->LogInfo("All worker threads stopped");
    }

    void AddTask(const std::string& data) {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        task_queue_.push(data);
        cv_.notify_one();  // 唤醒一个等待的线程
    }

private:
    void WorkerThread(int thread_id) {
        api_->LogInfo("Worker thread " + std::to_string(thread_id) + " started");

        while (!stop_flag_) {
            std::unique_lock<std::mutex> lock(queue_mutex_);

            // 等待任务或停止信号
            cv_.wait(lock, [this] {
                return !task_queue_.empty() || stop_flag_;
            });

            if (stop_flag_) {
                break;
            }

            if (!task_queue_.empty()) {
                std::string task = task_queue_.front();
                task_queue_.pop();
                lock.unlock();  // 释放锁

                // 处理任务
                ProcessTask(task);
            }
        }

        api_->LogInfo("Worker thread " + std::to_string(thread_id) + " stopped");
    }

    void ProcessTask(const std::string& task) {
        // 处理任务
        api_->LogInfo("Processing task: " + task);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    std::vector<std::thread> workers_;
    std::atomic<bool> stop_flag_{false};
    std::queue<std::string> task_queue_;
    std::mutex queue_mutex_;
    std::condition_variable cv_;
};
```

### 3. 性能优化技巧

#### 内存池

```cpp
template<typename T, size_t PoolSize = 1024>
class MemoryPool {
public:
    T* Allocate() {
        if (free_list_.empty()) {
            // 分配新块
            blocks_.emplace_back(std::make_unique<T[]>(PoolSize));
            for (size_t i = 0; i < PoolSize; ++i) {
                free_list_.push_back(&blocks_.back()[i]);
            }
        }

        T* ptr = free_list_.back();
        free_list_.pop_back();
        return ptr;
    }

    void Deallocate(T* ptr) {
        free_list_.push_back(ptr);
    }

private:
    std::vector<std::unique_ptr<T[]>> blocks_;
    std::vector<T*> free_list_;
};

// 使用
class MyPlugin : public classtop::Plugin {
private:
    MemoryPool<MyDataStruct> pool_;

    void ProcessData() {
        // 从池分配
        MyDataStruct* data = pool_.Allocate();

        // 使用数据
        // ...

        // 归还到池
        pool_.Deallocate(data);
    }
};
```

#### 对象复用

```cpp
class ObjectCache {
public:
    template<typename T>
    std::shared_ptr<T> Get() {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = cache_.find(typeid(T).name());
        if (it != cache_.end() && !it->second.empty()) {
            auto obj = std::static_pointer_cast<T>(it->second.back());
            it->second.pop_back();
            return obj;
        }

        return std::make_shared<T>();
    }

    template<typename T>
    void Return(std::shared_ptr<T> obj) {
        std::lock_guard<std::mutex> lock(mutex_);
        cache_[typeid(T).name()].push_back(obj);
    }

private:
    std::unordered_map<std::string, std::vector<std::shared_ptr<void>>> cache_;
    std::mutex mutex_;
};
```

---

## 跨平台开发

### 平台检测宏

```cpp
// platform.h
#pragma once

// 操作系统检测
#if defined(_WIN32) || defined(_WIN64)
    #define CLASSTOP_PLATFORM_WINDOWS
#elif defined(__APPLE__)
    #include <TargetConditionals.h>
    #if TARGET_OS_MAC
        #define CLASSTOP_PLATFORM_MACOS
    #endif
#elif defined(__linux__)
    #define CLASSTOP_PLATFORM_LINUX
#endif

// 编译器检测
#if defined(_MSC_VER)
    #define CLASSTOP_COMPILER_MSVC
#elif defined(__GNUC__)
    #define CLASSTOP_COMPILER_GCC
#elif defined(__clang__)
    #define CLASSTOP_COMPILER_CLANG
#endif

// 架构检测
#if defined(_M_X64) || defined(__x86_64__)
    #define CLASSTOP_ARCH_X64
#elif defined(_M_IX86) || defined(__i386__)
    #define CLASSTOP_ARCH_X86
#elif defined(_M_ARM64) || defined(__aarch64__)
    #define CLASSTOP_ARCH_ARM64
#endif

// 导出宏
#ifdef CLASSTOP_PLATFORM_WINDOWS
    #ifdef CLASSTOP_PLUGIN_EXPORTS
        #define PLUGIN_API __declspec(dllexport)
    #else
        #define PLUGIN_API __declspec(dllimport)
    #endif
#else
    #define PLUGIN_API __attribute__((visibility("default")))
#endif
```

### 平台特定代码

```cpp
#include "platform.h"

class MyPlugin : public classtop::Plugin {
public:
    std::string GetPlatformInfo() {
        #ifdef CLASSTOP_PLATFORM_WINDOWS
            return "Windows";
        #elif defined(CLASSTOP_PLATFORM_MACOS)
            return "macOS";
        #elif defined(CLASSTOP_PLATFORM_LINUX)
            return "Linux";
        #else
            return "Unknown";
        #endif
    }

    void PlatformSpecificOperation() {
        #ifdef CLASSTOP_PLATFORM_WINDOWS
            // Windows 特定代码
            WindowsOperation();
        #elif defined(CLASSTOP_PLATFORM_MACOS)
            // macOS 特定代码
            MacOSOperation();
        #elif defined(CLASSTOP_PLATFORM_LINUX)
            // Linux 特定代码
            LinuxOperation();
        #endif
    }

private:
    #ifdef CLASSTOP_PLATFORM_WINDOWS
    void WindowsOperation() {
        // Windows API 调用
    }
    #endif

    #ifdef CLASSTOP_PLATFORM_MACOS
    void MacOSOperation() {
        // macOS API 调用
    }
    #endif

    #ifdef CLASSTOP_PLATFORM_LINUX
    void LinuxOperation() {
        // Linux API 调用
    }
    #endif
};
```

### CMake 跨平台配置

```cmake
# CMakeLists.txt

if(WIN32)
    # Windows 特定配置
    target_compile_definitions(plugin PRIVATE
        _WIN32_WINNT=0x0601  # Windows 7
    )
    target_link_libraries(plugin PRIVATE
        ws2_32  # Windows Sockets
    )
elseif(APPLE)
    # macOS 特定配置
    target_link_libraries(plugin PRIVATE
        "-framework CoreFoundation"
        "-framework Foundation"
    )
elseif(UNIX)
    # Linux 特定配置
    target_link_libraries(plugin PRIVATE
        pthread
        dl
    )
endif()
```

---

## 调试技巧

### 1. 使用 Visual Studio 调试器

**配置调试启动项**:

项目属性 → 调试 → 命令:
```
C:\Path\To\ClassTop.exe
```

项目属性 → 调试 → 工作目录:
```
C:\Path\To\ClassTop\
```

**设置断点**:
```cpp
void MyPlugin::OnEnable() {
    api_->LogInfo("Plugin enabled");  // 在此行设置断点

    // 按 F9 设置断点
    // 按 F5 开始调试
    // 按 F10 单步执行
    // 按 F11 进入函数
}
```

### 2. 使用 GDB (Linux)

```bash
# Debug 构建
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build .

# 运行 GDB
gdb /path/to/classtop

# GDB 命令
(gdb) break MyPlugin::OnEnable  # 设置断点
(gdb) run                        # 运行程序
(gdb) next                       # 下一行
(gdb) step                       # 进入函数
(gdb) print variable_name        # 打印变量
(gdb) backtrace                  # 查看调用栈
```

### 3. 使用 LLDB (macOS)

```bash
# Debug 构建
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build .

# 运行 LLDB
lldb /path/to/ClassTop

# LLDB 命令
(lldb) breakpoint set --name MyPlugin::OnEnable
(lldb) run
(lldb) next
(lldb) step
(lldb) print variable_name
(lldb) bt  # 查看调用栈
```

### 4. 日志调试

```cpp
class MyPlugin : public classtop::Plugin {
public:
    void DebugFunction() {
        api_->LogDebug("=== Debug Function Start ===");

        // 记录变量值
        api_->LogDebug("counter = " + std::to_string(counter_));

        // 记录指针地址
        std::stringstream ss;
        ss << "pointer address: " << static_cast<void*>(data_ptr_);
        api_->LogDebug(ss.str());

        // 记录堆栈跟踪
        #ifdef CLASSTOP_PLATFORM_LINUX
            void* array[10];
            size_t size = backtrace(array, 10);
            char** strings = backtrace_symbols(array, size);

            api_->LogDebug("Stack trace:");
            for (size_t i = 0; i < size; ++i) {
                api_->LogDebug(strings[i]);
            }
            free(strings);
        #endif

        api_->LogDebug("=== Debug Function End ===");
    }
};
```

### 5. 性能分析

#### Valgrind (Linux)

```bash
# 内存泄漏检测
valgrind --leak-check=full --show-leak-kinds=all /path/to/classtop

# 性能分析
valgrind --tool=callgrind /path/to/classtop
kcachegrind callgrind.out.<pid>
```

#### Visual Studio 分析器 (Windows)

1. 调试 → 性能分析器
2. 选择 "CPU 使用情况" 或 "内存使用情况"
3. 开始分析

---

## 最佳实践

### 1. RAII (资源获取即初始化)

```cpp
class DatabaseConnection {
public:
    DatabaseConnection(const std::string& connection_string) {
        // 打开连接
        connection_ = OpenDatabase(connection_string);
    }

    ~DatabaseConnection() {
        // 自动关闭连接
        if (connection_) {
            CloseDatabase(connection_);
        }
    }

    // 禁止拷贝
    DatabaseConnection(const DatabaseConnection&) = delete;
    DatabaseConnection& operator=(const DatabaseConnection&) = delete;

    // 允许移动
    DatabaseConnection(DatabaseConnection&& other) noexcept
        : connection_(other.connection_) {
        other.connection_ = nullptr;
    }

private:
    void* connection_ = nullptr;
};

// 使用
void MyPlugin::UseDatabase() {
    DatabaseConnection db("connection_string");
    // 使用数据库
    // ...
    // 作用域结束时自动关闭连接
}
```

### 2. 智能指针

```cpp
class MyPlugin : public classtop::Plugin {
public:
    void OnEnable() override {
        // 使用 unique_ptr 管理独占资源
        database_ = std::make_unique<Database>();

        // 使用 shared_ptr 管理共享资源
        cache_ = std::make_shared<CacheManager>();
    }

private:
    std::unique_ptr<Database> database_;
    std::shared_ptr<CacheManager> cache_;
};
```

### 3. 异常安全

```cpp
class MyPlugin : public classtop::Plugin {
public:
    void SafeOperation() {
        try {
            // 可能抛出异常的操作
            RiskyOperation();
        } catch (const std::runtime_error& e) {
            api_->LogError("Runtime error: " + std::string(e.what()));
        } catch (const std::exception& e) {
            api_->LogError("Exception: " + std::string(e.what()));
        } catch (...) {
            api_->LogError("Unknown exception");
        }
    }

private:
    void RiskyOperation() {
        if (invalid_condition) {
            throw std::runtime_error("Invalid condition");
        }
    }
};
```

### 4. 现代 C++ 特性

```cpp
class ModernPlugin : public classtop::Plugin {
public:
    void UseModernFeatures() {
        // 1. auto 类型推导
        auto courses = api_->GetCourses();

        // 2. 范围 for 循环
        for (const auto& course : courses) {
            api_->LogInfo(course.name);
        }

        // 3. Lambda 表达式
        api_->On("event", [this](const std::string& data) {
            ProcessEvent(data);
        });

        // 4. std::optional (C++17)
        std::optional<Course> course = FindCourse("Math");
        if (course.has_value()) {
            api_->LogInfo("Found: " + course->name);
        }

        // 5. 结构化绑定 (C++17)
        auto [success, message] = ValidateData(data_);
        if (success) {
            api_->LogInfo(message);
        }

        // 6. if 初始化语句 (C++17)
        if (auto config = LoadConfig(); config.has_value()) {
            UseConfig(*config);
        }
    }

private:
    std::optional<Course> FindCourse(const std::string& name) {
        // 查找课程
        return std::nullopt;  // 未找到
    }

    std::pair<bool, std::string> ValidateData(const std::string& data) {
        if (data.empty()) {
            return {false, "Data is empty"};
        }
        return {true, "Validation passed"};
    }
};
```

---

## 常见问题

### Q1: 编译时提示找不到 classtop/plugin.h

**解决方案**:

CMake:
```cmake
target_include_directories(plugin PRIVATE
    ${ClassTopSDK_INCLUDE_DIRS}
)
```

Visual Studio:
- 项目属性 → C/C++ → 常规 → 附加包含目录
- 添加: `C:\path\to\classtop-sdk\include`

### Q2: 链接时提示找不到 classtop_sdk.lib

**解决方案**:

CMake:
```cmake
target_link_libraries(plugin PRIVATE
    ClassTopSDK::ClassTopSDK
)
```

Visual Studio:
- 项目属性 → 链接器 → 常规 → 附加库目录
- 添加: `C:\path\to\classtop-sdk\lib`

### Q3: 插件运行时崩溃

**原因**:
- 内存访问错误
- 未处理的异常
- ABI 不兼容

**调试步骤**:
```cpp
// 1. 添加异常处理
extern "C" PLUGIN_API classtop::Plugin* CreatePlugin(...) {
    try {
        return new MyPlugin(api);
    } catch (const std::exception& e) {
        // 记录错误
        std::cerr << "Failed to create plugin: " << e.what() << std::endl;
        return nullptr;
    }
}

// 2. 使用调试器定位崩溃位置
// 3. 检查编译器和标准库版本一致性
```

### Q4: 如何在 C++ 插件中使用第三方库?

**方案 1: 静态链接** (推荐)
```cmake
# 将第三方库静态链接到插件
target_link_libraries(plugin PRIVATE
    third_party_lib
)
```

**方案 2: 动态链接**
```cmake
# 确保第三方 DLL/SO 在系统路径或插件目录
install(FILES ${THIRD_PARTY_DLLS}
    DESTINATION plugins/myplugin
)
```

---

## 示例插件

### 完整示例: 图像处理插件

```cpp
// image_processor_plugin.h

#pragma once

#include "classtop/plugin.h"
#include "classtop/shared_memory.h"
#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>

class ImageProcessorPlugin : public classtop::Plugin {
public:
    explicit ImageProcessorPlugin(std::shared_ptr<classtop::PluginAPI> api);
    ~ImageProcessorPlugin() override;

    void OnEnable() override;
    void OnDisable() override;
    std::string OnSave() override;
    void OnRestore(const std::string& state) override;
    std::string GetId() const override;

private:
    void ProcessImageEvent(const std::string& event_data);
    void WorkerThread();
    void ProcessImage(const std::string& image_id);

    std::thread worker_;
    std::atomic<bool> stop_flag_{false};
    std::queue<std::string> task_queue_;
    std::mutex queue_mutex_;
    std::condition_variable cv_;

    int processed_count_ = 0;
};

// image_processor_plugin.cpp

#include "image_processor_plugin.h"
#include <nlohmann/json.hpp>
#include <cstring>

using json = nlohmann::json;

ImageProcessorPlugin::ImageProcessorPlugin(std::shared_ptr<classtop::PluginAPI> api)
    : classtop::Plugin(api) {}

ImageProcessorPlugin::~ImageProcessorPlugin() = default;

void ImageProcessorPlugin::OnEnable() {
    api_->LogInfo("ImageProcessorPlugin enabled");

    // 订阅图像处理事件
    api_->On("process_image", [this](const std::string& data) {
        ProcessImageEvent(data);
    });

    // 启动工作线程
    stop_flag_ = false;
    worker_ = std::thread(&ImageProcessorPlugin::WorkerThread, this);

    api_->LogInfo("Worker thread started");
}

void ImageProcessorPlugin::OnDisable() {
    api_->LogInfo("Stopping ImageProcessorPlugin...");

    // 停止工作线程
    stop_flag_ = true;
    cv_.notify_all();

    if (worker_.joinable()) {
        worker_.join();
    }

    api_->LogInfo("ImageProcessorPlugin disabled");
}

std::string ImageProcessorPlugin::OnSave() {
    json state;
    state["processed_count"] = processed_count_;
    return state.dump();
}

void ImageProcessorPlugin::OnRestore(const std::string& state) {
    try {
        json j = json::parse(state);
        processed_count_ = j.value("processed_count", 0);
        api_->LogInfo("Restored state: processed_count=" + std::to_string(processed_count_));
    } catch (const std::exception& e) {
        api_->LogError("Failed to restore state: " + std::string(e.what()));
    }
}

std::string ImageProcessorPlugin::GetId() const {
    return "com.example.imageprocessor";
}

void ImageProcessorPlugin::ProcessImageEvent(const std::string& event_data) {
    try {
        json event = json::parse(event_data);
        std::string image_id = event["image_id"];

        // 添加到任务队列
        {
            std::lock_guard<std::mutex> lock(queue_mutex_);
            task_queue_.push(image_id);
        }
        cv_.notify_one();

        api_->LogInfo("Image processing task queued: " + image_id);
    } catch (const std::exception& e) {
        api_->LogError("Failed to parse event: " + std::string(e.what()));
    }
}

void ImageProcessorPlugin::WorkerThread() {
    api_->LogInfo("Worker thread running");

    while (!stop_flag_) {
        std::unique_lock<std::mutex> lock(queue_mutex_);

        // 等待任务
        cv_.wait(lock, [this] {
            return !task_queue_.empty() || stop_flag_;
        });

        if (stop_flag_) {
            break;
        }

        if (!task_queue_.empty()) {
            std::string image_id = task_queue_.front();
            task_queue_.pop();
            lock.unlock();

            // 处理图像
            ProcessImage(image_id);
        }
    }

    api_->LogInfo("Worker thread stopped");
}

void ImageProcessorPlugin::ProcessImage(const std::string& image_id) {
    api_->LogInfo("Processing image: " + image_id);

    try {
        // 打开共享内存
        auto shm = classtop::SharedMemory::Open(image_id);
        if (!shm) {
            api_->LogError("Failed to open shared memory: " + image_id);
            return;
        }

        uint8_t* data = static_cast<uint8_t*>(shm->GetBuffer());
        size_t size = shm->GetSize();

        // 图像处理逻辑 (示例: 简单的灰度化)
        for (size_t i = 0; i < size; i += 3) {
            uint8_t r = data[i];
            uint8_t g = data[i + 1];
            uint8_t b = data[i + 2];

            // 灰度值 = 0.299*R + 0.587*G + 0.114*B
            uint8_t gray = static_cast<uint8_t>(
                0.299 * r + 0.587 * g + 0.114 * b
            );

            data[i] = data[i + 1] = data[i + 2] = gray;
        }

        processed_count_++;

        // 发送处理完成事件
        json result;
        result["image_id"] = image_id;
        result["processed_count"] = processed_count_;
        result["status"] = "completed";

        api_->EmitEvent("image_processed", result.dump());

        api_->LogInfo("Image processed successfully: " + image_id);
    } catch (const std::exception& e) {
        api_->LogError("Error processing image: " + std::string(e.what()));
    }
}

// 导出函数
extern "C" {
    #ifdef _WIN32
        __declspec(dllexport)
    #else
        __attribute__((visibility("default")))
    #endif
    classtop::Plugin* CreatePlugin(std::shared_ptr<classtop::PluginAPI> api) {
        return new ImageProcessorPlugin(api);
    }

    #ifdef _WIN32
        __declspec(dllexport)
    #else
        __attribute__((visibility("default")))
    #endif
    void DestroyPlugin(classtop::Plugin* plugin) {
        delete plugin;
    }
}
```

---

## 相关文档

- [插件 IPC 规范](./PLUGIN_IPC_SPECIFICATION.md)
- [Python 插件开发指南](./PYTHON_PLUGIN_GUIDE.md)
- [ClassTop SDK API 参考](./CLASSTOP_SDK_API_REFERENCE.md)

---

**文档版本**: 1.0.0
**最后更新**: 2025-11-01
**维护者**: ClassTop 开发团队
