"""
Hello World Plugin for ClassTop

A simple example plugin that demonstrates:
- Basic plugin structure
- Lifecycle hooks (on_enable, on_disable)
- Logging
- Fetching course data
- Event emission
"""

from tauri_app.plugin_system.base import Plugin
from datetime import datetime


class HelloWorldPlugin(Plugin):
    """Simple hello world plugin"""

    def __init__(self, plugin_api):
        super().__init__(plugin_api)
        self.message_count = 0

    async def on_enable(self):
        """Called when plugin is enabled"""
        self.plugin_api.log_info("=" * 50)
        self.plugin_api.log_info("Hello World Plugin Enabled!")
        self.plugin_api.log_info("=" * 50)

        # Log current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.plugin_api.log_info(f"Plugin started at: {current_time}")

        # Fetch and display course count
        try:
            courses = await self.plugin_api.get_courses()
            self.plugin_api.log_info(f"Found {len(courses)} courses in the system")

            # Display course names
            if courses:
                self.plugin_api.log_info("Course list:")
                for idx, course in enumerate(courses, 1):
                    self.plugin_api.log_info(f"  {idx}. {course.name} - {course.teacher}")
        except Exception as e:
            self.plugin_api.log_error(f"Failed to fetch courses: {e}")

        # Emit a custom event
        await self.plugin_api.emit_event("hello_world_started", {
            "plugin_id": self.id,
            "message": "Hello from Python plugin!",
            "timestamp": current_time
        })

        self.plugin_api.log_info("Hello World Plugin ready!")

    async def on_disable(self):
        """Called when plugin is disabled"""
        self.plugin_api.log_info("=" * 50)
        self.plugin_api.log_info("Hello World Plugin Disabled!")
        self.plugin_api.log_info(f"Total messages logged: {self.message_count}")
        self.plugin_api.log_info("=" * 50)

        # Emit goodbye event
        await self.plugin_api.emit_event("hello_world_stopped", {
            "plugin_id": self.id,
            "message": "Goodbye from Python plugin!",
            "message_count": self.message_count
        })

    async def on_save(self):
        """Save plugin state for hot reload"""
        return {
            "message_count": self.message_count,
            "version": "1.0.0"
        }

    async def on_restore(self, state):
        """Restore plugin state after hot reload"""
        self.message_count = state.get("message_count", 0)
        self.plugin_api.log_info(f"State restored: message_count={self.message_count}")
