"""
Schedule Manager for ClassTop application.
Handles all schedule-related operations with proper logging.
"""

import json
import sqlite3
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from contextlib import contextmanager
from pathlib import Path

from . import logger as _logger


class ScheduleManager:
    """Manages course schedules and related operations."""

    def __init__(self, db_path: Path, event_handler=None):
        self.db_path = db_path
        self.logger = _logger
        self.event_handler = event_handler

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            self.logger.log_message("debug", f"Database connection opened: {self.db_path}")
            yield conn
        except Exception as e:
            self.logger.log_message("error", f"Database connection failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
                self.logger.log_message("debug", "Database connection closed")

    # Course Management Methods
    def add_course(self, name: str, teacher: Optional[str] = None,
                   location: Optional[str] = None, color: Optional[str] = None) -> int:
        """Add a new course and return its ID."""
        self.logger.log_message("info", f"Adding course: {name}")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO courses (name, teacher, location, color) VALUES (?, ?, ?, ?)",
                    (name, teacher, location, color)
                )
                conn.commit()
                course_id = cur.lastrowid if cur.lastrowid is not None else -1

                if course_id > 0:
                    self.logger.log_message("info", f"Course added successfully with ID: {course_id}")
                    # Emit event if handler is available
                    if self.event_handler:
                        self.event_handler.emit_course_added(course_id, name)
                else:
                    self.logger.log_message("warning", f"Failed to get course ID after insertion")

                return course_id
            except sqlite3.IntegrityError as e:
                self.logger.log_message("error", f"Integrity error adding course: {e}")
                return -1
            except Exception as e:
                self.logger.log_message("error", f"Unexpected error adding course: {e}")
                return -1

    def get_courses(self) -> List[Dict]:
        """Get all courses."""
        self.logger.log_message("debug", "Fetching all courses")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT id, name, teacher, location, color FROM courses")
                courses = []

                for row in cur.fetchall():
                    courses.append({
                        "id": row[0],
                        "name": row[1],
                        "teacher": row[2],
                        "location": row[3],
                        "color": row[4]
                    })

                self.logger.log_message("debug", f"Retrieved {len(courses)} courses")
                return courses
            except Exception as e:
                self.logger.log_message("error", f"Error fetching courses: {e}")
                return []

    def update_course(self, course_id: int, **kwargs) -> bool:
        """Update course information."""
        self.logger.log_message("info", f"Updating course {course_id} with: {kwargs}")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()

                # Build update query dynamically
                valid_fields = ['name', 'teacher', 'location', 'color']
                fields_to_update = {k: v for k, v in kwargs.items() if k in valid_fields}

                if not fields_to_update:
                    self.logger.log_message("warning", "No valid fields to update")
                    return False

                set_clause = ", ".join([f"{k} = ?" for k in fields_to_update.keys()])
                values = list(fields_to_update.values()) + [course_id]

                query = f"UPDATE courses SET {set_clause} WHERE id = ?"
                cur.execute(query, values)
                conn.commit()

                success = cur.rowcount > 0
                if success:
                    self.logger.log_message("info", f"Course {course_id} updated successfully")
                    # Emit event if handler is available
                    if self.event_handler:
                        self.event_handler.emit_course_updated(course_id, **fields_to_update)
                else:
                    self.logger.log_message("warning", f"Course {course_id} not found")

                return success
            except Exception as e:
                self.logger.log_message("error", f"Error updating course: {e}")
                return False

    def delete_course(self, course_id: int) -> bool:
        """Delete a course and all its schedule entries."""
        self.logger.log_message("info", f"Deleting course {course_id}")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()

                # Check if course exists
                cur.execute("SELECT name FROM courses WHERE id = ?", (course_id,))
                course = cur.fetchone()

                if not course:
                    self.logger.log_message("warning", f"Course {course_id} not found")
                    return False

                # Delete course (CASCADE will handle schedule entries)
                cur.execute("DELETE FROM courses WHERE id = ?", (course_id,))
                conn.commit()

                self.logger.log_message("info", f"Course '{course[0]}' (ID: {course_id}) deleted successfully")
                # Emit event if handler is available
                if self.event_handler:
                    self.event_handler.emit_course_deleted(course_id)
                return True
            except Exception as e:
                self.logger.log_message("error", f"Error deleting course: {e}")
                return False

    # Schedule Management Methods
    def add_schedule_entry(self, course_id: int, day_of_week: int,
                          start_time: str, end_time: str,
                          weeks: Optional[List[int]] = None,
                          note: Optional[str] = None) -> int:
        """Add a schedule entry."""
        self.logger.log_message("info", f"Adding schedule entry for course {course_id}")

        # Validate input
        if not self._validate_time_format(start_time) or not self._validate_time_format(end_time):
            self.logger.log_message("error", "Invalid time format. Use HH:MM")
            return -1

        if not 1 <= day_of_week <= 7:
            self.logger.log_message("error", f"Invalid day_of_week: {day_of_week}")
            return -1

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()

                # Check if course exists
                cur.execute("SELECT name FROM courses WHERE id = ?", (course_id,))
                course = cur.fetchone()
                if not course:
                    self.logger.log_message("error", f"Course {course_id} does not exist")
                    return -1

                # Check for time conflicts
                if self._has_time_conflict(conn, day_of_week, start_time, end_time, weeks):
                    self.logger.log_message("warning", "Schedule conflict detected")

                weeks_json = json.dumps(weeks) if weeks else None
                cur.execute(
                    """INSERT INTO schedule (course_id, day_of_week, start_time, end_time, weeks, note)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (course_id, day_of_week, start_time, end_time, weeks_json, note)
                )
                conn.commit()

                entry_id = cur.lastrowid if cur.lastrowid is not None else -1
                if entry_id > 0:
                    self.logger.log_message("info", f"Schedule entry added with ID: {entry_id}")
                    # Emit event if handler is available
                    if self.event_handler:
                        self.event_handler.emit_schedule_added(entry_id, course_id, day_of_week, start_time, end_time)

                return entry_id
            except Exception as e:
                self.logger.log_message("error", f"Error adding schedule entry: {e}")
                return -1

    def get_schedule(self, week: Optional[int] = None) -> List[Dict]:
        """Get schedule for a specific week or all schedules."""
        self.logger.log_message("debug", f"Fetching schedule for week: {week if week else 'all'}")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()
                query = """
                    SELECT s.id, s.course_id, c.name, c.teacher, c.location, c.color,
                           s.day_of_week, s.start_time, s.end_time, s.weeks, s.note
                    FROM schedule s
                    JOIN courses c ON s.course_id = c.id
                    ORDER BY s.day_of_week, s.start_time
                """
                cur.execute(query)

                schedule = []
                for row in cur.fetchall():
                    weeks_json = row[9]
                    weeks_list = json.loads(weeks_json) if weeks_json else []

                    # Filter by week if specified
                    if week is not None and weeks_list and week not in weeks_list:
                        continue

                    schedule.append({
                        "id": row[0],
                        "course_id": row[1],
                        "course_name": row[2],
                        "teacher": row[3],
                        "location": row[4],
                        "color": row[5],
                        "day_of_week": row[6],
                        "start_time": row[7],
                        "end_time": row[8],
                        "weeks": weeks_list,
                        "note": row[10]
                    })

                self.logger.log_message("debug", f"Retrieved {len(schedule)} schedule entries")
                return schedule
            except Exception as e:
                self.logger.log_message("error", f"Error fetching schedule: {e}")
                return []

    def delete_schedule_entry(self, entry_id: int) -> bool:
        """Delete a schedule entry."""
        self.logger.log_message("info", f"Deleting schedule entry {entry_id}")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM schedule WHERE id = ?", (entry_id,))
                conn.commit()

                success = cur.rowcount > 0
                if success:
                    self.logger.log_message("info", f"Schedule entry {entry_id} deleted")
                    # Emit event if handler is available
                    if self.event_handler:
                        self.event_handler.emit_schedule_deleted(entry_id)
                else:
                    self.logger.log_message("warning", f"Schedule entry {entry_id} not found")

                return success
            except Exception as e:
                self.logger.log_message("error", f"Error deleting schedule entry: {e}")
                return False

    def get_schedule_by_day(self, day_of_week: int, week: Optional[int] = None) -> List[Dict]:
        """Get all classes for a specific day, optionally filtered by week."""
        self.logger.log_message("debug", f"Getting schedule for day {day_of_week}, week {week}")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()
                query = """
                    SELECT s.id, c.name, c.teacher, c.location, s.day_of_week,
                           s.start_time, s.end_time, s.weeks, c.color
                    FROM schedule s
                    JOIN courses c ON s.course_id = c.id
                    WHERE s.day_of_week = ?
                    ORDER BY s.start_time
                """
                cur.execute(query, (day_of_week,))

                classes = []
                for row in cur.fetchall():
                    weeks_list = json.loads(row[7]) if row[7] else []

                    # Filter by week if specified
                    if week is not None and weeks_list and week not in weeks_list:
                        continue

                    classes.append({
                        "id": row[0],
                        "name": row[1],
                        "teacher": row[2],
                        "location": row[3],
                        "day_of_week": row[4],
                        "start_time": row[5],
                        "end_time": row[6],
                        "weeks": weeks_list,
                        "color": row[8] if len(row) > 8 else None
                    })

                return classes
            except Exception as e:
                self.logger.log_message("error", f"Error getting schedule by day: {e}")
                return []

    def get_schedule_for_week(self, week: Optional[int] = None) -> List[Dict]:
        """Get all classes for the entire week, optionally filtered by week number."""
        self.logger.log_message("debug", f"Getting schedule for week {week}")

        all_classes = []
        for day in range(1, 8):  # Monday to Sunday
            day_classes = self.get_schedule_by_day(day, week)
            all_classes.extend(day_classes)

        return all_classes

    # Utility Methods
    def _validate_time_format(self, time_str: str) -> bool:
        """Validate time string format (HH:MM)."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except:
            return False

    def _has_time_conflict(self, conn: sqlite3.Connection, day_of_week: int,
                          start_time: str, end_time: str,
                          weeks: Optional[List[int]] = None) -> bool:
        """Check if there's a time conflict with existing schedule."""
        try:
            cur = conn.cursor()
            query = """
                SELECT s.id, s.start_time, s.end_time, s.weeks, c.name
                FROM schedule s
                JOIN courses c ON s.course_id = c.id
                WHERE s.day_of_week = ?
            """
            cur.execute(query, (day_of_week,))

            for row in cur.fetchall():
                existing_start = row[1]
                existing_end = row[2]
                existing_weeks = json.loads(row[3]) if row[3] else []

                # Check time overlap
                if not (end_time <= existing_start or start_time >= existing_end):
                    # Check week overlap
                    if not weeks or not existing_weeks:
                        self.logger.log_message("warning",
                            f"Time conflict with course '{row[4]}' ({existing_start}-{existing_end})")
                        return True

                    week_overlap = set(weeks) & set(existing_weeks)
                    if week_overlap:
                        self.logger.log_message("warning",
                            f"Time conflict with course '{row[4]}' in weeks {week_overlap}")
                        return True

            return False
        except Exception as e:
            self.logger.log_message("error", f"Error checking time conflict: {e}")
            return False

    def calculate_week_number(self, semester_start_date: Optional[str] = None) -> int:
        """Calculate current week number based on semester start date."""
        if not semester_start_date:
            return 1

        try:
            start_date = datetime.strptime(semester_start_date, "%Y-%m-%d")
            current_date = datetime.now()
            days_diff = (current_date - start_date).days
            return max(1, (days_diff // 7) + 1)
        except Exception as e:
            self.logger.log_message("error", f"Error calculating week number: {e}")
            return 1

    def check_conflicts(self, day_of_week: int, start_time: str, end_time: str,
                       weeks: Optional[List[int]] = None,
                       exclude_entry_id: Optional[int] = None) -> List[Dict]:
        """
        Check for schedule conflicts and return detailed conflict information.

        Args:
            day_of_week: Day of week (1-7)
            start_time: Start time (HH:MM)
            end_time: End time (HH:MM)
            weeks: List of weeks this entry applies to
            exclude_entry_id: Entry ID to exclude (for editing existing entries)

        Returns:
            List of conflicting schedule entries with conflict details
        """
        self.logger.log_message("debug", f"Checking conflicts for {day_of_week} {start_time}-{end_time}")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()
                query = """
                    SELECT s.id, c.name, c.teacher, c.location, s.start_time, s.end_time,
                           s.day_of_week, s.weeks
                    FROM schedule s
                    JOIN courses c ON s.course_id = c.id
                    WHERE s.day_of_week = ?
                """
                params = [day_of_week]

                # Exclude specific entry if editing
                if exclude_entry_id:
                    query += " AND s.id != ?"
                    params.append(exclude_entry_id)

                cur.execute(query, params)

                conflicts = []
                for row in cur.fetchall():
                    existing_id = row[0]
                    existing_name = row[1]
                    existing_teacher = row[2]
                    existing_location = row[3]
                    existing_start = row[4]
                    existing_end = row[5]
                    existing_day = row[6]
                    existing_weeks = json.loads(row[7]) if row[7] else []

                    # Check time overlap
                    if not (end_time <= existing_start or start_time >= existing_end):
                        # Check week overlap
                        conflict_weeks = []

                        if not weeks or not existing_weeks:
                            # If either has no week restriction, it conflicts for all weeks
                            conflict_weeks = weeks if weeks else existing_weeks if existing_weeks else [1]
                        else:
                            # Calculate actual conflicting weeks
                            conflict_weeks = list(set(weeks) & set(existing_weeks))

                        if conflict_weeks or (not weeks and not existing_weeks):
                            conflicts.append({
                                "id": existing_id,
                                "course_name": existing_name,
                                "teacher": existing_teacher,
                                "location": existing_location,
                                "start_time": existing_start,
                                "end_time": existing_end,
                                "day_of_week": existing_day,
                                "weeks": existing_weeks,
                                "conflict_weeks": conflict_weeks
                            })

                            self.logger.log_message("warning",
                                f"Conflict detected with '{existing_name}' ({existing_start}-{existing_end}) "
                                f"in weeks {conflict_weeks}")

                return conflicts

            except Exception as e:
                self.logger.log_message("error", f"Error checking conflicts: {e}")
                return []

    def get_statistics(self) -> Dict:
        """Get schedule statistics."""
        self.logger.log_message("debug", "Calculating schedule statistics")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()

                # Count courses
                cur.execute("SELECT COUNT(*) FROM courses")
                total_courses = cur.fetchone()[0]

                # Count schedule entries
                cur.execute("SELECT COUNT(*) FROM schedule")
                total_entries = cur.fetchone()[0]

                # Get busiest day
                cur.execute("""
                    SELECT day_of_week, COUNT(*) as count
                    FROM schedule
                    GROUP BY day_of_week
                    ORDER BY count DESC
                    LIMIT 1
                """)
                busiest = cur.fetchone()
                busiest_day = busiest[0] if busiest else None

                stats = {
                    "total_courses": total_courses,
                    "total_schedule_entries": total_entries,
                    "busiest_day": busiest_day
                }

                self.logger.log_message("info", f"Statistics: {stats}")
                return stats
            except Exception as e:
                self.logger.log_message("error", f"Error getting statistics: {e}")
                return {}

    # Sync Methods for Management Server Integration
    def get_all_courses(self) -> List[Dict]:
        """获取所有课程（用于同步）"""
        self.logger.log_message("debug", "Fetching all courses for sync")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, name, teacher, location, color
                    FROM courses
                    ORDER BY id
                """)

                courses = []
                for row in cur.fetchall():
                    courses.append({
                        "id": row[0],
                        "name": row[1],
                        "teacher": row[2] or "",
                        "location": row[3] or "",
                        "color": row[4] or "#6750A4"
                    })

                self.logger.log_message("debug", f"Retrieved {len(courses)} courses for sync")
                return courses
            except Exception as e:
                self.logger.log_message("error", f"Error fetching courses for sync: {e}")
                return []

    def get_all_schedule_entries(self) -> List[Dict]:
        """获取所有课程表条目（用于同步）"""
        self.logger.log_message("debug", "Fetching all schedule entries for sync")

        with self.get_connection() as conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT s.id, s.course_id, s.day_of_week, s.start_time, s.end_time, s.weeks,
                           c.name, c.teacher, c.location, c.color
                    FROM schedule s
                    JOIN courses c ON s.course_id = c.id
                    ORDER BY s.day_of_week, s.start_time
                """)

                entries = []
                for row in cur.fetchall():
                    entries.append({
                        "id": row[0],
                        "course_id": row[1],
                        "day_of_week": row[2],
                        "start_time": row[3],
                        "end_time": row[4],
                        "weeks": row[5],  # Keep as JSON string
                        "course_name": row[6],
                        "teacher": row[7] or "",
                        "location": row[8] or "",
                        "color": row[9] or "#6750A4"
                    })

                self.logger.log_message("debug", f"Retrieved {len(entries)} schedule entries for sync")
                return entries
            except Exception as e:
                self.logger.log_message("error", f"Error fetching schedule entries for sync: {e}")
                return []