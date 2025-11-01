cmake_minimum_required(VERSION 3.15)

# 项目信息
project(ClassTopPlugin
    VERSION 1.0.0
    DESCRIPTION "A ClassTop C++ plugin"
    LANGUAGES CXX
)

# C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 导出编译命令(用于 IDE)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# 构建类型
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# 编译选项
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Werror)
endif()

# ========== 依赖项 ==========

# 查找 ClassTop SDK
find_package(ClassTopSDK REQUIRED)

# nlohmann/json (JSON 处理库)
find_package(nlohmann_json 3.10.0 REQUIRED)

# ========== 插件库 ==========

# 源文件
set(PLUGIN_SOURCES
    src/plugin.cpp
)

# 头文件
set(PLUGIN_HEADERS
    include/plugin.h
)

# 创建动态库
add_library(plugin SHARED
    ${PLUGIN_SOURCES}
    ${PLUGIN_HEADERS}
)

# 包含目录
target_include_directories(plugin
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${ClassTopSDK_INCLUDE_DIRS}
)

# 链接库
target_link_libraries(plugin
    PRIVATE
        ClassTopSDK::ClassTopSDK
        nlohmann_json::nlohmann_json
)

# 编译定义
target_compile_definitions(plugin
    PRIVATE
        CLASSTOP_PLUGIN_EXPORTS
)

# Windows 特定配置
if(WIN32)
    # 导出所有符号
    set_target_properties(plugin PROPERTIES
        WINDOWS_EXPORT_ALL_SYMBOLS ON
    )
endif()

# 输出目录
set_target_properties(plugin PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# ========== 安装 ==========

# 安装插件库
install(TARGETS plugin
    LIBRARY DESTINATION plugins/${PROJECT_NAME}
    RUNTIME DESTINATION plugins/${PROJECT_NAME}
)

# 安装元数据文件
install(FILES
    plugin.yaml
    DESTINATION plugins/${PROJECT_NAME}
)

# 安装前端组件(如果有)
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/plugin_ui.js")
    install(FILES
        plugin_ui.js
        DESTINATION plugins/${PROJECT_NAME}
    )
endif()

# ========== 测试 (可选) ==========

option(BUILD_TESTING "Build tests" OFF)

if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()

# ========== CPack (可选,用于打包) ==========

option(BUILD_PACKAGE "Build installable package" OFF)

if(BUILD_PACKAGE)
    include(cmake/Packaging.cmake)
endif()

# ========== 打印配置信息 ==========

message(STATUS "")
message(STATUS "==================================================")
message(STATUS "  ClassTop Plugin Configuration")
message(STATUS "==================================================")
message(STATUS "  Project:         ${PROJECT_NAME}")
message(STATUS "  Version:         ${PROJECT_VERSION}")
message(STATUS "  Build type:      ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ standard:    C++${CMAKE_CXX_STANDARD}")
message(STATUS "  Install prefix:  ${CMAKE_INSTALL_PREFIX}")
message(STATUS "  ClassTop SDK:    ${ClassTopSDK_VERSION}")
message(STATUS "==================================================")
message(STATUS "")
