cmake_minimum_required(VERSION 3.15)

project(SimpleDataProcessorPlugin
    VERSION 1.0.0
    DESCRIPTION "Simple Data Processor Plugin for ClassTop"
    LANGUAGES CXX
)

# C++17 standard required
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Source files
set(PLUGIN_SOURCES
    src/plugin.cpp
)

set(PLUGIN_HEADERS
    include/plugin.h
)

# Create shared library
add_library(plugin SHARED ${PLUGIN_SOURCES} ${PLUGIN_HEADERS})

# Include directories
target_include_directories(plugin PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Find ClassTop SDK
find_package(ClassTopSDK REQUIRED)
target_link_libraries(plugin PRIVATE ClassTopSDK::ClassTopSDK)

# Find nlohmann_json
find_package(nlohmann_json 3.10.0 REQUIRED)
target_link_libraries(plugin PRIVATE nlohmann_json::nlohmann_json)

# Platform-specific settings
if(WIN32)
    target_compile_definitions(plugin PRIVATE
        _WIN32_WINNT=0x0601
        NOMINMAX
    )
    set_target_properties(plugin PROPERTIES
        OUTPUT_NAME "plugin"
        PREFIX ""
        SUFFIX ".dll"
    )
elseif(APPLE)
    set_target_properties(plugin PROPERTIES
        OUTPUT_NAME "plugin"
        PREFIX "lib"
        SUFFIX ".dylib"
    )
elseif(UNIX)
    # Linux - requires pthread for threading
    target_link_libraries(plugin PRIVATE pthread)
    set_target_properties(plugin PROPERTIES
        OUTPUT_NAME "plugin"
        PREFIX "lib"
        SUFFIX ".so"
    )
endif()

# Compiler warnings
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(plugin PRIVATE
        -Wall -Wextra -Wpedantic
    )
elseif(MSVC)
    target_compile_options(plugin PRIVATE
        /W4
    )
endif()

# Output directory
set_target_properties(plugin PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Install target
install(TARGETS plugin
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)

install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/plugin.yaml
    DESTINATION .
)
