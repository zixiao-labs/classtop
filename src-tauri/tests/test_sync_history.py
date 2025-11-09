"""
Test sync history tracking functionality
"""
import pytest
import sqlite3
from pathlib import Path
import tempfile
from tauri_app.sync_client import SyncClient
from tauri_app.settings_manager import SettingsManager
from tauri_app.schedule_manager import ScheduleManager
from tauri_app import db


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_sync_history.db"

    # Initialize database schema
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

        # Sync history table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                direction TEXT CHECK(direction IN ('upload', 'download', 'bidirectional')) NOT NULL,
                status TEXT CHECK(status IN ('success', 'failure', 'conflict')) NOT NULL,
                message TEXT,
                courses_synced INTEGER DEFAULT 0,
                schedule_synced INTEGER DEFAULT 0,
                conflicts_found INTEGER DEFAULT 0
            )
            """
        )

        conn.commit()
    finally:
        conn.close()

    yield db_path

    # Cleanup
    db_path.unlink(missing_ok=True)


@pytest.fixture
def schedule_manager(temp_db):
    """Create a ScheduleManager instance."""
    manager = ScheduleManager(temp_db, event_handler=None)
    return manager


@pytest.fixture
def settings_manager(temp_db):
    """Create a SettingsManager instance."""
    manager = SettingsManager(temp_db, event_handler=None)
    manager.initialize_defaults()
    return manager


@pytest.fixture
def sync_client(settings_manager, schedule_manager):
    """Create a SyncClient instance."""
    return SyncClient(settings_manager, schedule_manager)


def test_sync_history_table_created(temp_db):
    """Test that sync_history table is created correctly."""
    conn = sqlite3.connect(temp_db)
    try:
        cur = conn.cursor()

        # Check table exists
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sync_history'"
        )
        assert cur.fetchone() is not None, "sync_history table should exist"

        # Check columns
        cur.execute("PRAGMA table_info(sync_history)")
        columns = {row[1]: row[2] for row in cur.fetchall()}

        expected_columns = {
            'id': 'INTEGER',
            'timestamp': 'TIMESTAMP',
            'direction': 'TEXT',
            'status': 'TEXT',
            'message': 'TEXT',
            'courses_synced': 'INTEGER',
            'schedule_synced': 'INTEGER',
            'conflicts_found': 'INTEGER'
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column {col_name} should exist"
            assert columns[col_name] == col_type, f"Column {col_name} should be {col_type}"

    finally:
        conn.close()


def test_log_sync_history(sync_client, temp_db):
    """Test logging sync history."""
    # Log a successful upload
    sync_client._log_sync_history(
        direction="upload",
        status="success",
        message="Test upload sync",
        courses_synced=5,
        schedule_synced=10,
        conflicts_found=0
    )

    # Verify the log was saved
    conn = sqlite3.connect(temp_db)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sync_history ORDER BY timestamp DESC LIMIT 1")
        row = cur.fetchone()

        assert row is not None, "Sync history entry should be created"
        assert row[2] == "upload", "Direction should be upload"
        assert row[3] == "success", "Status should be success"
        assert row[4] == "Test upload sync", "Message should match"
        assert row[5] == 5, "courses_synced should be 5"
        assert row[6] == 10, "schedule_synced should be 10"
        assert row[7] == 0, "conflicts_found should be 0"

    finally:
        conn.close()


def test_log_sync_history_with_conflicts(sync_client, temp_db):
    """Test logging sync history with conflicts."""
    # Log a bidirectional sync with conflicts
    sync_client._log_sync_history(
        direction="bidirectional",
        status="conflict",
        message="Sync with conflicts resolved",
        courses_synced=8,
        schedule_synced=15,
        conflicts_found=3
    )

    # Verify the log
    conn = sqlite3.connect(temp_db)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sync_history WHERE direction='bidirectional'")
        row = cur.fetchone()

        assert row is not None
        assert row[3] == "conflict", "Status should be conflict"
        assert row[7] == 3, "conflicts_found should be 3"

    finally:
        conn.close()


def test_log_sync_history_failure(sync_client, temp_db):
    """Test logging failed sync."""
    # Log a failed download
    sync_client._log_sync_history(
        direction="download",
        status="failure",
        message="Connection timeout",
        courses_synced=0,
        schedule_synced=0,
        conflicts_found=0
    )

    # Verify the log
    conn = sqlite3.connect(temp_db)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sync_history WHERE status='failure'")
        row = cur.fetchone()

        assert row is not None
        assert row[2] == "download", "Direction should be download"
        assert row[4] == "Connection timeout", "Message should match"
        assert row[5] == 0, "courses_synced should be 0"

    finally:
        conn.close()


def test_multiple_sync_history_entries(sync_client, temp_db):
    """Test multiple sync history entries."""
    # Log multiple syncs
    sync_client._log_sync_history(
        direction="upload",
        status="success",
        message="First sync",
        courses_synced=5,
        schedule_synced=10,
        conflicts_found=0
    )

    sync_client._log_sync_history(
        direction="download",
        status="success",
        message="Second sync",
        courses_synced=3,
        schedule_synced=7,
        conflicts_found=0
    )

    sync_client._log_sync_history(
        direction="bidirectional",
        status="conflict",
        message="Third sync with conflicts",
        courses_synced=8,
        schedule_synced=12,
        conflicts_found=2
    )

    # Verify all entries
    conn = sqlite3.connect(temp_db)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sync_history")
        count = cur.fetchone()[0]
        assert count == 3, "Should have 3 sync history entries"

        # Check ordering (DESC by timestamp)
        cur.execute("SELECT direction FROM sync_history ORDER BY timestamp DESC")
        directions = [row[0] for row in cur.fetchall()]
        assert directions == ["bidirectional", "download", "upload"], "Entries should be ordered by timestamp DESC"

    finally:
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
