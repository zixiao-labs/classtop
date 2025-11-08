"""
Unit tests for the database layer (db.py).
"""
import sqlite3
import tempfile
from pathlib import Path
import pytest

from tauri_app import db


class TestDatabaseInitialization:
    """Tests for database initialization."""

    def test_init_db_creates_tables(self, temp_db: str):
        """Test that init_db creates all required tables."""
        # Connect and verify tables exist
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()

        # Check settings table
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
        )
        assert cur.fetchone() is not None, "Settings table should exist"

        # Check courses table
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='courses'"
        )
        assert cur.fetchone() is not None, "Courses table should exist"

        # Check schedule table
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schedule'"
        )
        assert cur.fetchone() is not None, "Schedule table should exist"

        conn.close()

    def test_init_db_creates_default_settings(self, temp_db: str):
        """Test that init_db creates default configuration settings."""
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()

        # Check default settings
        cur.execute("SELECT key, value FROM settings")
        settings = {row[0]: row[1] for row in cur.fetchall()}

        assert "current_week" in settings, "current_week should be initialized"
        assert settings["current_week"] == "1", "current_week default should be 1"

        assert "total_weeks" in settings, "total_weeks should be initialized"
        assert settings["total_weeks"] == "20", "total_weeks default should be 20"

        assert (
            "semester_start_date" in settings
        ), "semester_start_date should be initialized"
        assert (
            settings["semester_start_date"] == ""
        ), "semester_start_date default should be empty"

        conn.close()

    def test_courses_table_constraints(self, temp_db: str):
        """Test courses table constraints."""
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()

        # name should be NOT NULL
        with pytest.raises(sqlite3.IntegrityError):
            cur.execute(
                "INSERT INTO courses (name, teacher) VALUES (NULL, 'Teacher')"
            )

        # Valid insert should succeed
        cur.execute(
            "INSERT INTO courses (name, teacher, location, color) VALUES (?, ?, ?, ?)",
            ("Test Course", "Test Teacher", "Room 101", "#FF5733"),
        )
        conn.commit()

        # Verify insert
        cur.execute("SELECT * FROM courses WHERE name='Test Course'")
        row = cur.fetchone()
        assert row is not None
        assert row[1] == "Test Course"  # name
        assert row[2] == "Test Teacher"  # teacher
        assert row[3] == "Room 101"  # location
        assert row[4] == "#FF5733"  # color

        conn.close()

    def test_schedule_table_constraints(self, temp_db: str):
        """Test schedule table constraints and foreign key relationships."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()

        # Create a course first
        cur.execute(
            "INSERT INTO courses (name) VALUES ('Test Course')"
        )
        course_id = cur.lastrowid

        # Valid schedule entry
        cur.execute(
            "INSERT INTO schedule (course_id, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?)",
            (course_id, 1, "09:00", "10:30"),
        )
        conn.commit()

        # Invalid day_of_week (must be 1-7)
        with pytest.raises(sqlite3.IntegrityError):
            cur.execute(
                "INSERT INTO schedule (course_id, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?)",
                (course_id, 0, "09:00", "10:30"),
            )

        with pytest.raises(sqlite3.IntegrityError):
            cur.execute(
                "INSERT INTO schedule (course_id, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?)",
                (course_id, 8, "09:00", "10:30"),
            )

        # Foreign key constraint should be enforced
        # Note: SQLite foreign keys need to be explicitly enabled
        with pytest.raises(sqlite3.IntegrityError):
            cur.execute(
                "INSERT INTO schedule (course_id, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?)",
                (9999, 1, "09:00", "10:30"),
            )

        conn.close()

    def test_cascade_delete(self, temp_db: str):
        """Test that deleting a course cascades to schedule entries."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()

        # Create a course
        cur.execute("INSERT INTO courses (name) VALUES ('Test Course')")
        course_id = cur.lastrowid

        # Create schedule entries
        for day in range(1, 6):
            cur.execute(
                "INSERT INTO schedule (course_id, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?)",
                (course_id, day, "09:00", "10:30"),
            )
        conn.commit()

        # Verify schedule entries exist
        cur.execute("SELECT COUNT(*) FROM schedule WHERE course_id=?", (course_id,))
        assert cur.fetchone()[0] == 5

        # Delete the course
        cur.execute("DELETE FROM courses WHERE id=?", (course_id,))
        conn.commit()

        # Verify schedule entries are also deleted (CASCADE)
        cur.execute("SELECT COUNT(*) FROM schedule WHERE course_id=?", (course_id,))
        assert cur.fetchone()[0] == 0

        conn.close()


class TestConfigurationManagement:
    """Tests for configuration management functions."""

    def test_set_and_get_config(self, temp_db: str, mocker):
        """Test setting and getting configuration values."""
        # Mock the logger to avoid actual logging
        mocker.patch("tauri_app.db.logger.log_message")

        # Test direct DB access (without manager)
        db.settings_manager = None
        db.DB_PATH = temp_db

        # Set a config value
        db.set_config("test_key", "test_value")

        # Get the config value
        value = db.get_config("test_key")
        assert value == "test_value"

    def test_get_nonexistent_config(self, temp_db: str, mocker):
        """Test getting a non-existent configuration value."""
        mocker.patch("tauri_app.db.logger.log_message")

        db.settings_manager = None
        db.DB_PATH = temp_db

        value = db.get_config("nonexistent_key")
        assert value is None

    def test_update_existing_config(self, temp_db: str, mocker):
        """Test updating an existing configuration value."""
        mocker.patch("tauri_app.db.logger.log_message")

        db.settings_manager = None
        db.DB_PATH = temp_db

        # Set initial value
        db.set_config("update_test", "initial")
        assert db.get_config("update_test") == "initial"

        # Update value
        db.set_config("update_test", "updated")
        assert db.get_config("update_test") == "updated"

    def test_list_all_configs(self, temp_db: str, mocker):
        """Test listing all configuration values."""
        mocker.patch("tauri_app.db.logger.log_message")

        db.settings_manager = None
        db.DB_PATH = temp_db

        # Set multiple configs
        db.set_config("key1", "value1")
        db.set_config("key2", "value2")
        db.set_config("key3", "value3")

        # List all configs
        configs = db.list_configs()

        assert isinstance(configs, dict)
        assert "key1" in configs
        assert configs["key1"] == "value1"
        assert "key2" in configs
        assert configs["key2"] == "value2"
        assert "key3" in configs
        assert configs["key3"] == "value3"


class TestWeekCalculation:
    """Tests for week number calculation."""

    def test_calculated_week_from_semester_start(self, temp_db: str, mocker):
        """Test week calculation from semester start date."""
        from datetime import datetime, timedelta

        mocker.patch("tauri_app.db.logger.log_message")
        mock_schedule_manager = mocker.MagicMock()

        # Set up a semester start date (e.g., 4 weeks ago)
        start_date = (datetime.now() - timedelta(weeks=4)).strftime("%Y-%m-%d")

        db.settings_manager = None
        db.schedule_manager = mock_schedule_manager
        db.DB_PATH = temp_db

        # Set semester start date
        db.set_config("semester_start_date", start_date)

        # Mock the calculate_week_number method
        mock_schedule_manager.calculate_week_number.return_value = 5

        # Get calculated week
        week = db.get_calculated_week_number()

        # Verify that calculate_week_number was called
        mock_schedule_manager.calculate_week_number.assert_called_once_with(
            start_date
        )
        assert week == 5

    def test_manual_week_fallback(self, temp_db: str, mocker):
        """Test fallback to manual week setting when semester start is not configured."""
        mocker.patch("tauri_app.db.logger.log_message")

        db.settings_manager = None
        db.schedule_manager = None
        db.DB_PATH = temp_db

        # Set manual week (no semester_start_date)
        db.set_config("semester_start_date", "")
        db.set_config("current_week", "10")

        # Get calculated week (should fall back to manual)
        week = db.get_calculated_week_number()
        assert week == 10


class TestManagerSetters:
    """Tests for manager setter functions."""

    def test_set_schedule_manager(self, mocker):
        """Test setting the schedule manager."""
        mocker.patch("tauri_app.db.logger.log_message")

        mock_manager = mocker.MagicMock()
        db.set_schedule_manager(mock_manager)

        assert db.schedule_manager is mock_manager

    def test_set_settings_manager(self, mocker):
        """Test setting the settings manager."""
        mocker.patch("tauri_app.db.logger.log_message")

        mock_manager = mocker.MagicMock()
        db.set_settings_manager(mock_manager)

        assert db.settings_manager is mock_manager

    def test_set_camera_manager(self, mocker):
        """Test setting the camera manager."""
        mocker.patch("tauri_app.db.logger.log_message")

        mock_manager = mocker.MagicMock()
        db.set_camera_manager(mock_manager)

        assert db.camera_manager is mock_manager

    def test_set_sync_client(self, mocker):
        """Test setting the sync client."""
        mocker.patch("tauri_app.db.logger.log_message")

        mock_client = mocker.MagicMock()
        db.set_sync_client(mock_client)

        assert db.sync_client is mock_client
