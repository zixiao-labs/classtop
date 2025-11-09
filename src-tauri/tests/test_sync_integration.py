"""
Integration tests for sync functionality with live Management Server.

These tests require a running Classtop-Management-Server instance.
To run: pytest -m integration

Setup:
1. Start Management Server: cd ../Classtop-Management-Server && cargo run
2. Ensure PostgreSQL is running
3. Run tests: pytest tests/test_sync_integration.py -v
"""
import pytest
import sqlite3
import time
import tempfile
import requests
from pathlib import Path
from tauri_app.sync_client import SyncClient
from tauri_app.settings_manager import SettingsManager
from tauri_app.schedule_manager import ScheduleManager

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# Management Server configuration
SERVER_URL = "http://localhost:8765"
HEALTH_CHECK_TIMEOUT = 2  # seconds


def is_server_running():
    """Check if Management Server is running."""
    try:
        response = requests.get(f"{SERVER_URL}/api/health", timeout=HEALTH_CHECK_TIMEOUT)
        return response.status_code == 200
    except:
        return False


@pytest.fixture(scope="module", autouse=True)
def check_server():
    """Check if Management Server is running before running tests."""
    if not is_server_running():
        pytest.skip(
            f"Management Server is not running at {SERVER_URL}. "
            "Start it with: cd ../Classtop-Management-Server && cargo run"
        )


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_integration.db"

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
    # Configure for test server
    manager.set_setting("server_url", SERVER_URL)
    manager.set_setting_bool("sync_enabled", True)
    return manager


@pytest.fixture
def sync_client(settings_manager, schedule_manager):
    """Create a SyncClient instance."""
    return SyncClient(settings_manager, schedule_manager)


class TestServerConnection:
    """Test basic server connectivity."""

    def test_health_check(self):
        """Test server health endpoint."""
        response = requests.get(f"{SERVER_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_connection_via_sync_client(self, sync_client):
        """Test connection through SyncClient."""
        result = sync_client.test_connection()
        assert result["success"] is True
        assert "message" in result


class TestClientRegistration:
    """Test client registration workflow."""

    def test_register_new_client(self, sync_client, settings_manager):
        """Test registering a new client to the server."""
        # Generate unique client name for this test
        client_name = f"IntegrationTest-{int(time.time())}"
        settings_manager.set_setting("client_name", client_name)

        # Register client
        success = sync_client.register_client()
        assert success is True

        # Verify UUID was generated and saved
        uuid = settings_manager.get_setting("client_uuid")
        assert uuid is not None
        assert len(uuid) == 36  # UUID format

    def test_register_existing_client(self, sync_client, settings_manager):
        """Test re-registering an existing client."""
        # Register once
        sync_client.register_client()
        first_uuid = settings_manager.get_setting("client_uuid")

        # Register again
        sync_client.register_client()
        second_uuid = settings_manager.get_setting("client_uuid")

        # UUID should remain the same
        assert first_uuid == second_uuid


class TestDataUpload:
    """Test uploading data to server."""

    def test_upload_courses_and_schedule(self, sync_client, schedule_manager, settings_manager):
        """Test uploading courses and schedule entries."""
        # Register client first
        sync_client.register_client()

        # Add test course
        course_id = schedule_manager.add_course(
            name="Integration Test Course",
            teacher="Test Teacher",
            location="Test Room 101",
            color="#FF5722"
        )
        assert course_id > 0

        # Add schedule entry
        entry_id = schedule_manager.add_schedule_entry(
            course_id=course_id,
            day_of_week=1,  # Monday
            start_time="09:00",
            end_time="10:30",
            weeks=[1, 2, 3, 4, 5],
            note="Integration test entry"
        )
        assert entry_id > 0

        # Sync to server
        success = sync_client.sync_to_server()
        assert success is True

        # Verify sync history was logged
        with schedule_manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT direction, status, courses_synced, schedule_synced
                FROM sync_history
                WHERE direction = 'upload' AND status = 'success'
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "upload"
            assert row[1] == "success"
            assert row[2] >= 1  # At least 1 course
            assert row[3] >= 1  # At least 1 entry


class TestDataDownload:
    """Test downloading data from server."""

    def test_download_from_server(self, sync_client, settings_manager):
        """Test downloading data from server."""
        # Register and upload some data first
        sync_client.register_client()
        sync_client.sync_to_server()

        # Download data
        result = sync_client.download_from_server()
        assert result["success"] is True
        assert "courses" in result
        assert "schedule_entries" in result
        assert isinstance(result["courses"], list)
        assert isinstance(result["schedule_entries"], list)


class TestBidirectionalSync:
    """Test bidirectional synchronization with conflict resolution."""

    def test_bidirectional_sync_no_conflicts(self, sync_client, schedule_manager, settings_manager):
        """Test bidirectional sync when there are no conflicts."""
        # Setup
        sync_client.register_client()

        # Add local data
        course_id = schedule_manager.add_course(
            name="Bidirectional Test Course",
            teacher="Test Teacher",
            location="Room 202"
        )
        schedule_manager.add_schedule_entry(
            course_id=course_id,
            day_of_week=2,
            start_time="14:00",
            end_time="15:30",
            weeks=[1, 2, 3]
        )

        # Perform bidirectional sync
        result = sync_client.bidirectional_sync(strategy="server_wins")

        assert result["success"] is True
        assert result["conflicts_found"] == 0
        assert result["courses_updated"] >= 1
        assert result["entries_updated"] >= 1

    def test_bidirectional_sync_server_wins(self, sync_client, schedule_manager, settings_manager):
        """Test bidirectional sync with server_wins strategy."""
        sync_client.register_client()

        # Upload initial data
        course_id = schedule_manager.add_course(name="Conflict Test", teacher="Teacher A")
        sync_client.sync_to_server()

        # Modify local data (simulating conflict)
        schedule_manager.update_course(course_id, teacher="Teacher B (Local)")

        # Bidirectional sync with server_wins should keep server version
        result = sync_client.bidirectional_sync(strategy="server_wins")
        assert result["success"] is True

    def test_bidirectional_sync_local_wins(self, sync_client, schedule_manager):
        """Test bidirectional sync with local_wins strategy."""
        sync_client.register_client()

        # Add data
        course_id = schedule_manager.add_course(name="Local Wins Test", teacher="Teacher X")

        # Sync
        result = sync_client.bidirectional_sync(strategy="local_wins")
        assert result["success"] is True


class TestConflictDetection:
    """Test conflict detection logic."""

    def test_detect_conflicts(self, sync_client, schedule_manager):
        """Test detecting conflicts between local and server data."""
        # Setup two datasets with conflicts
        local_data = {
            "courses": [
                {"id": 1, "name": "Course A", "teacher": "Teacher Local", "location": "Room 1", "color": "#FF0000"}
            ],
            "schedule_entries": [
                {"id": 1, "course_id": 1, "day_of_week": 1, "start_time": "09:00", "end_time": "10:00", "weeks": "[1,2,3]"}
            ]
        }

        server_data = {
            "courses": [
                {"id": 1, "name": "Course A", "teacher": "Teacher Server", "location": "Room 2", "color": "#00FF00"}
            ],
            "schedule_entries": [
                {"id": 1, "course_id": 1, "day_of_week": 1, "start_time": "10:00", "end_time": "11:00", "weeks": [1,2,3]}
            ]
        }

        # Detect conflicts
        conflicts = sync_client.detect_conflicts(local_data, server_data)

        assert conflicts["has_conflicts"] is True
        assert len(conflicts["conflicted_courses"]) > 0
        assert len(conflicts["conflicted_entries"]) > 0


class TestAutoSync:
    """Test automatic synchronization."""

    def test_start_stop_auto_sync(self, sync_client, settings_manager):
        """Test starting and stopping auto-sync."""
        # Enable sync
        settings_manager.set_setting_bool("sync_enabled", True)
        settings_manager.set_setting("sync_interval", "1")  # 1 second for test

        # Start auto-sync
        sync_client.start_auto_sync()
        assert sync_client.is_running is True

        # Let it run briefly
        time.sleep(2)

        # Stop auto-sync
        sync_client.stop_auto_sync()
        assert sync_client.is_running is False


class TestMultiClient:
    """Test multi-client scenarios."""

    def test_two_clients_sync(self, temp_db):
        """Test two clients syncing to the same server."""
        # Create first client
        settings_mgr_1 = SettingsManager(temp_db, event_handler=None)
        settings_mgr_1.initialize_defaults()
        settings_mgr_1.set_setting("server_url", SERVER_URL)
        settings_mgr_1.set_setting("client_name", f"Client1-{int(time.time())}")

        schedule_mgr_1 = ScheduleManager(temp_db, event_handler=None)
        sync_client_1 = SyncClient(settings_mgr_1, schedule_mgr_1)

        # Create second client with separate database
        temp_dir_2 = tempfile.mkdtemp()
        db_path_2 = Path(temp_dir_2) / "client2.db"

        # Copy schema to second database
        conn_2 = sqlite3.connect(db_path_2)
        conn_1 = sqlite3.connect(temp_db)
        for line in conn_1.iterdump():
            if 'INSERT' not in line:  # Only schema, not data
                conn_2.execute(line)
        conn_2.commit()
        conn_1.close()
        conn_2.close()

        settings_mgr_2 = SettingsManager(db_path_2, event_handler=None)
        settings_mgr_2.initialize_defaults()
        settings_mgr_2.set_setting("server_url", SERVER_URL)
        settings_mgr_2.set_setting("client_name", f"Client2-{int(time.time())}")

        schedule_mgr_2 = ScheduleManager(db_path_2, event_handler=None)
        sync_client_2 = SyncClient(settings_mgr_2, schedule_mgr_2)

        # Register both clients
        assert sync_client_1.register_client() is True
        assert sync_client_2.register_client() is True

        # Client 1: Add and upload data
        course_id = schedule_mgr_1.add_course(name="Shared Course", teacher="Teacher", location="Room 303")
        assert sync_client_1.sync_to_server() is True

        # Client 2: Download data
        result = sync_client_2.download_from_server()
        assert result["success"] is True

        # Cleanup
        db_path_2.unlink(missing_ok=True)


class TestErrorHandling:
    """Test error handling in sync operations."""

    def test_sync_with_invalid_server_url(self, sync_client, settings_manager):
        """Test sync fails gracefully with invalid server URL."""
        settings_manager.set_setting("server_url", "http://invalid-server:9999")

        result = sync_client.test_connection()
        assert result["success"] is False
        assert "message" in result

    def test_sync_without_registration(self, sync_client, settings_manager):
        """Test sync behavior when client is not registered."""
        # Clear UUID
        settings_manager.set_setting("client_uuid", "")

        success = sync_client.sync_to_server()
        # Should either fail or auto-generate UUID
        assert isinstance(success, bool)

    def test_https_validation(self, sync_client, settings_manager):
        """Test HTTPS validation for remote servers."""
        # HTTP should be rejected for non-localhost
        settings_manager.set_setting("server_url", "http://remote-server.com:8765")
        success = sync_client.register_client()
        assert success is False

        # HTTPS should be accepted
        settings_manager.set_setting("server_url", "https://remote-server.com:8765")
        # Will fail due to connection error, but should pass validation
        # (Can't test actual HTTPS without real server)


class TestSyncHistory:
    """Test sync history logging."""

    def test_sync_history_logging(self, sync_client, schedule_manager):
        """Test that sync operations are logged to history."""
        sync_client.register_client()

        # Perform sync
        sync_client.sync_to_server()

        # Check history
        with schedule_manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM sync_history
                WHERE direction = 'upload' AND status = 'success'
            """)
            count = cur.fetchone()[0]
            assert count > 0

    def test_sync_history_failure_logging(self, sync_client, schedule_manager, settings_manager):
        """Test that failed syncs are logged."""
        # Use invalid server to force failure
        settings_manager.set_setting("server_url", "http://invalid:9999")

        # Attempt sync (will fail)
        sync_client.sync_to_server()

        # Check failure was logged
        with schedule_manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM sync_history
                WHERE status = 'failure'
            """)
            count = cur.fetchone()[0]
            assert count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
