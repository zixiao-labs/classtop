#include "plugin.h"
#include <iostream>
#include <sstream>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

MyPlugin::MyPlugin(std::shared_ptr<classtop::PluginAPI> api)
    : classtop::Plugin(api) {
    // 构造函数
}

void MyPlugin::OnEnable() {
    api_->LogInfo("MyPlugin enabled - starting initialization");

    // 订阅事件
    api_->On("schedule_update", [this](const std::string& data) {
        OnScheduleUpdate(data);
    });

    api_->On("course_update", [this](const std::string& data) {
        api_->LogInfo("Course updated: " + data);
    });

    // 处理课程数据
    ProcessCourses();

    api_->LogInfo("MyPlugin initialization completed");
}

void MyPlugin::OnDisable() {
    api_->LogInfo("MyPlugin disabled - cleaning up");
    // 清理资源
    api_->LogInfo("MyPlugin cleanup completed");
}

std::string MyPlugin::OnSave() {
    json state;
    state["call_count"] = call_count_;
    state["version"] = "1.0.0";

    std::string state_str = state.dump();
    api_->LogInfo("Plugin state saved: " + state_str);

    return state_str;
}

void MyPlugin::OnRestore(const std::string& state) {
    try {
        json j = json::parse(state);
        call_count_ = j.value("call_count", 0);

        std::ostringstream oss;
        oss << "Plugin state restored: call_count=" << call_count_;
        api_->LogInfo(oss.str());
    } catch (const std::exception& e) {
        api_->LogError("Failed to restore state: " + std::string(e.what()));
    }
}

std::string MyPlugin::GetId() const {
    return "com.example.myplugin";
}

void MyPlugin::OnScheduleUpdate(const std::string& event_data) {
    call_count_++;

    std::ostringstream oss;
    oss << "Schedule update received (call #" << call_count_ << "): " << event_data;
    api_->LogInfo(oss.str());

    try {
        json event = json::parse(event_data);

        if (event.contains("action")) {
            std::string action = event["action"];
            api_->LogInfo("Action: " + action);

            if (action == "added") {
                api_->LogInfo("New schedule entry added");
            } else if (action == "deleted") {
                api_->LogInfo("Schedule entry deleted");
            }
        }
    } catch (const std::exception& e) {
        api_->LogError("Failed to parse event data: " + std::string(e.what()));
    }
}

void MyPlugin::ProcessCourses() {
    try {
        auto courses = api_->GetCourses();

        std::ostringstream oss;
        oss << "Total courses: " << courses.size();
        api_->LogInfo(oss.str());

        for (const auto& course : courses) {
            oss.str("");
            oss << "Course: " << course.name
                << " (Teacher: " << course.teacher
                << ", Location: " << course.location << ")";
            api_->LogInfo(oss.str());
        }
    } catch (const std::exception& e) {
        api_->LogError("Failed to process courses: " + std::string(e.what()));
    }
}

// ========== 插件导出 (跨平台) ==========

#if defined(_WIN32) || defined(_WIN64)
    #define PLUGIN_EXPORT __declspec(dllexport)
#elif defined(__GNUC__)
    #define PLUGIN_EXPORT __attribute__((visibility("default")))
#else
    #define PLUGIN_EXPORT
#endif

extern "C" {
    /**
     * @brief 创建插件实例
     */
    PLUGIN_EXPORT classtop::Plugin* CreatePlugin(std::shared_ptr<classtop::PluginAPI> api) {
        return new MyPlugin(api);
    }

    /**
     * @brief 销毁插件实例
     */
    PLUGIN_EXPORT void DestroyPlugin(classtop::Plugin* plugin) {
        delete plugin;
    }

    /**
     * @brief 获取插件元数据
     */
    PLUGIN_EXPORT const char* GetPluginMetadata() {
        static const char* metadata = R"({
            "id": "com.example.myplugin",
            "name": "My Plugin",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "A cross-platform C++ plugin for ClassTop",
            "min_classtop_version": "2.0.0"
        })";
        return metadata;
    }
}
