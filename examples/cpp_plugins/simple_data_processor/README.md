# Simple Data Processor Plugin

A C++ plugin demonstrating shared memory for high-performance, zero-copy data transfer.

## Features

- ✅ Shared memory for large data transfers
- ✅ Zero-copy data processing
- ✅ Background worker thread
- ✅ Task queue for async processing
- ✅ Demonstrates 1MB+ data handling
- ✅ In-place data modification

## Requirements

- **CMake**: 3.15 or higher
- **C++ Compiler**: GCC 7+, Clang 6+, or MSVC 2017+
- **ClassTop SDK**: 2.0.0 or higher (with SharedMemory support)
- **nlohmann/json**: 3.10.0 or higher

## Building

### Linux

```bash
mkdir build && cd build
cmake ..
cmake --build . --config Release
cmake --install . --prefix ~/.classtop/plugins/simple_data_processor
```

### macOS

```bash
mkdir build && cd build
cmake ..
cmake --build . --config Release
cmake --install . --prefix ~/.classtop/plugins/simple_data_processor
```

### Windows

```powershell
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release
cmake --install . --prefix %USERPROFILE%\.classtop\plugins\simple_data_processor
```

## What This Plugin Does

This plugin demonstrates how to use shared memory for efficient large data transfer:

### Shared Memory Workflow

1. **Create Shared Memory**:
   ```cpp
   auto shm = classtop::SharedMemory::Create("demo_data", 1024*1024);
   ```

2. **Write Data** (zero-copy):
   ```cpp
   uint8_t* buffer = static_cast<uint8_t*>(shm->GetBuffer());
   // Fill buffer directly - no memcpy needed!
   ```

3. **Notify ClassTop**:
   ```cpp
   api_->NotifySharedMemoryReady("demo_data", size);
   ```

4. **Process Data** in background thread:
   ```cpp
   auto shm = classtop::SharedMemory::Open("demo_data");
   uint8_t* data = static_cast<uint8_t*>(shm->GetBuffer());
   // Process data in-place
   ```

### Demo Functionality

When enabled, the plugin:
1. Creates 1MB of demo data in shared memory
2. Notifies the main application
3. Processes the data in a background thread
4. Calculates checksum and reverses bytes
5. Emits `data_processed` event with results

## Events

### `data_processed`
Emitted after processing each data block:

```json
{
  "data_id": "demo_data",
  "size": 1048576,
  "checksum": 33423360,
  "processed_count": 1
}
```

## Project Structure

```
simple_data_processor/
├── CMakeLists.txt       # CMake build configuration
├── plugin.yaml          # Plugin metadata
├── include/
│   └── plugin.h         # Plugin header with shared memory
├── src/
│   └── plugin.cpp       # Implementation with zero-copy processing
└── README.md            # This file
```

## Learning Points

This example demonstrates:

### 1. Creating Shared Memory

```cpp
auto shm = classtop::SharedMemory::Create("my_data", size);
if (!shm) {
    // Handle error
    return;
}
```

### 2. Writing Data (Zero-Copy)

```cpp
uint8_t* buffer = static_cast<uint8_t*>(shm->GetBuffer());
size_t size = shm->GetSize();

// Write data directly to shared memory
for (size_t i = 0; i < size; ++i) {
    buffer[i] = static_cast<uint8_t>(i % 256);
}
```

### 3. Notifying Main Application

```cpp
api_->NotifySharedMemoryReady("my_data", size);
```

### 4. Reading from Shared Memory

```cpp
auto shm = classtop::SharedMemory::Open("my_data");
if (!shm) {
    // Handle error
    return;
}

uint8_t* data = static_cast<uint8_t*>(shm->GetBuffer());
size_t size = shm->GetSize();

// Process data
ProcessBuffer(data, size);
```

### 5. In-Place Data Modification

```cpp
// Reverse bytes in-place (no extra allocation)
std::reverse(data, data + size);
```

## Performance Benefits

### Traditional IPC (with copying)
```
Source → Serialize → Copy to IPC buffer → Deserialize → Destination
```
**Cost**: 2x memory, 2x copy operations, serialization overhead

### Shared Memory (zero-copy)
```
Source → Write to shared buffer → Destination reads directly
```
**Cost**: 1x memory, no copies, no serialization

### Example Performance Gains

For a 10MB image:
- **Traditional**: ~40ms (2x copy + serialize/deserialize)
- **Shared Memory**: ~2ms (direct memory access)

**Speedup**: ~20x faster!

## Use Cases

Shared memory is ideal for:

1. **Image Processing**: Photos, screenshots, video frames
2. **Large Datasets**: ML models, databases, CSV files
3. **Real-time Data**: Audio streams, sensor data
4. **Binary Files**: PDFs, executables, archives
5. **Buffers**: Any data > 1KB benefits from zero-copy

## Advanced Techniques

### Memory-Mapped Files

```cpp
// Create shared memory backed by a file
auto shm = classtop::SharedMemory::CreateMapped("data.bin", size);

// Changes persist to disk
uint8_t* buffer = static_cast<uint8_t*>(shm->GetBuffer());
ModifyData(buffer, size);

// Automatically synced when shm is destroyed
```

### Multiple Readers

```cpp
// Writer creates shared memory
auto shm_write = classtop::SharedMemory::Create("shared_data", size);

// Multiple readers can open simultaneously
auto shm_read1 = classtop::SharedMemory::Open("shared_data");
auto shm_read2 = classtop::SharedMemory::Open("shared_data");
auto shm_read3 = classtop::SharedMemory::Open("shared_data");

// All readers see the same data (no copying!)
```

### Synchronization

```cpp
// Use atomic flags for synchronization
struct SharedData {
    std::atomic<bool> ready{false};
    uint8_t data[1024*1024];
};

// Writer
auto shm = classtop::SharedMemory::Create("sync_data", sizeof(SharedData));
auto* shared = static_cast<SharedData*>(shm->GetBuffer());
FillData(shared->data);
shared->ready.store(true);  // Signal ready

// Reader
auto shm = classtop::SharedMemory::Open("sync_data");
auto* shared = static_cast<SharedData*>(shm->GetBuffer());
while (!shared->ready.load()) {
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
}
ProcessData(shared->data);
```

## Safety Considerations

### Memory Safety

1. **Size Validation**: Always check `GetSize()` before accessing
2. **Bounds Checking**: Validate indices before array access
3. **Type Safety**: Use `static_cast` carefully
4. **Lifetime**: Ensure shared memory outlives all users

### Concurrency

1. **No Built-in Locking**: Shared memory doesn't provide mutexes
2. **Use Atomics**: For simple flags and counters
3. **Use Named Mutexes**: For complex synchronization
4. **Reader-Writer**: Consider multiple readers, single writer pattern

## Troubleshooting

### Shared Memory Creation Fails

**Cause**: Name collision or insufficient permissions

**Solution**:
```cpp
// Use unique names
std::string unique_name = "data_" + std::to_string(std::time(nullptr));
auto shm = classtop::SharedMemory::Create(unique_name, size);
```

### Size Mismatch

**Cause**: Writer and reader use different sizes

**Solution**:
```cpp
auto shm = classtop::SharedMemory::Open("data");
size_t actual_size = shm->GetSize();
// Always use actual_size, not assumed size
```

### Data Corruption

**Cause**: Concurrent writes without synchronization

**Solution**: Use atomic operations or mutexes:
```cpp
// Option 1: Atomic flag
std::atomic<bool> writing{false};

// Option 2: Named mutex
#include <boost/interprocess/sync/named_mutex.hpp>
boost::interprocess::named_mutex mutex(boost::interprocess::open_or_create, "my_mutex");
```

## Extending This Plugin

Ideas for enhancements:

1. **Image Filters**: Apply blur, sharpen, grayscale on images
2. **Video Processing**: Process video frames in real-time
3. **Audio DSP**: Apply audio effects (reverb, EQ, compression)
4. **Data Compression**: Compress/decompress large files
5. **Encryption**: Encrypt data before transferring
6. **Parallel Processing**: Split buffer across multiple threads

## Related Documentation

- [C++ Plugin Development Guide](../../../docs/CPP_PLUGIN_GUIDE.md)
- [Plugin IPC Specification](../../../docs/PLUGIN_IPC_SPECIFICATION.md)
- [Boost.Interprocess](https://www.boost.org/doc/libs/release/doc/html/interprocess.html)
- [POSIX Shared Memory](https://man7.org/linux/man-pages/man7/shm_overview.7.html)
