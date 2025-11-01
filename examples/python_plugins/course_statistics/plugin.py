"""
Course Statistics Plugin for ClassTop

Demonstrates:
- Data aggregation and analysis
- Background task scheduling
- Configuration management
- Frontend integration
- Event handling
"""

from tauri_app.plugin_system.base import Plugin
from datetime import datetime
from collections import defaultdict
import asyncio


class CourseStatisticsPlugin(Plugin):
    """Analyzes and reports course statistics"""

    def __init__(self, plugin_api):
        super().__init__(plugin_api)
        self.stats = {}
        self.update_task = None
        self.update_interval = 300  # 5 minutes default

    async def on_enable(self):
        """Initialize plugin and start background tasks"""
        self.plugin_api.log_info("Course Statistics Plugin enabled")

        # Load configuration
        await self.load_config()

        # Subscribe to course and schedule updates
        self.plugin_api.on("course_update", self.on_course_update)
        self.plugin_api.on("schedule_update", self.on_schedule_update)

        # Perform initial analysis
        await self.analyze_statistics()

        # Start background update task
        self.update_task = asyncio.create_task(self.periodic_update())

        self.plugin_api.log_info("Statistics analysis started")

    async def on_disable(self):
        """Clean up resources"""
        # Cancel background task
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        # Unsubscribe from events
        self.plugin_api.off("course_update", self.on_course_update)
        self.plugin_api.off("schedule_update", self.on_schedule_update)

        self.plugin_api.log_info("Course Statistics Plugin disabled")

    async def on_save(self):
        """Save plugin state"""
        return {
            "stats": self.stats,
            "update_interval": self.update_interval,
            "version": "1.0.0"
        }

    async def on_restore(self, state):
        """Restore plugin state"""
        self.stats = state.get("stats", {})
        self.update_interval = state.get("update_interval", 300)
        self.plugin_api.log_info(f"State restored: {len(self.stats)} statistics")

    async def load_config(self):
        """Load plugin configuration"""
        config = await self.plugin_api.get_plugin_data("config")

        if not config:
            # Set default config
            config = {
                "update_interval": 300,  # 5 minutes
                "enable_notifications": True,
                "min_class_hours": 0
            }
            await self.plugin_api.set_plugin_data("config", config)

        self.update_interval = config.get("update_interval", 300)
        self.plugin_api.log_info(f"Config loaded: update_interval={self.update_interval}s")

    async def periodic_update(self):
        """Background task for periodic statistics updates"""
        while True:
            try:
                await asyncio.sleep(self.update_interval)
                await self.analyze_statistics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.plugin_api.log_error(f"Error in periodic update: {e}")

    async def analyze_statistics(self):
        """Analyze course and schedule data"""
        try:
            # Fetch all courses
            courses = await self.plugin_api.get_courses()

            # Get current week
            week_info = await self.plugin_api.get_current_week()
            current_week = week_info.get("week", 1)

            # Fetch schedule for current week
            schedule = await self.plugin_api.get_schedule_for_week(current_week)

            # Calculate statistics
            stats = {
                "total_courses": len(courses),
                "courses_by_teacher": defaultdict(int),
                "courses_by_location": defaultdict(int),
                "schedule_entries_per_day": defaultdict(int),
                "total_class_hours": 0,
                "busiest_day": None,
                "timestamp": datetime.now().isoformat()
            }

            # Analyze courses
            for course in courses:
                stats["courses_by_teacher"][course.teacher] += 1
                stats["courses_by_location"][course.location] += 1

            # Analyze schedule
            max_entries = 0
            busiest_day = 0

            for day, entries in schedule.items():
                count = len(entries)
                stats["schedule_entries_per_day"][day] = count

                # Calculate class hours
                for entry in entries:
                    start_hour, start_min = map(int, entry.start_time.split(":"))
                    end_hour, end_min = map(int, entry.end_time.split(":"))
                    duration = (end_hour * 60 + end_min - start_hour * 60 - start_min) / 60
                    stats["total_class_hours"] += duration

                if count > max_entries:
                    max_entries = count
                    busiest_day = day

            stats["busiest_day"] = busiest_day

            # Convert defaultdict to dict for JSON serialization
            stats["courses_by_teacher"] = dict(stats["courses_by_teacher"])
            stats["courses_by_location"] = dict(stats["courses_by_location"])
            stats["schedule_entries_per_day"] = dict(stats["schedule_entries_per_day"])

            self.stats = stats

            # Emit statistics update event
            await self.plugin_api.emit_event("statistics_updated", stats)

            # Log summary
            self.plugin_api.log_info(
                f"Statistics updated: {stats['total_courses']} courses, "
                f"{stats['total_class_hours']:.1f} hours/week, "
                f"busiest day: {self.get_day_name(busiest_day)}"
            )

        except Exception as e:
            self.plugin_api.log_error(f"Failed to analyze statistics: {e}")

    async def on_course_update(self, data):
        """Handle course update events"""
        action = data.get("action")
        self.plugin_api.log_info(f"Course {action}, recalculating statistics...")
        await self.analyze_statistics()

    async def on_schedule_update(self, data):
        """Handle schedule update events"""
        action = data.get("action")
        self.plugin_api.log_info(f"Schedule {action}, recalculating statistics...")
        await self.analyze_statistics()

    @staticmethod
    def get_day_name(day):
        """Convert day number to name"""
        days = {
            1: "Monday", 2: "Tuesday", 3: "Wednesday",
            4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"
        }
        return days.get(day, "Unknown")
