#pragma once

#include "classtop/plugin.h"
#include <string>
#include <memory>
#include <thread>
#include <atomic>
#include <mutex>
#include <queue>
#include <condition_variable>

/**
 * @brief Performance Monitor Plugin
 *
 * Demonstrates:
 * - Multi-threading with worker threads
 * - Thread-safe task queue
 * - Atomic operations
 * - Condition variables
 * - Background monitoring
 * - Thread lifecycle management
 */
class PerformanceMonitorPlugin : public classtop::Plugin {
public:
    explicit PerformanceMonitorPlugin(std::shared_ptr<classtop::PluginAPI> api);
    ~PerformanceMonitorPlugin() override;

    // Lifecycle hooks
    void OnEnable() override;
    void OnDisable() override;
    std::string OnSave() override;
    void OnRestore(const std::string& state) override;

    // Plugin identification
    std::string GetId() const override;

private:
    // Performance monitoring
    struct PerformanceData {
        double cpu_usage = 0.0;
        double memory_usage = 0.0;
        int64_t uptime_seconds = 0;
        std::time_t timestamp = 0;
    };

    // Task structure
    struct Task {
        std::string type;
        std::string data;
    };

    // Worker thread functions
    void WorkerThread(int thread_id);
    void MonitorThread();

    // Performance collection
    PerformanceData CollectPerformanceData();
    void ProcessTask(const Task& task);
    void EmitPerformanceUpdate(const PerformanceData& data);

    // Task queue operations
    void AddTask(const std::string& type, const std::string& data);

    // Worker threads
    std::vector<std::thread> workers_;
    std::thread monitor_thread_;

    // Synchronization
    std::atomic<bool> stop_flag_{false};
    std::mutex queue_mutex_;
    std::condition_variable cv_;

    // Task queue
    std::queue<Task> task_queue_;

    // State
    int tasks_processed_ = 0;
    int monitoring_interval_ms_ = 5000;  // 5 seconds
    PerformanceData last_performance_;
};
