import sqlite3
from pathlib import Path
from typing import Optional, Dict, List
from . import logger

# Store DB in user home directory under .classtop
APP_DIR = Path.home() / ".classtop"
APP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DIR / "app_config.db"

# Global managers
schedule_manager = None
settings_manager = None
camera_manager = None
audio_manager = None
sync_client = None


def init_db() -> None:
    """Initialize database and create tables."""
    logger.log_message("info", "Initializing database")

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()

        # Settings table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        logger.log_message("debug", "Settings table ready")

        # Courses table - stores course information
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                teacher TEXT,
                location TEXT,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        logger.log_message("debug", "Courses table ready")

        # Schedule table - stores weekly schedule
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL CHECK (day_of_week >= 1 AND day_of_week <= 7),
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                weeks TEXT,  -- JSON array of week numbers
                note TEXT,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            )
            """
        )
        logger.log_message("debug", "Schedule table ready")

        # Current week settings with semester start date
        cur.execute(
            """
            INSERT OR IGNORE INTO settings(key, value)
            VALUES('current_week', '1'), ('total_weeks', '20'), ('semester_start_date', '')
            """
        )

        conn.commit()
        logger.log_message("info", "Database initialized successfully")

    except Exception as e:
        logger.log_message("error", f"Error initializing database: {e}")
        raise
    finally:
        conn.close()


def set_schedule_manager(manager) -> None:
    """Set the global schedule manager instance."""
    global schedule_manager
    schedule_manager = manager
    logger.log_message("info", "Schedule manager instance set")


def set_settings_manager(manager) -> None:
    """Set the global settings manager instance."""
    global settings_manager
    settings_manager = manager
    logger.log_message("info", "Settings manager instance set")


def set_camera_manager(manager) -> None:
    """Set the global camera manager instance."""
    global camera_manager
    camera_manager = manager
    logger.log_message("info", "Camera manager instance set")


def set_audio_manager(manager) -> None:
    """Set the global audio manager instance."""
    global audio_manager
    audio_manager = manager
    logger.log_message("info", "Audio manager instance set")


def set_sync_client(client) -> None:
    """Set the global sync client instance."""
    global sync_client
    sync_client = client
    logger.log_message("info", "Sync client instance set")


# Configuration management functions - delegated to settings manager
def set_config(key: str, value: str) -> None:
    """Set a configuration value."""
    global settings_manager
    if settings_manager:
        settings_manager.set_setting(key, value)
    else:
        # Fallback to direct database access if manager not initialized
        logger.log_message("warning", "Settings manager not initialized, using direct DB access")
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
            conn.commit()
            logger.log_message("info", f"Config set: {key} = {value}")
        except Exception as e:
            logger.log_message("error", f"Error setting config for key '{key}': {e}")
        finally:
            conn.close()


def get_config(key: str) -> Optional[str]:
    """Get a configuration value."""
    global settings_manager
    if settings_manager:
        return settings_manager.get_setting(key)
    else:
        # Fallback to direct database access
        logger.log_message("warning", "Settings manager not initialized, using direct DB access")
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.log_message("error", f"Error getting config for key '{key}': {e}")
            return None
        finally:
            conn.close()


def list_configs() -> Dict[str, str]:
    """List all configuration values."""
    global settings_manager
    if settings_manager:
        return settings_manager.get_all_settings()
    else:
        # Fallback to direct database access
        logger.log_message("warning", "Settings manager not initialized, using direct DB access")
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute("SELECT key, value FROM settings")
            return {k: v for k, v in cur.fetchall()}
        except Exception as e:
            logger.log_message("error", f"Error listing configs: {e}")
            return {}
        finally:
            conn.close()


# Course management functions - delegated to schedule manager
def add_course(name: str, teacher: Optional[str] = None,
               location: Optional[str] = None, color: Optional[str] = None) -> int:
    """Add a new course and return its ID."""
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return -1
    return schedule_manager.add_course(name, teacher, location, color)


def get_courses() -> List[Dict]:
    """Get all courses."""
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return []
    return schedule_manager.get_courses()


def update_course(course_id: int, **kwargs) -> bool:
    """Update course information."""
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return False
    return schedule_manager.update_course(course_id, **kwargs)


def delete_course(course_id: int) -> bool:
    """Delete a course and all its schedule entries."""
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return False
    return schedule_manager.delete_course(course_id)


# Schedule management functions - delegated to schedule manager
def add_schedule_entry(course_id: int, day_of_week: int, start_time: str, end_time: str,
                      weeks: Optional[List[int]] = None, note: Optional[str] = None) -> int:
    """Add a schedule entry."""
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return -1
    return schedule_manager.add_schedule_entry(course_id, day_of_week, start_time, end_time, weeks, note)


def get_schedule(week: Optional[int] = None) -> List[Dict]:
    """Get schedule for a specific week or all schedules."""
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return []
    return schedule_manager.get_schedule(week)


def delete_schedule_entry(entry_id: int) -> bool:
    """Delete a schedule entry."""
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return False
    return schedule_manager.delete_schedule_entry(entry_id)


def get_calculated_week_number() -> int:
    """Get current week number, either from manual setting or calculated from semester start."""
    # First check if semester start date is configured
    semester_start = get_config("semester_start_date")

    if semester_start and semester_start.strip():
        # Calculate week from semester start date
        global schedule_manager
        if schedule_manager:
            week_num = schedule_manager.calculate_week_number(semester_start)
            return week_num

    # Fall back to manually set current week
    current_week = get_config("current_week")
    return int(current_week) if current_week else 1


def get_schedule_by_day(day_of_week: int, week: Optional[int] = None) -> List[Dict]:
    """Get all classes for a specific day."""
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return []

    return schedule_manager.get_schedule_by_day(day_of_week, week)


def get_schedule_for_week(week: Optional[int] = None) -> List[Dict]:
    """Get all classes for the entire week."""
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return []

    return schedule_manager.get_schedule_for_week(week)


def get_current_class() -> Optional[Dict]:
    """
    DEPRECATED: Use get_schedule_by_day() and calculate on frontend.
    Kept for backward compatibility.
    """
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return None

    from datetime import datetime
    now = datetime.now()
    day_of_week = now.isoweekday()
    current_time = now.strftime("%H:%M")
    week_num = get_calculated_week_number()

    classes = schedule_manager.get_schedule_by_day(day_of_week, week_num)
    for cls in classes:
        if cls["start_time"] <= current_time <= cls["end_time"]:
            return cls
    return None


def get_next_class() -> Optional[Dict]:
    """
    DEPRECATED: Use get_schedule_by_day() and calculate on frontend.
    Kept for backward compatibility.
    """
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return None

    from datetime import datetime
    now = datetime.now()
    day_of_week = now.isoweekday()
    current_time = now.strftime("%H:%M")
    week_num = get_calculated_week_number()

    classes = schedule_manager.get_schedule_by_day(day_of_week, week_num)
    for cls in classes:
        if cls["start_time"] > current_time:
            return cls

    for day_offset in range(1, 8):
        next_day = ((day_of_week - 1 + day_offset) % 7) + 1
        classes = schedule_manager.get_schedule_by_day(next_day, week_num)
        if classes:
            return classes[0]
    return None


def get_last_class() -> Optional[Dict]:
    """
    DEPRECATED: Use get_schedule_by_day() and calculate on frontend.
    Kept for backward compatibility.
    """
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return None

    from datetime import datetime
    now = datetime.now()
    day_of_week = now.isoweekday()
    current_time = now.strftime("%H:%M")
    week_num = get_calculated_week_number()

    classes = schedule_manager.get_schedule_by_day(day_of_week, week_num)
    last_class = None
    for cls in classes:
        if cls["end_time"] <= current_time:
            last_class = cls
        else:
            break
    return last_class


def get_schedule_statistics() -> Dict:
    """Get schedule statistics."""
    global schedule_manager
    if not schedule_manager:
        logger.log_message("error", "Schedule manager not initialized")
        return {}
    return schedule_manager.get_statistics()