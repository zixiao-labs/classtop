#include "plugin.h"
#include <nlohmann/json.hpp>
#include <sstream>
#include <chrono>
#include <ctime>

#ifdef _WIN32
    #include <windows.h>
    #include <psapi.h>
#elif defined(__APPLE__)
    #include <sys/sysctl.h>
    #include <mach/mach.h>
#else
    #include <sys/types.h>
    #include <sys/sysinfo.h>
    #include <unistd.h>
#endif

using json = nlohmann::json;

PerformanceMonitorPlugin::PerformanceMonitorPlugin(std::shared_ptr<classtop::PluginAPI> api)
    : classtop::Plugin(api) {
    // Constructor
}

PerformanceMonitorPlugin::~PerformanceMonitorPlugin() {
    // Ensure threads are stopped
    if (!stop_flag_) {
        OnDisable();
    }
}

void PerformanceMonitorPlugin::OnEnable() {
    api_->LogInfo("Performance Monitor Plugin enabled");
    api_->LogInfo("Starting worker threads and monitoring...");

    stop_flag_ = false;

    // Start worker threads (4 workers)
    for (int i = 0; i < 4; ++i) {
        workers_.emplace_back(&PerformanceMonitorPlugin::WorkerThread, this, i);
    }

    // Start monitoring thread
    monitor_thread_ = std::thread(&PerformanceMonitorPlugin::MonitorThread, this);

    api_->LogInfo("Performance Monitor ready (4 workers + 1 monitor thread)");

    // Add initial test task
    AddTask("initialization", "{}");
}

void PerformanceMonitorPlugin::OnDisable() {
    api_->LogInfo("Stopping Performance Monitor...");

    // Stop all threads
    stop_flag_ = true;
    cv_.notify_all();

    // Wait for worker threads
    for (auto& worker : workers_) {
        if (worker.joinable()) {
            worker.join();
        }
    }
    workers_.clear();

    // Wait for monitor thread
    if (monitor_thread_.joinable()) {
        monitor_thread_.join();
    }

    std::ostringstream oss;
    oss << "Performance Monitor disabled. Total tasks processed: " << tasks_processed_;
    api_->LogInfo(oss.str());
}

std::string PerformanceMonitorPlugin::OnSave() {
    json state;
    state["tasks_processed"] = tasks_processed_;
    state["monitoring_interval_ms"] = monitoring_interval_ms_;
    state["last_cpu_usage"] = last_performance_.cpu_usage;
    state["last_memory_usage"] = last_performance_.memory_usage;
    state["version"] = "1.0.0";

    return state.dump();
}

void PerformanceMonitorPlugin::OnRestore(const std::string& state) {
    try {
        json j = json::parse(state);
        tasks_processed_ = j.value("tasks_processed", 0);
        monitoring_interval_ms_ = j.value("monitoring_interval_ms", 5000);
        last_performance_.cpu_usage = j.value("last_cpu_usage", 0.0);
        last_performance_.memory_usage = j.value("last_memory_usage", 0.0);

        api_->LogInfo("State restored successfully");
    } catch (const std::exception& e) {
        api_->LogError("Failed to restore state: " + std::string(e.what()));
    }
}

std::string PerformanceMonitorPlugin::GetId() const {
    return "com.example.performance_monitor";
}

void PerformanceMonitorPlugin::WorkerThread(int thread_id) {
    std::ostringstream oss;
    oss << "Worker thread " << thread_id << " started";
    api_->LogInfo(oss.str());

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
            Task task = task_queue_.front();
            task_queue_.pop();
            lock.unlock();  // Release lock before processing

            // Process task
            ProcessTask(task);

            tasks_processed_++;
        }
    }

    oss.str("");
    oss << "Worker thread " << thread_id << " stopped";
    api_->LogInfo(oss.str());
}

void PerformanceMonitorPlugin::MonitorThread() {
    api_->LogInfo("Monitor thread started");

    while (!stop_flag_) {
        // Collect performance data
        PerformanceData data = CollectPerformanceData();
        last_performance_ = data;

        // Emit performance update event
        EmitPerformanceUpdate(data);

        // Sleep for monitoring interval
        std::this_thread::sleep_for(std::chrono::milliseconds(monitoring_interval_ms_));
    }

    api_->LogInfo("Monitor thread stopped");
}

PerformanceMonitorPlugin::PerformanceData PerformanceMonitorPlugin::CollectPerformanceData() {
    PerformanceData data;
    data.timestamp = std::time(nullptr);

#ifdef _WIN32
    // Windows performance collection
    MEMORYSTATUSEX memInfo;
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    if (GlobalMemoryStatusEx(&memInfo)) {
        data.memory_usage = static_cast<double>(memInfo.dwMemoryLoad);
    }

    // Simplified CPU usage (would need more complex logic for accurate CPU usage)
    data.cpu_usage = 0.0;  // Placeholder

#elif defined(__APPLE__)
    // macOS performance collection
    vm_statistics64_data_t vmStats;
    mach_msg_type_number_t infoCount = HOST_VM_INFO64_COUNT;
    kern_return_t kernReturn = host_statistics64(mach_host_self(),
                                                   HOST_VM_INFO64,
                                                   (host_info64_t)&vmStats,
                                                   &infoCount);

    if (kernReturn == KERN_SUCCESS) {
        uint64_t used_memory = (vmStats.active_count + vmStats.wire_count) * vm_page_size;
        uint64_t total_memory = vmStats.free_count + vmStats.active_count +
                                vmStats.inactive_count + vmStats.wire_count;
        total_memory *= vm_page_size;
        data.memory_usage = (static_cast<double>(used_memory) / total_memory) * 100.0;
    }

#else
    // Linux performance collection
    struct sysinfo sys_info;
    if (sysinfo(&sys_info) == 0) {
        data.uptime_seconds = sys_info.uptime;

        uint64_t total_ram = sys_info.totalram;
        uint64_t free_ram = sys_info.freeram;
        uint64_t used_ram = total_ram - free_ram;

        data.memory_usage = (static_cast<double>(used_ram) / total_ram) * 100.0;
    }

    // Simplified CPU usage
    data.cpu_usage = 0.0;  // Placeholder
#endif

    return data;
}

void PerformanceMonitorPlugin::ProcessTask(const Task& task) {
    std::ostringstream oss;
    oss << "Processing task: type=" << task.type << ", data=" << task.data;
    api_->LogInfo(oss.str());

    // Simulate task processing
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
}

void PerformanceMonitorPlugin::EmitPerformanceUpdate(const PerformanceData& data) {
    json event_data;
    event_data["plugin_id"] = GetId();
    event_data["cpu_usage"] = data.cpu_usage;
    event_data["memory_usage"] = data.memory_usage;
    event_data["uptime_seconds"] = data.uptime_seconds;
    event_data["timestamp"] = data.timestamp;
    event_data["tasks_processed"] = tasks_processed_.load();

    api_->EmitEvent("performance_update", event_data.dump());

    std::ostringstream oss;
    oss << "Performance: Memory=" << std::fixed << std::setprecision(1)
        << data.memory_usage << "%, Tasks=" << tasks_processed_;
    api_->LogInfo(oss.str());
}

void PerformanceMonitorPlugin::AddTask(const std::string& type, const std::string& data) {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    task_queue_.push({type, data});
    cv_.notify_one();  // Notify one waiting worker
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
        return new PerformanceMonitorPlugin(api);
    }

    PLUGIN_EXPORT void DestroyPlugin(classtop::Plugin* plugin) {
        delete plugin;
    }

    PLUGIN_EXPORT const char* GetPluginMetadata() {
        static const char* metadata = R"({
            "id": "com.example.performance_monitor",
            "name": "Performance Monitor Plugin",
            "version": "1.0.0",
            "author": "ClassTop Team",
            "description": "Monitors system performance using multi-threading",
            "min_classtop_version": "2.0.0"
        })";
        return metadata;
    }
}
