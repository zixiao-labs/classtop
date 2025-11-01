#include "plugin.h"
#include <nlohmann/json.hpp>
#include <sstream>
#include <iostream>

using json = nlohmann::json;

HelloWorldPlugin::HelloWorldPlugin(std::shared_ptr<classtop::PluginAPI> api)
    : classtop::Plugin(api) {
    // Constructor - initialize member variables if needed
}

void HelloWorldPlugin::OnEnable() {
    api_->LogInfo("==================================================");
    api_->LogInfo("C++ Hello World Plugin Enabled!");
    api_->LogInfo("==================================================");

    // Log plugin info
    api_->LogInfo("Plugin ID: " + GetId());
    api_->LogInfo("Language: C++17");
    api_->LogInfo("Compiled: " + std::string(__DATE__) + " " + std::string(__TIME__));

    // Display course information
    DisplayCourses();

    // Send welcome event
    SendWelcomeEvent();

    api_->LogInfo("C++ Hello World Plugin ready!");
}

void HelloWorldPlugin::OnDisable() {
    api_->LogInfo("==================================================");
    api_->LogInfo("C++ Hello World Plugin Disabled!");

    std::ostringstream oss;
    oss << "Total messages logged: " << message_count_;
    api_->LogInfo(oss.str());

    api_->LogInfo("==================================================");

    // Send goodbye event
    json event_data;
    event_data["plugin_id"] = GetId();
    event_data["message"] = "Goodbye from C++ plugin!";
    event_data["message_count"] = message_count_;

    api_->EmitEvent("cpp_hello_stopped", event_data.dump());
}

std::string HelloWorldPlugin::OnSave() {
    json state;
    state["message_count"] = message_count_;
    state["version"] = "1.0.0";

    std::string state_str = state.dump();
    api_->LogInfo("Plugin state saved: " + state_str);

    return state_str;
}

void HelloWorldPlugin::OnRestore(const std::string& state) {
    try {
        json j = json::parse(state);
        message_count_ = j.value("message_count", 0);

        std::ostringstream oss;
        oss << "Plugin state restored: message_count=" << message_count_;
        api_->LogInfo(oss.str());
    } catch (const std::exception& e) {
        api_->LogError("Failed to restore state: " + std::string(e.what()));
    }
}

std::string HelloWorldPlugin::GetId() const {
    return "com.example.cpp_hello";
}

void HelloWorldPlugin::DisplayCourses() {
    try {
        auto courses = api_->GetCourses();

        std::ostringstream oss;
        oss << "Found " << courses.size() << " courses in the system";
        api_->LogInfo(oss.str());

        if (!courses.empty()) {
            api_->LogInfo("Course list:");
            int idx = 1;
            for (const auto& course : courses) {
                oss.str("");
                oss << "  " << idx << ". " << course.name
                    << " - " << course.teacher
                    << " (" << course.location << ")";
                api_->LogInfo(oss.str());
                idx++;
                message_count_++;
            }
        }
    } catch (const std::exception& e) {
        api_->LogError("Failed to fetch courses: " + std::string(e.what()));
    }
}

void HelloWorldPlugin::SendWelcomeEvent() {
    json event_data;
    event_data["plugin_id"] = GetId();
    event_data["message"] = "Hello from C++ plugin!";
    event_data["language"] = "C++17";
    event_data["timestamp"] = std::time(nullptr);

    api_->EmitEvent("cpp_hello_started", event_data.dump());
    api_->LogInfo("Welcome event sent");
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
    /**
     * @brief Create plugin instance
     */
    PLUGIN_EXPORT classtop::Plugin* CreatePlugin(std::shared_ptr<classtop::PluginAPI> api) {
        return new HelloWorldPlugin(api);
    }

    /**
     * @brief Destroy plugin instance
     */
    PLUGIN_EXPORT void DestroyPlugin(classtop::Plugin* plugin) {
        delete plugin;
    }

    /**
     * @brief Get plugin metadata
     */
    PLUGIN_EXPORT const char* GetPluginMetadata() {
        static const char* metadata = R"({
            "id": "com.example.cpp_hello",
            "name": "C++ Hello World Plugin",
            "version": "1.0.0",
            "author": "ClassTop Team",
            "description": "A simple C++ plugin demonstrating basic structure",
            "min_classtop_version": "2.0.0"
        })";
        return metadata;
    }
}
