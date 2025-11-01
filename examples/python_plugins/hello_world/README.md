# Hello World Plugin

A simple example plugin demonstrating the basic structure of a ClassTop Python plugin.

## Features

- ✅ Basic plugin lifecycle hooks
- ✅ Logging demonstration
- ✅ Fetching course data via API
- ✅ Custom event emission
- ✅ State persistence (hot reload support)

## Installation

1. Copy this directory to your ClassTop plugins folder:

```bash
cp -r hello_world ~/.classtop/plugins/
```

2. Restart ClassTop or reload plugins

3. Enable the plugin in Settings → Plugin Management

## What This Plugin Does

When enabled, this plugin:
1. Logs a welcome message
2. Fetches all courses from the database
3. Displays the course count and names
4. Emits a `hello_world_started` event

When disabled, it:
1. Logs a goodbye message with statistics
2. Emits a `hello_world_stopped` event

## Events

This plugin emits two custom events:

### `hello_world_started`
```json
{
  "plugin_id": "com.example.hello_world",
  "message": "Hello from Python plugin!",
  "timestamp": "2025-11-01 10:30:00"
}
```

### `hello_world_stopped`
```json
{
  "plugin_id": "com.example.hello_world",
  "message": "Goodbye from Python plugin!",
  "message_count": 0
}
```

## Code Structure

```
hello_world/
├── plugin.yaml      # Plugin metadata
├── plugin.py        # Plugin implementation
└── README.md        # This file
```

## Learning Points

This example demonstrates:

1. **Plugin Class Structure**: Inherit from `Plugin` base class
2. **Lifecycle Hooks**: `on_enable()`, `on_disable()`, `on_save()`, `on_restore()`
3. **API Usage**: `get_courses()`, `log_info()`, `emit_event()`
4. **State Management**: Saving and restoring plugin state for hot reload
5. **Error Handling**: Try-except blocks for robust operation

## Next Steps

Once you understand this example, check out:
- `course_statistics` - Data aggregation and analysis
- `schedule_export` - File operations and external APIs

## Related Documentation

- [Python Plugin Development Guide](../../../docs/PYTHON_PLUGIN_GUIDE.md)
- [Plugin IPC Specification](../../../docs/PLUGIN_IPC_SPECIFICATION.md)
