# Performance Monitor Plugin

An advanced C++ plugin demonstrating multi-threading, worker pools, and background monitoring.

## Features

- ✅ Multi-threaded architecture (4 worker threads + 1 monitor thread)
- ✅ Thread-safe task queue with mutex and condition variables
- ✅ Atomic operations for thread-safe counters
- ✅ Background system performance monitoring
- ✅ Cross-platform performance data collection
- ✅ Event-driven performance updates
- ✅ Proper thread lifecycle management

## Requirements

- **CMake**: 3.15 or higher
- **C++ Compiler**: GCC 7+, Clang 6+, or MSVC 2017+
- **ClassTop SDK**: 2.0.0 or higher
- **nlohmann/json**: 3.10.0 or higher
- **Platform-specific**: psapi.lib (Windows), pthread (Linux)

## Building

### Linux

```bash
mkdir build && cd build
cmake ..
cmake --build . --config Release
cmake --install . --prefix ~/.classtop/plugins/performance_monitor
```

### macOS

```bash
mkdir build && cd build
cmake ..
cmake --build . --config Release
cmake --install . --prefix ~/.classtop/plugins/performance_monitor
```

### Windows

```powershell
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release
cmake --install . --prefix %USERPROFILE%\.classtop\plugins\performance_monitor
```

## What This Plugin Does

This plugin demonstrates advanced C++ threading capabilities:

### Worker Thread Pool

- **4 Worker Threads**: Process tasks from a shared queue
- **Thread-Safe Queue**: Protected by mutex and condition variables
- **Task Processing**: Each worker waits for tasks and processes them asynchronously

### Monitor Thread

- **Background Monitoring**: Collects system performance data every 5 seconds
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Metrics Collected**:
  - Memory usage percentage
  - CPU usage (simplified)
  - System uptime
  - Tasks processed count

### Thread Lifecycle

1. **OnEnable()**: Starts worker threads and monitor thread
2. **Running**: Threads process tasks and collect metrics
3. **OnDisable()**: Gracefully stops all threads with proper cleanup

## Events

### `performance_update`
Emitted every 5 seconds with current performance metrics:

```json
{
  "plugin_id": "com.example.performance_monitor",
  "cpu_usage": 0.0,
  "memory_usage": 45.2,
  "uptime_seconds": 123456,
  "timestamp": 1730462400,
  "tasks_processed": 42
}
```

## Project Structure

```
performance_monitor/
├── CMakeLists.txt       # CMake build with platform-specific libs
├── plugin.yaml          # Plugin metadata
├── include/
│   └── plugin.h         # Plugin header with thread management
├── src/
│   └── plugin.cpp       # Implementation with platform-specific code
└── README.md            # This file
```

## Learning Points

This example demonstrates:

1. **Worker Thread Pool**:
   ```cpp
   for (int i = 0; i < 4; ++i) {
       workers_.emplace_back(&PerformanceMonitorPlugin::WorkerThread, this, i);
   }
   ```

2. **Thread-Safe Task Queue**:
   ```cpp
   std::unique_lock<std::mutex> lock(queue_mutex_);
   cv_.wait(lock, [this] {
       return !task_queue_.empty() || stop_flag_;
   });
   ```

3. **Atomic Operations**:
   ```cpp
   std::atomic<bool> stop_flag_{false};
   tasks_processed_++;  // Atomic increment
   ```

4. **Condition Variables**:
   ```cpp
   cv_.notify_one();   // Wake one worker
   cv_.notify_all();   // Wake all workers
   ```

5. **Thread Lifecycle Management**:
   ```cpp
   stop_flag_ = true;
   cv_.notify_all();
   for (auto& worker : workers_) {
       if (worker.joinable()) {
           worker.join();
       }
   }
   ```

6. **Platform-Specific Code**:
   ```cpp
   #ifdef _WIN32
       // Windows performance collection
   #elif defined(__APPLE__)
       // macOS performance collection
   #else
       // Linux performance collection
   #endif
   ```

## Advanced Techniques

### RAII Thread Management

```cpp
PerformanceMonitorPlugin::~PerformanceMonitorPlugin() {
    if (!stop_flag_) {
        OnDisable();  // Ensure cleanup
    }
}
```

### Thread-Safe Task Addition

```cpp
void PerformanceMonitorPlugin::AddTask(const std::string& type, const std::string& data) {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    task_queue_.push({type, data});
    cv_.notify_one();
}
```

### Graceful Shutdown

```cpp
void OnDisable() {
    stop_flag_ = true;      // Signal stop
    cv_.notify_all();        // Wake all threads

    for (auto& worker : workers_) {
        if (worker.joinable()) {
            worker.join();   // Wait for completion
        }
    }
}
```

## Performance Considerations

### Memory Usage

- Each thread has its own stack (typically 1-8 MB)
- Task queue grows dynamically based on load
- Monitor thread has minimal overhead

### CPU Usage

- Worker threads sleep when idle (no busy-waiting)
- Condition variables ensure efficient wake-up
- Monitor thread sleeps between collections

### Thread Count

Current configuration uses 5 threads (4 workers + 1 monitor). Adjust based on:
- Available CPU cores
- Task complexity
- System load

## Debugging Multi-Threaded Code

### Linux (GDB)

```bash
gdb /path/to/classtop
(gdb) thread apply all bt  # Backtrace all threads
(gdb) info threads          # List all threads
(gdb) thread 2              # Switch to thread 2
```

### macOS (LLDB)

```bash
lldb /path/to/ClassTop
(lldb) thread list          # List all threads
(lldb) thread backtrace all # Backtrace all threads
(lldb) thread select 2      # Switch to thread 2
```

### Common Threading Issues

1. **Deadlocks**: Use lock hierarchies, avoid nested locks
2. **Race Conditions**: Use atomic operations, mutex protection
3. **Thread Leaks**: Always join or detach threads
4. **Data Races**: Use thread-safe data structures

## Extending This Plugin

Ideas for enhancements:

1. **Dynamic Thread Pool**: Adjust worker count based on load
2. **Task Priorities**: Priority queue for urgent tasks
3. **CPU Usage**: Accurate CPU usage calculation
4. **Disk I/O**: Monitor disk read/write speeds
5. **Network Stats**: Track network bandwidth
6. **Thread Pool Library**: Use C++11 `std::async` or boost::asio

## Related Documentation

- [C++ Plugin Development Guide](../../../docs/CPP_PLUGIN_GUIDE.md)
- [Plugin IPC Specification](../../../docs/PLUGIN_IPC_SPECIFICATION.md)
- [C++ Threading Reference](https://en.cppreference.com/w/cpp/thread)
- [C++ Concurrency in Action](https://www.manning.com/books/c-plus-plus-concurrency-in-action)
