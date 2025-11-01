#pragma once

#include "classtop/plugin.h"
#include "classtop/plugin_api.h"
#include <string>
#include <memory>

/**
 * @brief ClassTop 插件示例
 *
 * 这是一个使用 C++ 开发的 ClassTop 插件模板。
 * 开发者可以基于此模板快速开发自己的插件。
 */
class MyPlugin : public classtop::Plugin {
public:
    /**
     * @brief 构造函数
     * @param api 插件 API 接口
     */
    explicit MyPlugin(std::shared_ptr<classtop::PluginAPI> api);

    /**
     * @brief 析构函数
     */
    ~MyPlugin() override = default;

    /**
     * @brief 插件启用时调用
     *
     * 在此方法中初始化插件,订阅事件,注册服务等
     */
    void OnEnable() override;

    /**
     * @brief 插件禁用时调用
     *
     * 在此方法中清理资源,取消事件订阅等
     */
    void OnDisable() override;

    /**
     * @brief 保存插件状态(用于热重载)
     * @return JSON 格式的状态字符串
     */
    std::string OnSave() override;

    /**
     * @brief 恢复插件状态(用于热重载)
     * @param state JSON 格式的状态字符串
     */
    void OnRestore(const std::string& state) override;

    /**
     * @brief 获取插件 ID
     * @return 插件唯一标识符
     */
    std::string GetId() const override;

private:
    /**
     * @brief 处理日程更新事件
     * @param event_data 事件数据(JSON 格式)
     */
    void OnScheduleUpdate(const std::string& event_data);

    /**
     * @brief 示例:获取并处理课程数据
     */
    void ProcessCourses();

    // 添加你的私有成员变量
    int call_count_ = 0;
};
