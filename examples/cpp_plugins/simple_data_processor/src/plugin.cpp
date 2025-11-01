#include "plugin.h"
#include <nlohmann/json.hpp>
#include <sstream>
#include <cstring>
#include <algorithm>

using json = nlohmann::json;

SimpleDataProcessorPlugin::SimpleDataProcessorPlugin(std::shared_ptr<classtop::PluginAPI> api)
    : classtop::Plugin(api) {
    // Constructor
}

SimpleDataProcessorPlugin::~SimpleDataProcessorPlugin() {
    if (!stop_flag_) {
        OnDisable();
    }
}

void SimpleDataProcessorPlugin::OnEnable() {
    api_->LogInfo("Simple Data Processor Plugin enabled");

    stop_flag_ = false;

    // Start worker thread
    worker_ = std::thread(&SimpleDataProcessorPlugin::WorkerThread, this);

    api_->LogInfo("Data processor worker thread started");

    // Demonstrate shared memory by processing demo data
    ProcessDataInSharedMemory();
}

void SimpleDataProcessorPlugin::OnDisable() {
    api_->LogInfo("Stopping Simple Data Processor...");

    // Stop worker thread
    stop_flag_ = true;
    cv_.notify_all();

    if (worker_.joinable()) {
        worker_.join();
    }

    std::ostringstream oss;
    oss << "Data processor disabled. Processed " << processed_count_ << " data blocks";
    api_->LogInfo(oss.str());
}

std::string SimpleDataProcessorPlugin::OnSave() {
    json state;
    state["processed_count"] = processed_count_;
    state["version"] = "1.0.0";
    return state.dump();
}

void SimpleDataProcessorPlugin::OnRestore(const std::string& state) {
    try {
        json j = json::parse(state);
        processed_count_ = j.value("processed_count", 0);

        std::ostringstream oss;
        oss << "State restored: processed_count=" << processed_count_;
        api_->LogInfo(oss.str());
    } catch (const std::exception& e) {
        api_->LogError("Failed to restore state: " + std::string(e.what()));
    }
}

std::string SimpleDataProcessorPlugin::GetId() const {
    return "com.example.simple_data_processor";
}

void SimpleDataProcessorPlugin::WorkerThread() {
    api_->LogInfo("Worker thread running");

    while (!stop_flag_) {
        std::unique_lock<std::mutex> lock(queue_mutex_);

        // Wait for task or stop signal
        cv_.wait(lock, [this] {
            return !task_queue_.empty() || stop_flag_;
        });

        if (stop_flag_) {
            break;
        }

        if (!task_queue_.empty()) {
            ProcessingTask task = task_queue_.front();
            task_queue_.pop();
            lock.unlock();

            // Process the data
            ProcessData(task.data_id, task.data_size);

            processed_count_++;
        }
    }

    api_->LogInfo("Worker thread stopped");
}

void SimpleDataProcessorPlugin::ProcessData(const std::string& data_id, size_t size) {
    try {
        api_->LogInfo("Processing data: " + data_id);

        // Open shared memory
        auto shm = classtop::SharedMemory::Open(data_id);
        if (!shm) {
            api_->LogError("Failed to open shared memory: " + data_id);
            return;
        }

        // Get buffer and size
        uint8_t* data = static_cast<uint8_t*>(shm->GetBuffer());
        size_t actual_size = shm->GetSize();

        if (actual_size != size) {
            std::ostringstream oss;
            oss << "Size mismatch: expected " << size << ", got " << actual_size;
            api_->LogWarning(oss.str());
        }

        // Process data (example: calculate checksum)
        uint32_t checksum = 0;
        for (size_t i = 0; i < actual_size; ++i) {
            checksum += data[i];
        }

        // Example processing: reverse bytes (in-place)
        std::reverse(data, data + actual_size);

        // Emit processing complete event
        json result;
        result["data_id"] = data_id;
        result["size"] = actual_size;
        result["checksum"] = checksum;
        result["processed_count"] = processed_count_;

        api_->EmitEvent("data_processed", result.dump());

        std::ostringstream oss;
        oss << "Processed " << actual_size << " bytes, checksum=" << checksum;
        api_->LogInfo(oss.str());

    } catch (const std::exception& e) {
        api_->LogError("Error processing data: " + std::string(e.what()));
    }
}

void SimpleDataProcessorPlugin::ProcessDataInSharedMemory() {
    try {
        api_->LogInfo("Demonstrating shared memory usage...");

        // Create demo data (1 MB)
        const size_t data_size = 1024 * 1024;
        std::string memory_name = "demo_data";

        // Create shared memory
        auto shm = classtop::SharedMemory::Create(memory_name, data_size);
        if (!shm) {
            api_->LogError("Failed to create shared memory");
            return;
        }

        // Fill with demo data
        uint8_t* buffer = static_cast<uint8_t*>(shm->GetBuffer());
        for (size_t i = 0; i < data_size; ++i) {
            buffer[i] = static_cast<uint8_t>(i % 256);
        }

        api_->LogInfo("Created 1MB demo data in shared memory");

        // Notify ClassTop that data is ready
        api_->NotifySharedMemoryReady(memory_name, data_size);

        // Add task to process this data
        AddTask(memory_name, data_size);

    } catch (const std::exception& e) {
        api_->LogError("Failed to demonstrate shared memory: " + std::string(e.what()));
    }
}

void SimpleDataProcessorPlugin::AddTask(const std::string& data_id, size_t size) {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    task_queue_.push({data_id, size});
    cv_.notify_one();
}

// ========== Plugin Export Functions ==========

#if defined(_WIN32) || defined(_WIN64)
    #define PLUGIN_EXPORT __declspec(dllexport)
#elif defined(__GNUC__)
    #define PLUGIN_EXPORT __attribute__((visibility("default")))
#else
    #define PLUGIN_EXPORT
#endif

extern "C" {
    PLUGIN_EXPORT classtop::Plugin* CreatePlugin(std::shared_ptr<classtop::PluginAPI> api) {
        return new SimpleDataProcessorPlugin(api);
    }

    PLUGIN_EXPORT void DestroyPlugin(classtop::Plugin* plugin) {
        delete plugin;
    }

    PLUGIN_EXPORT const char* GetPluginMetadata() {
        static const char* metadata = R"({
            "id": "com.example.simple_data_processor",
            "name": "Simple Data Processor",
            "version": "1.0.0",
            "author": "ClassTop Team",
            "description": "Demonstrates shared memory for high-performance data processing",
            "min_classtop_version": "2.0.0"
        })";
        return metadata;
    }
}
