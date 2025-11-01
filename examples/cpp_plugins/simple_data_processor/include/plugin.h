#pragma once

#include "classtop/plugin.h"
#include "classtop/shared_memory.h"
#include <string>
#include <memory>
#include <thread>
#include <atomic>
#include <queue>
#include <mutex>
#include <condition_variable>

/**
 * @brief Simple Data Processor Plugin
 *
 * Demonstrates:
 * - Shared memory for zero-copy data transfer
 * - Background data processing thread
 * - Large data handling (e.g., images, binary data)
 * - Memory-efficient operations
 */
class SimpleDataProcessorPlugin : public classtop::Plugin {
public:
    explicit SimpleDataProcessorPlugin(std::shared_ptr<classtop::PluginAPI> api);
    ~SimpleDataProcessorPlugin() override;

    // Lifecycle hooks
    void OnEnable() override;
    void OnDisable() override;
    std::string OnSave() override;
    void OnRestore(const std::string& state) override;

    // Plugin identification
    std::string GetId() const override;

private:
    // Data processing task
    struct ProcessingTask {
        std::string data_id;
        size_t data_size;
    };

    // Worker thread
    void WorkerThread();

    // Data processing
    void ProcessData(const std::string& data_id, size_t size);
    void ProcessDataInSharedMemory();

    // Task queue operations
    void AddTask(const std::string& data_id, size_t size);

    // Worker thread
    std::thread worker_;
    std::atomic<bool> stop_flag_{false};

    // Task queue synchronization
    std::queue<ProcessingTask> task_queue_;
    std::mutex queue_mutex_;
    std::condition_variable cv_;

    // State
    int processed_count_ = 0;
};
