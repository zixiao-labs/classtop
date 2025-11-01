#pragma once

#include "classtop/plugin.h"
#include <string>
#include <memory>

/**
 * @brief Simple Hello World plugin for ClassTop
 *
 * Demonstrates:
 * - Basic plugin structure
 * - Lifecycle hooks
 * - API usage (logging, course access)
 * - Event emission
 * - State persistence
 */
class HelloWorldPlugin : public classtop::Plugin {
public:
    explicit HelloWorldPlugin(std::shared_ptr<classtop::PluginAPI> api);

    // Lifecycle hooks
    void OnEnable() override;
    void OnDisable() override;
    std::string OnSave() override;
    void OnRestore(const std::string& state) override;

    // Plugin identification
    std::string GetId() const override;

private:
    // Private methods
    void DisplayCourses();
    void SendWelcomeEvent();

    // State
    int message_count_ = 0;
};
