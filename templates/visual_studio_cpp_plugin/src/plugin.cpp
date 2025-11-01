#include "plugin.h"
#include <iostream>
#include <sstream>
#include <nlohmann/json.hpp>  // 需要安装 nlohmann/json 库

using json = nlohmann::json;

MyPlugin::MyPlugin(std::shared_ptr<classtop::PluginAPI> api)
    : classtop::Plugin(api) {
    // 构造函数初始化
}

void MyPlugin::OnEnable() {
    api_->LogInfo("MyPlugin enabled - starting initialization");

    // 订阅日程更新事件
    api_->On("schedule_update", [this](const std::string& data) {
        OnScheduleUpdate(data);
    });

    // 订阅课程更新事件
    api_->On("course_update", [this](const std::string& data) {
        api_->LogInfo("Course updated: " + data);
    });

    // 示例:获取并处理课程数据
    ProcessCourses();

    api_->LogInfo("MyPlugin initialization completed");
}

void MyPlugin::OnDisable() {
    api_->LogInfo("MyPlugin disabled - cleaning up");

    // 注意:事件监听器会在插件卸载时自动清理
    // 如果有其他资源需要清理,在此处添加

    api_->LogInfo("MyPlugin cleanup completed");
}

std::string MyPlugin::OnSave() {
    // 保存插件状态用于热重载
    json state;
    state["call_count"] = call_count_;
    state["version"] = "1.0.0";

    std::string state_str = state.dump();
    api_->LogInfo("Plugin state saved: " + state_str);

    return state_str;
}

void MyPlugin::OnRestore(const std::string& state) {
    // 从保存的状态恢复
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
    return "com.example.myplugin";  // 修改为你的插件 ID
}

void MyPlugin::OnScheduleUpdate(const std::string& event_data) {
    call_count_++;

    std::ostringstream oss;
    oss << "Schedule update received (call #" << call_count_ << "): " << event_data;
    api_->LogInfo(oss.str());

    // 解析事件数据
    try {
        json event = json::parse(event_data);

        if (event.contains("action")) {
            std::string action = event["action"];
            api_->LogInfo("Action: " + action);

            if (action == "added") {
                // 处理添加事件
                api_->LogInfo("New schedule entry added");
            } else if (action == "deleted") {
                // 处理删除事件
                api_->LogInfo("Schedule entry deleted");
            }
        }
    } catch (const std::exception& e) {
        api_->LogError("Failed to parse event data: " + std::string(e.what()));
    }
}

void MyPlugin::ProcessCourses() {
    try {
        // 获取所有课程
        auto courses = api_->GetCourses();

        std::ostringstream oss;
        oss << "Total courses: " << courses.size();
        api_->LogInfo(oss.str());

        // 遍历课程
        for (const auto& course : courses) {
            oss.str("");
            oss << "Course: " << course.name
                << " (Teacher: " << course.teacher
                << ", Location: " << course.location << ")";
            api_->LogInfo(oss.str());
        }

        // 示例:添加新课程
        // int course_id = api_->AddCourse("Math", "Dr. Smith", "Room 101", "#FF5733");
        // api_->LogInfo("Added new course with ID: " + std::to_string(course_id));

    } catch (const std::exception& e) {
        api_->LogError("Failed to process courses: " + std::string(e.what()));
    }
}

// ========== 插件导出 ==========

#ifdef _WIN32
#define PLUGIN_EXPORT __declspec(dllexport)
#else
#define PLUGIN_EXPORT __attribute__((visibility("default")))
#endif

extern "C" {
    /**
     * @brief 插件工厂函数
     *
     * ClassTop 主应用调用此函数创建插件实例
     *
     * @param api 插件 API 接口
     * @return 插件实例指针
     */
    PLUGIN_EXPORT classtop::Plugin* CreatePlugin(std::shared_ptr<classtop::PluginAPI> api) {
        return new MyPlugin(api);
    }

    /**
     * @brief 销毁插件实例
     *
     * @param plugin 插件实例指针
     */
    PLUGIN_EXPORT void DestroyPlugin(classtop::Plugin* plugin) {
        delete plugin;
    }

    /**
     * @brief 获取插件元数据
     *
     * @return JSON 格式的元数据字符串
     */
    PLUGIN_EXPORT const char* GetPluginMetadata() {
        static const char* metadata = R"({
            "id": "com.example.myplugin",
            "name": "My Plugin",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "A sample C++ plugin for ClassTop",
            "min_classtop_version": "2.0.0"
        })";
        return metadata;
    }
}
