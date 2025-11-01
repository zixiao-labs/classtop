"""
Schedule Export Plugin for ClassTop

Demonstrates:
- File operations and export functionality
- Multiple export formats (CSV, iCal, JSON)
- External library integration (icalendar)
- Datetime manipulation
- User-configurable export options
"""

from tauri_app.plugin_system.base import Plugin
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv


class ScheduleExportPlugin(Plugin):
    """Exports schedule data to various formats"""

    def __init__(self, plugin_api):
        super().__init__(plugin_api)
        self.export_dir = None
        self.config = {}

    async def on_enable(self):
        """Initialize plugin"""
        self.plugin_api.log_info("Schedule Export Plugin enabled")

        # Load configuration
        await self.load_config()

        # Set up export directory
        self.export_dir = Path.home() / ".classtop" / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

        self.plugin_api.log_info(f"Export directory: {self.export_dir}")

    async def on_disable(self):
        """Clean up resources"""
        self.plugin_api.log_info("Schedule Export Plugin disabled")

    async def load_config(self):
        """Load plugin configuration"""
        config = await self.plugin_api.get_plugin_data("config")

        if not config:
            config = {
                "default_format": "csv",
                "include_teacher": True,
                "include_location": True,
                "export_all_weeks": False
            }
            await self.plugin_api.set_plugin_data("config", config)

        self.config = config

    async def export_to_csv(self, week=None):
        """Export schedule to CSV format"""
        try:
            # Get week info
            if week is None:
                week_info = await self.plugin_api.get_current_week()
                week = week_info.get("week", 1)

            # Fetch schedule data
            schedule = await self.plugin_api.get_schedule_for_week(week)

            # Prepare CSV file
            filename = f"schedule_week_{week}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = self.export_dir / filename

            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Header
                header = ['Day', 'Start Time', 'End Time', 'Course']
                if self.config.get('include_teacher', True):
                    header.append('Teacher')
                if self.config.get('include_location', True):
                    header.append('Location')

                writer.writerow(header)

                # Data rows
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

                for day in sorted(schedule.keys()):
                    day_name = day_names[day - 1] if 1 <= day <= 7 else f'Day {day}'

                    for entry in schedule[day]:
                        row = [
                            day_name,
                            entry.start_time,
                            entry.end_time,
                            entry.course.name
                        ]

                        if self.config.get('include_teacher', True):
                            row.append(entry.course.teacher)
                        if self.config.get('include_location', True):
                            row.append(entry.course.location)

                        writer.writerow(row)

            self.plugin_api.log_info(f"Exported to CSV: {filepath}")

            # Emit export event
            await self.plugin_api.emit_event("schedule_exported", {
                "format": "csv",
                "filename": filename,
                "week": week,
                "path": str(filepath)
            })

            return str(filepath)

        except Exception as e:
            self.plugin_api.log_error(f"CSV export failed: {e}")
            raise

    async def export_to_json(self, week=None):
        """Export schedule to JSON format"""
        try:
            # Get week info
            if week is None:
                week_info = await self.plugin_api.get_current_week()
                week = week_info.get("week", 1)

            # Fetch schedule data
            schedule = await self.plugin_api.get_schedule_for_week(week)

            # Convert to JSON-serializable format
            json_data = {
                "week": week,
                "export_date": datetime.now().isoformat(),
                "schedule": {}
            }

            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

            for day, entries in schedule.items():
                day_name = day_names[day - 1] if 1 <= day <= 7 else f'Day {day}'

                json_data["schedule"][day_name] = [
                    {
                        "start_time": entry.start_time,
                        "end_time": entry.end_time,
                        "course": {
                            "name": entry.course.name,
                            "teacher": entry.course.teacher,
                            "location": entry.course.location,
                            "color": entry.course.color
                        }
                    }
                    for entry in entries
                ]

            # Write JSON file
            filename = f"schedule_week_{week}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.export_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            self.plugin_api.log_info(f"Exported to JSON: {filepath}")

            await self.plugin_api.emit_event("schedule_exported", {
                "format": "json",
                "filename": filename,
                "week": week,
                "path": str(filepath)
            })

            return str(filepath)

        except Exception as e:
            self.plugin_api.log_error(f"JSON export failed: {e}")
            raise

    async def export_to_ical(self, week=None):
        """Export schedule to iCalendar format"""
        try:
            # Import icalendar (optional dependency)
            try:
                from icalendar import Calendar, Event
            except ImportError:
                self.plugin_api.log_error("icalendar library not installed. Please install with: pip install icalendar")
                raise ImportError("icalendar library required for iCal export")

            # Get week info
            if week is None:
                week_info = await self.plugin_api.get_current_week()
                week = week_info.get("week", 1)

            # Get semester start date
            semester_start = await self.plugin_api.get_setting("semester_start_date")
            if not semester_start:
                self.plugin_api.log_error("Semester start date not configured")
                raise ValueError("Semester start date required for iCal export")

            # Parse semester start date
            start_date = datetime.fromisoformat(semester_start).date()

            # Calculate week start date
            week_start = start_date + timedelta(weeks=week - 1)

            # Fetch schedule data
            schedule = await self.plugin_api.get_schedule_for_week(week)

            # Create calendar
            cal = Calendar()
            cal.add('prodid', '-//ClassTop Schedule Export//EN')
            cal.add('version', '2.0')
            cal.add('x-wr-calname', f'ClassTop Schedule - Week {week}')
            cal.add('x-wr-timezone', 'UTC')

            # Add events for each class
            for day, entries in schedule.items():
                # Calculate date for this day
                class_date = week_start + timedelta(days=day - 1)

                for entry in entries:
                    # Parse times
                    start_hour, start_min = map(int, entry.start_time.split(':'))
                    end_hour, end_min = map(int, entry.end_time.split(':'))

                    # Create event
                    event = Event()
                    event.add('summary', entry.course.name)
                    event.add('dtstart', datetime.combine(class_date, datetime.min.time().replace(hour=start_hour, minute=start_min)))
                    event.add('dtend', datetime.combine(class_date, datetime.min.time().replace(hour=end_hour, minute=end_min)))
                    event.add('location', entry.course.location)
                    event.add('description', f'Teacher: {entry.course.teacher}')

                    cal.add_component(event)

            # Write iCal file
            filename = f"schedule_week_{week}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
            filepath = self.export_dir / filename

            with open(filepath, 'wb') as f:
                f.write(cal.to_ical())

            self.plugin_api.log_info(f"Exported to iCal: {filepath}")

            await self.plugin_api.emit_event("schedule_exported", {
                "format": "ical",
                "filename": filename,
                "week": week,
                "path": str(filepath)
            })

            return str(filepath)

        except Exception as e:
            self.plugin_api.log_error(f"iCal export failed: {e}")
            raise

    async def export_schedule(self, export_format="csv", week=None):
        """
        Export schedule in specified format

        Args:
            export_format: "csv", "json", or "ical"
            week: Week number (None for current week)

        Returns:
            Path to exported file
        """
        if export_format == "csv":
            return await self.export_to_csv(week)
        elif export_format == "json":
            return await self.export_to_json(week)
        elif export_format == "ical":
            return await self.export_to_ical(week)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
