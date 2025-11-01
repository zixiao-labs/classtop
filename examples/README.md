# ClassTop Plugin Examples

This directory contains complete, working example plugins demonstrating various features of the ClassTop plugin system.

## Directory Structure

```
examples/
├── python_plugins/          # Python plugin examples
│   ├── hello_world/        # Simple Python plugin
│   ├── course_statistics/  # Data analysis and frontend integration
│   └── schedule_export/    # File operations and external APIs
├── cpp_plugins/            # C++ plugin examples
│   ├── hello_world/       # Simple C++ plugin
│   ├── performance_monitor/ # Multi-threading and worker pools
│   └── simple_data_processor/ # Shared memory and zero-copy
└── README.md               # This file
```

## Python Examples

### 1. Hello World Plugin
**Directory**: `python_plugins/hello_world/`

A minimal plugin demonstrating basic structure and API usage.

**Features**:
- Plugin lifecycle hooks
- Logging
- Course data access
- Event emission
- State persistence

**Difficulty**: ⭐ Beginner

**Learn**: Plugin basics, API calls, event system

---

### 2. Course Statistics Plugin
**Directory**: `python_plugins/course_statistics/`

An advanced plugin with data analysis and frontend dashboard.

**Features**:
- Background tasks with `asyncio`
- Data aggregation and analysis
- Frontend Vue.js component
- Configuration management
- Real-time event handling

**Difficulty**: ⭐⭐⭐ Advanced

**Learn**: Background tasks, frontend integration, data processing

---

### 3. Schedule Export Plugin
**Directory**: `python_plugins/schedule_export/`

Export schedules to multiple formats using external libraries.

**Features**:
- CSV, JSON, iCal export
- External library integration (icalendar)
- File system operations
- User-configurable options
- Frontend export interface

**Difficulty**: ⭐⭐ Intermediate

**Learn**: File operations, external libraries, datetime handling

---

## C++ Examples

### 1. Hello World Plugin
**Directory**: `cpp_plugins/hello_world/`

A minimal C++ plugin demonstrating basic structure and IPC.

**Features**:
- Plugin lifecycle hooks
- API usage via C++ SDK
- Event emission
- JSON state persistence
- Cross-platform export

**Difficulty**: ⭐ Beginner

**Learn**: C++ plugin basics, SDK usage, CMake setup

---

### 2. Performance Monitor Plugin
**Directory**: `cpp_plugins/performance_monitor/`

Multi-threaded plugin for system performance monitoring.

**Features**:
- Worker thread pool (4 workers)
- Background monitoring thread
- Thread-safe task queue
- Mutex and condition variables
- Atomic operations
- Platform-specific performance data

**Difficulty**: ⭐⭐⭐ Advanced

**Learn**: Multi-threading, thread safety, worker pools

---

### 3. Simple Data Processor Plugin
**Directory**: `cpp_plugins/simple_data_processor/`

High-performance data processing with shared memory.

**Features**:
- Shared memory for zero-copy transfer
- Large data handling (1MB+)
- Background processing thread
- In-place data modification
- Performance optimization

**Difficulty**: ⭐⭐⭐ Advanced

**Learn**: Shared memory, zero-copy techniques, performance

---

## Quick Start Guide

### Python Plugins

1. **Prerequisites**:
   ```bash
   # Python 3.10+ required
   python --version
   ```

2. **Installation**:
   ```bash
   # Copy plugin to ClassTop plugins directory
   cp -r python_plugins/hello_world ~/.classtop/plugins/

   # For schedule_export, install dependencies
   pip install icalendar
   ```

3. **Enable in ClassTop**:
   - Open ClassTop
   - Navigate to Settings → Plugin Management
   - Find your plugin and click "Enable"

### C++ Plugins

1. **Prerequisites**:
   ```bash
   # CMake 3.15+
   cmake --version

   # C++17 compiler (GCC 7+, Clang 6+, MSVC 2017+)
   g++ --version
   ```

2. **Build**:
   ```bash
   cd cpp_plugins/hello_world
   mkdir build && cd build
   cmake ..
   cmake --build . --config Release
   ```

3. **Install**:
   ```bash
   # Linux/macOS
   cmake --install . --prefix ~/.classtop/plugins/cpp_hello

   # Windows
   cmake --install . --prefix %USERPROFILE%\.classtop\plugins\cpp_hello
   ```

4. **Enable in ClassTop**:
   Same as Python plugins above

---

## Learning Path

### Beginner Path
1. Start with **Python Hello World** to understand plugin basics
2. Try **C++ Hello World** to learn C++ plugin structure
3. Experiment with modifying logs and event data

### Intermediate Path
1. Study **Schedule Export** for file operations
2. Learn **Course Statistics** for background tasks
3. Understand event-driven architecture

### Advanced Path
1. Explore **Performance Monitor** for multi-threading
2. Master **Simple Data Processor** for shared memory
3. Build your own plugin combining techniques

---

## Features Comparison

| Feature | Python Hello | Course Stats | Schedule Export | C++ Hello | Performance Monitor | Data Processor |
|---------|--------------|--------------|-----------------|-----------|---------------------|----------------|
| Lifecycle hooks | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Event system | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| State persistence | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| Background tasks | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Frontend UI | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| File operations | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| External libraries | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Multi-threading | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Shared memory | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Configuration | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## Testing Your Plugins

### Verify Installation

Check logs for successful loading:
```bash
# Linux/macOS
tail -f ~/.classtop/logs/classtop.log

# Windows
Get-Content %APPDATA%\classtop\logs\classtop.log -Tail 20 -Wait
```

Look for:
```
[INFO] Plugin loaded: com.example.hello_world
[INFO] Hello World Plugin enabled
```

### Test Events

Use the browser console in ClassTop to listen for plugin events:
```javascript
// Open DevTools (Ctrl+Shift+I or Cmd+Option+I)
window.$classtop.plugins.on('hello_world_started', (data) => {
  console.log('Plugin event:', data);
});
```

### Debug Mode

Run ClassTop in debug mode for verbose logging:
```bash
# Linux/macOS
./classtop --debug

# Windows
.\ClassTop.exe --debug
```

---

## Common Issues

### Python Plugin Not Loading

**Problem**: Plugin doesn't appear in Plugin Management

**Solutions**:
1. Check `plugin.yaml` syntax: `python -c "import yaml; yaml.safe_load(open('plugin.yaml'))"`
2. Verify plugin.py has no syntax errors: `python -m py_compile plugin.py`
3. Check permissions: `chmod +r plugin.yaml plugin.py`
4. Review logs: `~/.classtop/logs/classtop.log`

### C++ Plugin Build Fails

**Problem**: CMake or compilation errors

**Solutions**:
1. Verify ClassTop SDK is installed: `find /usr/local -name "ClassTopSDK*"`
2. Install nlohmann-json: `sudo apt-get install nlohmann-json3-dev` (Linux)
3. Check compiler version: `g++ --version` (should be 7+)
4. Set SDK path: `cmake .. -DClassTopSDK_DIR=/path/to/sdk`

### Plugin Crashes ClassTop

**Problem**: ClassTop crashes when enabling plugin

**Solutions**:
1. Check for null pointer dereferences in C++ code
2. Add try-catch blocks in Python code
3. Validate all API parameters
4. Use debug build: `cmake .. -DCMAKE_BUILD_TYPE=Debug`
5. Run with debugger (gdb/lldb/Visual Studio)

---

## Extending These Examples

### Ideas for Enhancements

**Python Plugins**:
1. Add database integration (SQLite, PostgreSQL)
2. Implement REST API client for external services
3. Create notification system (desktop notifications)
4. Add i18n (internationalization) support
5. Implement plugin-to-plugin communication

**C++ Plugins**:
1. Add image processing (OpenCV integration)
2. Implement audio processing (FFmpeg)
3. Create GPU-accelerated computations (CUDA/OpenCL)
4. Add network protocol support (WebSocket, MQTT)
5. Implement custom IPC mechanisms

---

## Related Documentation

- [Python Plugin Development Guide](../docs/PYTHON_PLUGIN_GUIDE.md)
- [C++ Plugin Development Guide](../docs/CPP_PLUGIN_GUIDE.md)
- [Plugin IPC Specification](../docs/PLUGIN_IPC_SPECIFICATION.md)
- [ClassTop API Reference](../docs/PLUGIN_API_REFERENCE.md)

---

## Contributing

Found a bug or want to improve an example? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## Support

If you have questions about these examples:

1. Check the README in each plugin directory
2. Review the development guides in `docs/`
3. Search existing GitHub issues
4. Open a new issue with:
   - Plugin name and version
   - Steps to reproduce
   - Expected vs actual behavior
   - Log excerpts

---

## License

All examples are provided under the MIT License. Feel free to use them as templates for your own plugins.

---

**Last Updated**: 2025-11-01
**ClassTop Version**: 2.0.0+
**Maintainer**: ClassTop Development Team
