# C++ Hello World Plugin

A simple C++ plugin demonstrating the basic structure and IPC communication with ClassTop.

## Features

- ✅ Basic plugin lifecycle hooks
- ✅ Logging demonstration
- ✅ Fetching course data via C++ API
- ✅ Custom event emission
- ✅ State persistence (hot reload support)
- ✅ Cross-platform support (Windows, Linux, macOS)

## Requirements

- **CMake**: 3.15 or higher
- **C++ Compiler**: GCC 7+, Clang 6+, or MSVC 2017+
- **ClassTop SDK**: 2.0.0 or higher
- **nlohmann/json**: 3.10.0 or higher

## Building

### Linux/macOS

```bash
# Create build directory
mkdir build && cd build

# Configure
cmake ..

# Build
cmake --build . --config Release

# Install to ClassTop plugins directory
cmake --install . --prefix ~/.classtop/plugins/cpp_hello
```

### Windows

```powershell
# Create build directory
mkdir build
cd build

# Configure
cmake .. -G "Visual Studio 17 2022"

# Build
cmake --build . --config Release

# Install
cmake --install . --prefix %USERPROFILE%\.classtop\plugins\cpp_hello
```

## Installation

After building, the plugin files will be installed to:
- **Linux/macOS**: `~/.classtop/plugins/cpp_hello/`
- **Windows**: `%USERPROFILE%\.classtop\plugins\cpp_hello\`

The installed files include:
- `libplugin.so` / `libplugin.dylib` / `plugin.dll` - Plugin binary
- `plugin.yaml` - Plugin metadata

## What This Plugin Does

When enabled, this plugin:
1. Logs a welcome message with compilation info
2. Fetches all courses from the database
3. Displays the course count and details
4. Emits a `cpp_hello_started` event

When disabled, it:
1. Logs a goodbye message with statistics
2. Emits a `cpp_hello_stopped` event

## Events

This plugin emits two custom events:

### `cpp_hello_started`
```json
{
  "plugin_id": "com.example.cpp_hello",
  "message": "Hello from C++ plugin!",
  "language": "C++17",
  "timestamp": 1730462400
}
```

### `cpp_hello_stopped`
```json
{
  "plugin_id": "com.example.cpp_hello",
  "message": "Goodbye from C++ plugin!",
  "message_count": 5
}
```

## Project Structure

```
hello_world/
├── CMakeLists.txt       # CMake build configuration
├── plugin.yaml          # Plugin metadata
├── include/
│   └── plugin.h         # Plugin header
├── src/
│   └── plugin.cpp       # Plugin implementation
└── README.md            # This file
```

## Learning Points

This example demonstrates:

1. **Plugin Class Structure**: Inherit from `classtop::Plugin` base class
2. **Lifecycle Hooks**: `OnEnable()`, `OnDisable()`, `OnSave()`, `OnRestore()`
3. **API Usage**: `GetCourses()`, `LogInfo()`, `EmitEvent()`
4. **State Management**: Saving and restoring plugin state using JSON
5. **Error Handling**: Try-catch blocks for robust operation
6. **Cross-platform Export**: Platform-specific `PLUGIN_EXPORT` macro
7. **CMake Build System**: Cross-platform build configuration

## Code Highlights

### Plugin Export Functions

```cpp
extern "C" {
    PLUGIN_EXPORT classtop::Plugin* CreatePlugin(std::shared_ptr<classtop::PluginAPI> api) {
        return new HelloWorldPlugin(api);
    }

    PLUGIN_EXPORT void DestroyPlugin(classtop::Plugin* plugin) {
        delete plugin;
    }

    PLUGIN_EXPORT const char* GetPluginMetadata() {
        static const char* metadata = R"({"id": "com.example.cpp_hello", ...})";
        return metadata;
    }
}
```

### State Persistence with JSON

```cpp
std::string HelloWorldPlugin::OnSave() {
    json state;
    state["message_count"] = message_count_;
    state["version"] = "1.0.0";
    return state.dump();
}

void HelloWorldPlugin::OnRestore(const std::string& state) {
    json j = json::parse(state);
    message_count_ = j.value("message_count", 0);
}
```

### Event Emission

```cpp
json event_data;
event_data["plugin_id"] = GetId();
event_data["message"] = "Hello from C++ plugin!";
api_->EmitEvent("cpp_hello_started", event_data.dump());
```

## Debugging

### Linux (GDB)

```bash
# Build with debug symbols
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build .

# Run with GDB
gdb /path/to/classtop
(gdb) break HelloWorldPlugin::OnEnable
(gdb) run
```

### macOS (LLDB)

```bash
# Build with debug symbols
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build .

# Run with LLDB
lldb /path/to/ClassTop
(lldb) breakpoint set --name HelloWorldPlugin::OnEnable
(lldb) run
```

### Windows (Visual Studio)

1. Open the generated Visual Studio solution: `build/HelloWorldPlugin.sln`
2. Set breakpoints in `plugin.cpp`
3. Configure debugging:
   - Project Properties → Debugging → Command: `C:\Path\To\ClassTop.exe`
4. Press F5 to start debugging

## Next Steps

Once you understand this example, check out:
- `performance_monitor` - Multi-threading and background tasks
- `image_processor` - Shared memory and high-performance data processing

## Related Documentation

- [C++ Plugin Development Guide](../../../docs/CPP_PLUGIN_GUIDE.md)
- [Plugin IPC Specification](../../../docs/PLUGIN_IPC_SPECIFICATION.md)
- [ClassTop SDK API Reference](../../../docs/CLASSTOP_SDK_API_REFERENCE.md)
