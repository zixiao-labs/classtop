"""
Pytest configuration and shared fixtures for ClassTop tests.
"""
import os
import sys
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator
import pytest

# Add the python module to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from tauri_app import db, schedule_manager, settings_manager


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """
    Create a temporary SQLite database for testing.

    Yields:
        Path to the temporary database file
    """
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Initialize the database directly
    conn = sqlite3.connect(db_path)
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

        # Courses table
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

        # Schedule table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL CHECK (day_of_week >= 1 AND day_of_week <= 7),
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                weeks TEXT,
                note TEXT,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            )
            """
        )

        # Default settings
        cur.execute(
            """
            INSERT OR IGNORE INTO settings(key, value)
            VALUES('current_week', '1'), ('total_weeks', '20'), ('semester_start_date', '')
            """
        )

        conn.commit()
    finally:
        conn.close()

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def db_connection(temp_db: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Create a database connection to the temporary test database.

    Args:
        temp_db: Path to the temporary database

    Yields:
        SQLite connection object
    """
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row

    yield conn

    conn.close()


@pytest.fixture
def mock_event_handler(mocker):
    """
    Mock the EventHandler to prevent actual event emissions during tests.

    Args:
        mocker: pytest-mock mocker fixture

    Returns:
        Mocked EventHandler instance
    """
    mock_handler = mocker.MagicMock()
    mock_handler.emit = mocker.AsyncMock()
    return mock_handler


@pytest.fixture
def sample_course() -> dict:
    """
    Sample course data for testing.

    Returns:
        Dictionary containing course data
    """
    return {
        "name": "Test Course",
        "teacher": "Test Teacher",
        "location": "Room 101",
        "color": "#FF5733",
    }


@pytest.fixture
def sample_schedule_entry() -> dict:
    """
    Sample schedule entry data for testing.

    Returns:
        Dictionary containing schedule entry data
    """
    return {
        "day_of_week": 1,  # Monday
        "start_time": "09:00",
        "end_time": "10:30",
        "weeks": [1, 2, 3, 4, 5, 6, 7, 8],
    }


@pytest.fixture
def initialized_schedule_manager(temp_db: str, mock_event_handler):
    """
    Initialize a ScheduleManager with a temporary database.

    Args:
        temp_db: Path to the temporary database
        mock_event_handler: Mocked EventHandler

    Returns:
        Initialized ScheduleManager instance
    """
    manager = schedule_manager.ScheduleManager(temp_db)
    manager.event_handler = mock_event_handler
    return manager


@pytest.fixture
def initialized_settings_manager(temp_db: str, mock_event_handler):
    """
    Initialize a SettingsManager with a temporary database.

    Args:
        temp_db: Path to the temporary database
        mock_event_handler: Mocked EventHandler

    Returns:
        Initialized SettingsManager instance
    """
    manager = settings_manager.SettingsManager(temp_db, mock_event_handler)
    manager.initialize_defaults()  # Initialize default settings
    return manager


@pytest.fixture
def skip_on_non_windows():
    """
    Skip tests on non-Windows platforms.
    """
    import platform

    if platform.system() != "Windows":
        pytest.skip("This test only runs on Windows")
