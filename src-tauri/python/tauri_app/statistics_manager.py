"""
Statistics Manager for ClassTop
Handles course statistics calculation and attendance tracking
"""

import json
import sqlite3
from typing import Optional, Dict, List
from datetime import datetime, timedelta, date
from contextlib import contextmanager
from pathlib import Path

from . import logger as _logger


class StatisticsManager:
    """Manages course statistics and attendance tracking"""

    def __init__(self, db_path: Path, event_handler=None):
        self.db_path = db_path
        self.logger = _logger
        self.event_handler = event_handler

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            self.logger.log_message("debug", f"Database connection opened: {self.db_path}")
            yield conn
        except Exception as e:
            self.logger.log_message("error", f"Database connection failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
                self.logger.log_message("debug", "Database connection closed")

    # Attendance Tracking Methods
    def mark_attendance(self, course_id: int, schedule_entry_id: int,
                       date_str: str, attended: bool, notes: Optional[str] = None) -> int:
        """
        Mark attendance for a specific class session.

        Args:
            course_id: Course identifier
            schedule_entry_id: Schedule entry identifier
            date_str: Date in YYYY-MM-DD format
            attended: Whether student attended (True) or was absent (False)
            notes: Optional notes about the session

        Returns:
            Session ID if successful, -1 if failed
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()

                # Get schedule entry details
                cur.execute("""
                    SELECT start_time, end_time FROM schedule WHERE id = ?
                """, (schedule_entry_id,))
                entry = cur.fetchone()

                if not entry:
                    self.logger.log_message("error", f"Schedule entry {schedule_entry_id} not found")
                    return -1

                # Check if session already exists
                cur.execute("""
                    SELECT id FROM course_sessions
                    WHERE course_id = ? AND schedule_entry_id = ? AND date = ?
                """, (course_id, schedule_entry_id, date_str))
                existing = cur.fetchone()

                if existing:
                    # Update existing session
                    cur.execute("""
                        UPDATE course_sessions
                        SET attended = ?, notes = ?
                        WHERE id = ?
                    """, (1 if attended else 0, notes, existing['id']))
                    session_id = existing['id']
                    self.logger.log_message("info", f"Updated attendance for session {session_id}")
                else:
                    # Insert new session
                    cur.execute("""
                        INSERT INTO course_sessions
                        (course_id, schedule_entry_id, date, start_time, end_time, attended, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (course_id, schedule_entry_id, date_str, entry['start_time'],
                          entry['end_time'], 1 if attended else 0, notes))
                    session_id = cur.lastrowid
                    self.logger.log_message("info", f"Created attendance record for session {session_id}")

                conn.commit()

                # Emit event if handler is available
                if self.event_handler:
                    self.event_handler.emit_custom_event("attendance-updated", {
                        "session_id": session_id,
                        "course_id": course_id,
                        "date": date_str,
                        "attended": attended
                    })

                return session_id

        except Exception as e:
            self.logger.log_message("error", f"Failed to mark attendance: {e}")
            return -1

    def get_attendance_history(self, course_id: Optional[int] = None,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               limit: int = 100) -> List[Dict]:
        """
        Get attendance history with optional filters.

        Args:
            course_id: Filter by course ID (optional)
            start_date: Filter by start date in YYYY-MM-DD format (optional)
            end_date: Filter by end date in YYYY-MM-DD format (optional)
            limit: Maximum number of records to return

        Returns:
            List of attendance records
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()

                query = """
                    SELECT cs.*, c.name as course_name, c.teacher, c.color
                    FROM course_sessions cs
                    JOIN courses c ON cs.course_id = c.id
                    WHERE 1=1
                """
                params = []

                if course_id:
                    query += " AND cs.course_id = ?"
                    params.append(course_id)

                if start_date:
                    query += " AND cs.date >= ?"
                    params.append(start_date)

                if end_date:
                    query += " AND cs.date <= ?"
                    params.append(end_date)

                query += " ORDER BY cs.date DESC, cs.start_time DESC LIMIT ?"
                params.append(limit)

                cur.execute(query, params)
                rows = cur.fetchall()

                self.logger.log_message("debug", f"Retrieved {len(rows)} attendance records")
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.log_message("error", f"Failed to get attendance history: {e}")
            return []

    def delete_attendance_record(self, session_id: int) -> bool:
        """
        Delete an attendance record.

        Args:
            session_id: Session identifier to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM course_sessions WHERE id = ?", (session_id,))
                conn.commit()

                success = cur.rowcount > 0
                if success:
                    self.logger.log_message("info", f"Deleted attendance record {session_id}")
                    if self.event_handler:
                        self.event_handler.emit_custom_event("attendance-deleted", {
                            "session_id": session_id
                        })
                else:
                    self.logger.log_message("warning", f"Attendance record {session_id} not found")

                return success

        except Exception as e:
            self.logger.log_message("error", f"Failed to delete attendance record: {e}")
            return False

    # Statistics Calculation Methods
    def get_total_course_hours(self, start_week: Optional[int] = None,
                               end_week: Optional[int] = None) -> Dict:
        """
        Calculate total course hours in a week range.

        Args:
            start_week: Start week number (optional)
            end_week: End week number (optional)

        Returns:
            Dictionary with total hours, weekly breakdown, and average
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()

                # Get all schedule entries with duration calculation
                cur.execute("""
                    SELECT s.*, c.name as course_name,
                           CAST((julianday('1970-01-01 ' || s.end_time) -
                                 julianday('1970-01-01 ' || s.start_time)) * 24 AS REAL) as duration
                    FROM schedule s
                    JOIN courses c ON s.course_id = c.id
                """)
                entries = cur.fetchall()

                total_hours = 0.0
                weekly_hours = {}

                for entry in entries:
                    weeks = json.loads(entry['weeks']) if entry['weeks'] else []
                    duration = entry['duration'] if entry['duration'] else 0

                    for week in weeks:
                        if start_week and week < start_week:
                            continue
                        if end_week and week > end_week:
                            continue

                        total_hours += duration
                        weekly_hours[week] = weekly_hours.get(week, 0.0) + duration

                avg_per_week = total_hours / len(weekly_hours) if weekly_hours else 0

                result = {
                    "total_hours": round(total_hours, 2),
                    "weekly_hours": {k: round(v, 2) for k, v in weekly_hours.items()},
                    "average_per_week": round(avg_per_week, 2)
                }

                self.logger.log_message("debug", f"Calculated total hours: {result['total_hours']}")
                return result

        except Exception as e:
            self.logger.log_message("error", f"Failed to calculate total hours: {e}")
            return {"total_hours": 0, "weekly_hours": {}, "average_per_week": 0}

    def get_course_distribution(self) -> Dict:
        """
        Get course distribution by day, teacher, and location.

        Returns:
            Dictionary with distributions by day, teacher, and location
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()

                # By day of week
                cur.execute("""
                    SELECT s.day_of_week, COUNT(*) as count
                    FROM schedule s
                    GROUP BY s.day_of_week
                    ORDER BY s.day_of_week
                """)
                by_day = {row['day_of_week']: row['count'] for row in cur.fetchall()}

                # By teacher
                cur.execute("""
                    SELECT c.teacher, COUNT(DISTINCT s.id) as count
                    FROM courses c
                    LEFT JOIN schedule s ON c.id = s.course_id
                    WHERE c.teacher IS NOT NULL AND c.teacher != ''
                    GROUP BY c.teacher
                    ORDER BY count DESC
                """)
                by_teacher = {row['teacher']: row['count'] for row in cur.fetchall()}

                # By location
                cur.execute("""
                    SELECT c.location, COUNT(DISTINCT s.id) as count
                    FROM courses c
                    LEFT JOIN schedule s ON c.id = s.course_id
                    WHERE c.location IS NOT NULL AND c.location != ''
                    GROUP BY c.location
                    ORDER BY count DESC
                """)
                by_location = {row['location']: row['count'] for row in cur.fetchall()}

                result = {
                    "by_day": by_day,
                    "by_teacher": by_teacher,
                    "by_location": by_location
                }

                self.logger.log_message("debug", f"Calculated course distribution")
                return result

        except Exception as e:
            self.logger.log_message("error", f"Failed to get distribution: {e}")
            return {"by_day": {}, "by_teacher": {}, "by_location": {}}

    def get_attendance_rate(self, course_id: Optional[int] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> Dict:
        """
        Calculate attendance rate.

        Args:
            course_id: Filter by course ID (optional)
            start_date: Filter by start date in YYYY-MM-DD format (optional)
            end_date: Filter by end date in YYYY-MM-DD format (optional)

        Returns:
            Dictionary with attendance statistics
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()

                query = """
                    SELECT
                        COUNT(*) as total_sessions,
                        SUM(CASE WHEN attended = 1 THEN 1 ELSE 0 END) as attended_sessions
                    FROM course_sessions
                    WHERE 1=1
                """
                params = []

                if course_id:
                    query += " AND course_id = ?"
                    params.append(course_id)

                if start_date:
                    query += " AND date >= ?"
                    params.append(start_date)

                if end_date:
                    query += " AND date <= ?"
                    params.append(end_date)

                cur.execute(query, params)
                result = cur.fetchone()

                total = result['total_sessions'] if result['total_sessions'] else 0
                attended = result['attended_sessions'] if result['attended_sessions'] else 0
                rate = (attended / total * 100) if total > 0 else 0

                stats = {
                    "total_sessions": total,
                    "attended_sessions": attended,
                    "absence_sessions": total - attended,
                    "attendance_rate": round(rate, 2)
                }

                self.logger.log_message("debug", f"Calculated attendance rate: {rate:.2f}%")
                return stats

        except Exception as e:
            self.logger.log_message("error", f"Failed to calculate attendance rate: {e}")
            return {
                "total_sessions": 0,
                "attended_sessions": 0,
                "absence_sessions": 0,
                "attendance_rate": 0.0
            }

    def get_weekly_load(self, week_number: Optional[int] = None) -> List[Dict]:
        """
        Get weekly course load.

        Args:
            week_number: Filter by specific week number (optional)

        Returns:
            List of daily course loads
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()

                query = """
                    SELECT
                        s.day_of_week,
                        COUNT(*) as class_count,
                        SUM(CAST((julianday('1970-01-01 ' || s.end_time) -
                                  julianday('1970-01-01 ' || s.start_time)) * 24 AS REAL)) as total_hours
                    FROM schedule s
                    WHERE 1=1
                """
                params = []

                if week_number:
                    query += " AND s.weeks LIKE ?"
                    params.append(f'%{week_number}%')

                query += " GROUP BY s.day_of_week ORDER BY s.day_of_week"

                cur.execute(query, params)
                rows = cur.fetchall()

                result = [
                    {
                        "day_of_week": row['day_of_week'],
                        "class_count": row['class_count'],
                        "total_hours": round(row['total_hours'], 2) if row['total_hours'] else 0
                    }
                    for row in rows
                ]

                self.logger.log_message("debug", f"Retrieved weekly load for week {week_number}")
                return result

        except Exception as e:
            self.logger.log_message("error", f"Failed to get weekly load: {e}")
            return []

    def get_busiest_days(self, limit: int = 5) -> List[Dict]:
        """
        Get busiest days of the week.

        Args:
            limit: Maximum number of days to return

        Returns:
            List of busiest days with statistics
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()

                cur.execute("""
                    SELECT
                        s.day_of_week,
                        COUNT(*) as class_count,
                        SUM(CAST((julianday('1970-01-01 ' || s.end_time) -
                                  julianday('1970-01-01 ' || s.start_time)) * 24 AS REAL)) as total_hours
                    FROM schedule s
                    GROUP BY s.day_of_week
                    ORDER BY class_count DESC, total_hours DESC
                    LIMIT ?
                """, (limit,))

                rows = cur.fetchall()

                result = [
                    {
                        "day_of_week": row['day_of_week'],
                        "class_count": row['class_count'],
                        "total_hours": round(row['total_hours'], 2) if row['total_hours'] else 0
                    }
                    for row in rows
                ]

                self.logger.log_message("debug", f"Retrieved {len(result)} busiest days")
                return result

        except Exception as e:
            self.logger.log_message("error", f"Failed to get busiest days: {e}")
            return []

    def get_time_slot_distribution(self) -> Dict:
        """
        Get distribution of classes by time slot (morning/afternoon/evening).

        Returns:
            Dictionary with counts for each time slot
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()

                cur.execute("""
                    SELECT
                        CASE
                            WHEN CAST(substr(start_time, 1, 2) AS INTEGER) < 12 THEN 'morning'
                            WHEN CAST(substr(start_time, 1, 2) AS INTEGER) < 18 THEN 'afternoon'
                            ELSE 'evening'
                        END as time_slot,
                        COUNT(*) as count
                    FROM schedule
                    GROUP BY time_slot
                """)

                rows = cur.fetchall()

                result = {row['time_slot']: row['count'] for row in rows}

                self.logger.log_message("debug", f"Calculated time slot distribution")
                return result

        except Exception as e:
            self.logger.log_message("error", f"Failed to get time slot distribution: {e}")
            return {}

    def calculate_all_statistics(self, start_week: Optional[int] = None,
                                 end_week: Optional[int] = None) -> Dict:
        """
        Calculate comprehensive statistics.

        Args:
            start_week: Start week number (optional)
            end_week: End week number (optional)

        Returns:
            Dictionary with all statistics
        """
        try:
            self.logger.log_message("info", "Calculating comprehensive statistics")

            return {
                "total_hours": self.get_total_course_hours(start_week, end_week),
                "distribution": self.get_course_distribution(),
                "attendance": self.get_attendance_rate(),
                "weekly_load": self.get_weekly_load(),
                "busiest_days": self.get_busiest_days(),
                "time_slots": self.get_time_slot_distribution()
            }
        except Exception as e:
            self.logger.log_message("error", f"Failed to calculate statistics: {e}")
            return {}

    def get_course_attendance_summary(self, course_id: int) -> Dict:
        """
        Get attendance summary for a specific course.

        Args:
            course_id: Course identifier

        Returns:
            Dictionary with course attendance summary
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()

                # Get course info
                cur.execute("SELECT name, teacher FROM courses WHERE id = ?", (course_id,))
                course = cur.fetchone()

                if not course:
                    self.logger.log_message("error", f"Course {course_id} not found")
                    return {}

                # Get attendance stats
                attendance_stats = self.get_attendance_rate(course_id=course_id)

                # Get recent sessions
                recent_sessions = self.get_attendance_history(
                    course_id=course_id,
                    limit=10
                )

                return {
                    "course_id": course_id,
                    "course_name": course['name'],
                    "teacher": course['teacher'],
                    "statistics": attendance_stats,
                    "recent_sessions": recent_sessions
                }

        except Exception as e:
            self.logger.log_message("error", f"Failed to get course attendance summary: {e}")
            return {}
