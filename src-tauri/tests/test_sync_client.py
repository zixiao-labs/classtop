"""
Unit tests for SyncClient (sync_client.py).
"""
import pytest
import responses
import time
import json
import threading
from unittest.mock import MagicMock, patch

from tauri_app.sync_client import SyncClient


@pytest.fixture
def mock_settings_manager(mocker):
    """Mock SettingsManager."""
    mock_manager = mocker.MagicMock()
    mock_manager.get_setting.return_value = ""
    mock_manager.get_setting_bool.return_value = False
    mock_manager.set_setting.return_value = True
    return mock_manager


@pytest.fixture
def mock_schedule_manager(mocker):
    """Mock ScheduleManager."""
    mock_manager = mocker.MagicMock()
    mock_manager.get_all_courses.return_value = []
    mock_manager.get_all_schedule_entries.return_value = []
    return mock_manager


@pytest.fixture
def sync_client(mock_settings_manager, mock_schedule_manager):
    """Initialize SyncClient with mocked managers."""
    return SyncClient(mock_settings_manager, mock_schedule_manager)


class TestClientRegistration:
    """Tests for client registration."""

    @responses.activate
    def test_register_client_success(self, sync_client, mock_settings_manager):
        """Test successful client registration."""
        # Setup settings
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "test-uuid-123",
            "client_name": "TestClient"
        }.get(key, default)

        # Mock server response
        responses.add(
            responses.POST,
            "http://localhost:8765/api/clients/register",
            json={"success": True, "message": "Client registered"},
            status=200
        )

        # Test
        result = sync_client.register_client()

        assert result is True
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["uuid"] == "test-uuid-123"
        assert request_body["name"] == "TestClient"

    def test_register_client_no_server_url(self, sync_client, mock_settings_manager):
        """Test registration fails when server_url is not configured."""
        mock_settings_manager.get_setting.return_value = ""

        result = sync_client.register_client()

        assert result is False

    @responses.activate
    def test_register_client_server_error(self, sync_client, mock_settings_manager):
        """Test registration fails with server error."""
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "test-uuid-123"
        }.get(key, default)

        responses.add(
            responses.POST,
            "http://localhost:8765/api/clients/register",
            json={"success": False, "message": "Registration failed"},
            status=200
        )

        result = sync_client.register_client()

        assert result is False

    @responses.activate
    def test_register_client_generates_uuid(self, sync_client, mock_settings_manager):
        """Test UUID generation when not set."""
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "",  # Empty UUID triggers generation
            "client_name": "TestClient"
        }.get(key, default)

        responses.add(
            responses.POST,
            "http://localhost:8765/api/clients/register",
            json={"success": True},
            status=200
        )

        result = sync_client.register_client()

        assert result is True
        # Verify set_setting was called to save new UUID
        mock_settings_manager.set_setting.assert_called()
        call_args = [call[0] for call in mock_settings_manager.set_setting.call_args_list]
        assert any("client_uuid" == arg[0] for arg in call_args)


class TestSyncToServer:
    """Tests for syncing data to server."""

    @responses.activate
    def test_sync_success(self, sync_client, mock_settings_manager, mock_schedule_manager):
        """Test successful data sync."""
        # Setup settings
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "test-uuid-123"
        }.get(key, default)

        # Setup schedule data
        mock_schedule_manager.get_all_courses.return_value = [
            {"id": 1, "name": "Math", "teacher": "Mr. Smith", "color": "#FF0000"}
        ]
        mock_schedule_manager.get_all_schedule_entries.return_value = [
            {
                "id": 1,
                "course_id": 1,
                "day_of_week": 1,
                "start_time": "08:00",
                "end_time": "09:30",
                "weeks": "[1,2,3,4]"
            }
        ]

        # Mock server response
        responses.add(
            responses.POST,
            "http://localhost:8765/api/sync",
            json={
                "success": True,
                "data": {"synced_courses": 1, "synced_entries": 1}
            },
            status=200
        )

        # Test
        result = sync_client.sync_to_server()

        assert result is True
        assert len(responses.calls) == 1

        # Verify request data
        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["client_uuid"] == "test-uuid-123"
        assert len(request_body["courses"]) == 1
        assert request_body["courses"][0]["name"] == "Math"
        assert len(request_body["schedule_entries"]) == 1

    def test_sync_no_server_url(self, sync_client, mock_settings_manager):
        """Test sync fails when server_url is not configured."""
        mock_settings_manager.get_setting.return_value = ""

        result = sync_client.sync_to_server()

        assert result is False

    def test_sync_no_client_uuid(self, sync_client, mock_settings_manager):
        """Test sync fails when client_uuid is not configured."""
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": ""
        }.get(key, default)

        result = sync_client.sync_to_server()

        assert result is False

    @responses.activate
    def test_sync_server_error(self, sync_client, mock_settings_manager, mock_schedule_manager):
        """Test sync handles server errors."""
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "test-uuid-123"
        }.get(key, default)

        mock_schedule_manager.get_all_courses.return_value = []
        mock_schedule_manager.get_all_schedule_entries.return_value = []

        responses.add(
            responses.POST,
            "http://localhost:8765/api/sync",
            json={"success": False, "message": "Sync failed"},
            status=200
        )

        result = sync_client.sync_to_server()

        assert result is False


class TestConnectionTest:
    """Tests for testing server connection."""

    @responses.activate
    def test_connection_success(self, sync_client, mock_settings_manager):
        """Test successful connection test."""
        mock_settings_manager.get_setting.return_value = "http://localhost:8765"

        responses.add(
            responses.GET,
            "http://localhost:8765/api/health",
            json={"success": True, "data": {"version": "1.0"}},
            status=200
        )

        result = sync_client.test_connection()

        assert result["success"] is True
        assert result["message"] == "连接成功"
        assert "data" in result

    def test_connection_no_server_url(self, sync_client, mock_settings_manager):
        """Test connection fails when server_url is not configured."""
        mock_settings_manager.get_setting.return_value = ""

        result = sync_client.test_connection()

        assert result["success"] is False
        assert "未配置" in result["message"]

    @responses.activate
    def test_connection_timeout(self, sync_client, mock_settings_manager):
        """Test connection handles timeout."""
        mock_settings_manager.get_setting.return_value = "http://localhost:8765"

        responses.add(
            responses.GET,
            "http://localhost:8765/api/health",
            body=responses.ConnectionError("Timeout")
        )

        result = sync_client.test_connection()

        assert result["success"] is False
        assert "无法连接" in result["message"]


class TestAutoSync:
    """Tests for automatic syncing."""

    def test_start_auto_sync_disabled(self, sync_client, mock_settings_manager):
        """Test auto sync doesn't start when disabled."""
        mock_settings_manager.get_setting_bool.return_value = False

        sync_client.start_auto_sync()

        assert sync_client.is_running is False
        assert sync_client.sync_thread is None

    def test_start_auto_sync_enabled(self, sync_client, mock_settings_manager):
        """Test auto sync starts when enabled."""
        mock_settings_manager.get_setting_bool.return_value = True

        sync_client.start_auto_sync()

        assert sync_client.is_running is True
        assert sync_client.sync_thread is not None
        assert sync_client.sync_thread.daemon is True

        # Cleanup
        sync_client.stop_auto_sync()

    def test_start_auto_sync_already_running(self, sync_client, mock_settings_manager):
        """Test starting auto sync when already running."""
        mock_settings_manager.get_setting_bool.return_value = True

        sync_client.start_auto_sync()
        first_thread = sync_client.sync_thread

        # Try starting again
        sync_client.start_auto_sync()

        # Should be the same thread
        assert sync_client.sync_thread is first_thread

        # Cleanup
        sync_client.stop_auto_sync()

    def test_stop_auto_sync(self, sync_client, mock_settings_manager):
        """Test stopping auto sync."""
        mock_settings_manager.get_setting_bool.return_value = True

        sync_client.start_auto_sync()
        assert sync_client.is_running is True

        sync_client.stop_auto_sync()
        assert sync_client.is_running is False


class TestWeeksParser:
    """Tests for _parse_weeks method."""

    def test_parse_weeks_valid_json(self, sync_client):
        """Test parsing valid weeks JSON."""
        result = sync_client._parse_weeks("[1,2,3,4,5]")
        assert result == [1, 2, 3, 4, 5]

    def test_parse_weeks_none(self, sync_client):
        """Test parsing None weeks data."""
        result = sync_client._parse_weeks(None)
        assert result == []

    def test_parse_weeks_empty_string(self, sync_client):
        """Test parsing empty string."""
        result = sync_client._parse_weeks("")
        assert result == []

    def test_parse_weeks_invalid_json(self, sync_client):
        """Test parsing invalid JSON."""
        result = sync_client._parse_weeks("not a json")
        assert result == []

    def test_parse_weeks_string_numbers(self, sync_client):
        """Test parsing weeks with string numbers."""
        result = sync_client._parse_weeks('["1","2","3"]')
        assert result == [1, 2, 3]

    def test_parse_weeks_mixed_types(self, sync_client):
        """Test parsing weeks with mixed valid/invalid types."""
        result = sync_client._parse_weeks('[1,"2","invalid",3]')
        assert result == [1, 2, 3]

    def test_parse_weeks_not_a_list(self, sync_client):
        """Test parsing non-list JSON."""
        result = sync_client._parse_weeks('{"week": 1}')
        assert result == []


class TestThreadSafety:
    """Tests for thread safety."""

    def test_uuid_generation_thread_safe(self, sync_client, mock_settings_manager):
        """Test UUID generation is thread-safe."""
        # Simulate multiple threads requesting UUID
        uuids_generated = []

        def generate_uuid():
            with sync_client.uuid_lock:
                # Simulate the UUID generation logic
                client_uuid = "new-uuid-" + str(threading.current_thread().ident)
                uuids_generated.append(client_uuid)

        threads = [threading.Thread(target=generate_uuid) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All UUIDs should have been generated
        assert len(uuids_generated) == 10


class TestDataSerialization:
    """Tests for data serialization."""

    @responses.activate
    def test_courses_serialization(self, sync_client, mock_settings_manager, mock_schedule_manager):
        """Test courses are correctly serialized."""
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "test-uuid"
        }.get(key, default)

        mock_schedule_manager.get_all_courses.return_value = [
            {
                "id": 1,
                "name": "Physics",
                "teacher": "Dr. Johnson",
                "color": "#00FF00",
                "note": "Advanced course"
            }
        ]
        mock_schedule_manager.get_all_schedule_entries.return_value = []

        responses.add(
            responses.POST,
            "http://localhost:8765/api/sync",
            json={"success": True, "data": {}},
            status=200
        )

        sync_client.sync_to_server()

        request_body = json.loads(responses.calls[0].request.body)
        course = request_body["courses"][0]

        assert course["id"] == 1
        assert course["name"] == "Physics"
        assert course["teacher"] == "Dr. Johnson"
        assert course["color"] == "#00FF00"
        assert course["note"] == "Advanced course"

    @responses.activate
    def test_schedule_entries_serialization(self, sync_client, mock_settings_manager, mock_schedule_manager):
        """Test schedule entries are correctly serialized."""
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "test-uuid"
        }.get(key, default)

        mock_schedule_manager.get_all_courses.return_value = []
        mock_schedule_manager.get_all_schedule_entries.return_value = [
            {
                "id": 10,
                "course_id": 5,
                "day_of_week": 3,
                "start_time": "10:00",
                "end_time": "11:30",
                "weeks": "[1,2,3,4,5,6,7,8]"
            }
        ]

        responses.add(
            responses.POST,
            "http://localhost:8765/api/sync",
            json={"success": True, "data": {}},
            status=200
        )

        sync_client.sync_to_server()

        request_body = json.loads(responses.calls[0].request.body)
        entry = request_body["schedule_entries"][0]

        assert entry["id"] == 10
        assert entry["course_id"] == 5
        assert entry["day_of_week"] == 3
        assert entry["start_time"] == "10:00"
        assert entry["end_time"] == "11:30"
        assert entry["weeks"] == [1, 2, 3, 4, 5, 6, 7, 8]


class TestDownloadFromServer:
    """Tests for download_from_server method."""

    @responses.activate
    def test_download_success(self, sync_client, mock_settings_manager):
        """Test successful download from server."""
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "test-uuid-123"
        }.get(key, default)

        # Mock courses endpoint
        responses.add(
            responses.GET,
            "http://localhost:8765/api/clients/test-uuid-123/courses",
            json={
                "success": True,
                "data": {
                    "courses": [
                        {"id": 1, "name": "Math", "teacher": "Mr. Smith", "color": "#FF0000"}
                    ]
                }
            },
            status=200
        )

        # Mock schedule endpoint
        responses.add(
            responses.GET,
            "http://localhost:8765/api/clients/test-uuid-123/schedule",
            json={
                "success": True,
                "data": {
                    "schedule_entries": [
                        {
                            "id": 1,
                            "course_id": 1,
                            "day_of_week": 1,
                            "start_time": "08:00",
                            "end_time": "09:30",
                            "weeks": [1, 2, 3]
                        }
                    ]
                }
            },
            status=200
        )

        result = sync_client.download_from_server()

        assert result["success"] is True
        assert len(result["courses"]) == 1
        assert result["courses"][0]["name"] == "Math"
        assert len(result["schedule_entries"]) == 1

    def test_download_no_config(self, sync_client, mock_settings_manager):
        """Test download fails when configuration is missing."""
        mock_settings_manager.get_setting.return_value = ""

        result = sync_client.download_from_server()

        assert result["success"] is False
        assert "未配置" in result["message"]

    @responses.activate
    def test_download_server_error(self, sync_client, mock_settings_manager):
        """Test download handles server errors."""
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "test-uuid-123"
        }.get(key, default)

        responses.add(
            responses.GET,
            "http://localhost:8765/api/clients/test-uuid-123/courses",
            json={"success": False, "message": "Server error"},
            status=200
        )

        result = sync_client.download_from_server()

        assert result["success"] is False
        assert "下载课程失败" in result["message"]


class TestDetectConflicts:
    """Tests for detect_conflicts method."""

    def test_no_conflicts(self, sync_client):
        """Test when there are no conflicts."""
        local_data = {
            "courses": [{"id": 1, "name": "Math", "teacher": "Mr. Smith", "color": "#FF0000"}],
            "schedule_entries": [
                {"id": 1, "course_id": 1, "day_of_week": 1, "start_time": "08:00", "end_time": "09:30", "weeks": "[1,2,3]"}
            ]
        }
        server_data = {
            "courses": [{"id": 1, "name": "Math", "teacher": "Mr. Smith", "color": "#FF0000"}],
            "schedule_entries": [
                {"id": 1, "course_id": 1, "day_of_week": 1, "start_time": "08:00", "end_time": "09:30", "weeks": [1, 2, 3]}
            ]
        }

        result = sync_client.detect_conflicts(local_data, server_data)

        assert result["has_conflicts"] is False
        assert len(result["conflicted_courses"]) == 0
        assert len(result["conflicted_entries"]) == 0

    def test_course_conflict(self, sync_client):
        """Test when there are course conflicts."""
        local_data = {
            "courses": [{"id": 1, "name": "Math", "teacher": "Mr. Smith", "color": "#FF0000"}],
            "schedule_entries": []
        }
        server_data = {
            "courses": [{"id": 1, "name": "Math", "teacher": "Dr. Johnson", "color": "#FF0000"}],
            "schedule_entries": []
        }

        result = sync_client.detect_conflicts(local_data, server_data)

        assert result["has_conflicts"] is True
        assert len(result["conflicted_courses"]) == 1
        assert result["conflicted_courses"][0]["id"] == 1
        assert result["conflicted_courses"][0]["local"]["teacher"] == "Mr. Smith"
        assert result["conflicted_courses"][0]["server"]["teacher"] == "Dr. Johnson"

    def test_schedule_entry_conflict(self, sync_client):
        """Test when there are schedule entry conflicts."""
        local_data = {
            "courses": [],
            "schedule_entries": [
                {"id": 1, "course_id": 1, "day_of_week": 1, "start_time": "08:00", "end_time": "09:30", "weeks": "[1,2,3]"}
            ]
        }
        server_data = {
            "courses": [],
            "schedule_entries": [
                {"id": 1, "course_id": 1, "day_of_week": 2, "start_time": "08:00", "end_time": "09:30", "weeks": [1, 2, 3]}
            ]
        }

        result = sync_client.detect_conflicts(local_data, server_data)

        assert result["has_conflicts"] is True
        assert len(result["conflicted_entries"]) == 1
        assert result["conflicted_entries"][0]["id"] == 1


class TestMergeData:
    """Tests for merge_data method."""

    def test_merge_server_wins(self, sync_client):
        """Test merge with server_wins strategy."""
        local_data = {
            "courses": [{"id": 1, "name": "Math", "teacher": "Mr. Smith"}],
            "schedule_entries": []
        }
        server_data = {
            "courses": [{"id": 1, "name": "Math", "teacher": "Dr. Johnson"}],
            "schedule_entries": []
        }

        result = sync_client.merge_data(local_data, server_data, strategy="server_wins")

        assert len(result["courses"]) == 1
        assert result["courses"][0]["teacher"] == "Dr. Johnson"  # Server wins

    def test_merge_local_wins(self, sync_client):
        """Test merge with local_wins strategy."""
        local_data = {
            "courses": [{"id": 1, "name": "Math", "teacher": "Mr. Smith"}],
            "schedule_entries": []
        }
        server_data = {
            "courses": [{"id": 1, "name": "Math", "teacher": "Dr. Johnson"}],
            "schedule_entries": []
        }

        result = sync_client.merge_data(local_data, server_data, strategy="local_wins")

        assert len(result["courses"]) == 1
        assert result["courses"][0]["teacher"] == "Mr. Smith"  # Local wins

    def test_merge_combines_unique_items(self, sync_client):
        """Test merge combines unique items from both sources."""
        local_data = {
            "courses": [{"id": 1, "name": "Math", "teacher": "Mr. Smith"}],
            "schedule_entries": []
        }
        server_data = {
            "courses": [{"id": 2, "name": "Physics", "teacher": "Dr. Johnson"}],
            "schedule_entries": []
        }

        result = sync_client.merge_data(local_data, server_data, strategy="server_wins")

        assert len(result["courses"]) == 2


class TestApplyServerData:
    """Tests for apply_server_data method."""

    def test_apply_updates_courses(self, sync_client, mock_schedule_manager):
        """Test apply_server_data updates existing courses."""
        mock_schedule_manager.get_all_courses.return_value = [
            {"id": 1, "name": "Math", "teacher": "Mr. Smith", "location": "Room 101", "color": "#FF0000"}
        ]
        mock_schedule_manager.get_all_schedule_entries.return_value = []
        mock_schedule_manager.update_course.return_value = True

        server_data = {
            "courses": [
                {"id": 1, "name": "Math", "teacher": "Dr. Johnson", "location": "Room 102", "color": "#00FF00"}
            ],
            "schedule_entries": []
        }

        result = sync_client.apply_server_data(server_data)

        assert result is True
        mock_schedule_manager.update_course.assert_called_once_with(
            course_id=1,
            name="Math",
            teacher="Dr. Johnson",
            location="Room 102",
            color="#00FF00"
        )

    def test_apply_adds_schedule_entries(self, sync_client, mock_schedule_manager):
        """Test apply_server_data adds new schedule entries."""
        mock_schedule_manager.get_all_courses.return_value = []
        mock_schedule_manager.get_all_schedule_entries.return_value = []
        mock_schedule_manager.add_schedule_entry.return_value = 1

        server_data = {
            "courses": [],
            "schedule_entries": [
                {
                    "id": 1,
                    "course_id": 1,
                    "day_of_week": 1,
                    "start_time": "08:00",
                    "end_time": "09:30",
                    "weeks": [1, 2, 3],
                    "note": "Test note"
                }
            ]
        }

        result = sync_client.apply_server_data(server_data)

        assert result is True
        mock_schedule_manager.add_schedule_entry.assert_called_once()


class TestBidirectionalSync:
    """Tests for bidirectional_sync method."""

    @responses.activate
    def test_bidirectional_sync_success(self, sync_client, mock_settings_manager, mock_schedule_manager):
        """Test successful bidirectional sync."""
        # Setup settings
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "test-uuid-123"
        }.get(key, default)

        # Setup local data
        mock_schedule_manager.get_all_courses.return_value = [
            {"id": 1, "name": "Math", "teacher": "Mr. Smith", "location": "101", "color": "#FF0000"}
        ]
        mock_schedule_manager.get_all_schedule_entries.return_value = []
        mock_schedule_manager.update_course.return_value = True

        # Mock download endpoints
        responses.add(
            responses.GET,
            "http://localhost:8765/api/clients/test-uuid-123/courses",
            json={
                "success": True,
                "data": {
                    "courses": [
                        {"id": 1, "name": "Math", "teacher": "Dr. Johnson", "location": "102", "color": "#00FF00"}
                    ]
                }
            },
            status=200
        )

        responses.add(
            responses.GET,
            "http://localhost:8765/api/clients/test-uuid-123/schedule",
            json={
                "success": True,
                "data": {"schedule_entries": []}
            },
            status=200
        )

        # Mock upload endpoint
        responses.add(
            responses.POST,
            "http://localhost:8765/api/sync",
            json={"success": True, "data": {"synced_courses": 1, "synced_entries": 0}},
            status=200
        )

        result = sync_client.bidirectional_sync(strategy="server_wins")

        assert result["success"] is True
        assert result["conflicts_found"] == 1  # One course conflict
        assert result["courses_updated"] == 1

    @responses.activate
    def test_bidirectional_sync_download_failure(self, sync_client, mock_settings_manager):
        """Test bidirectional sync handles download failure."""
        mock_settings_manager.get_setting.side_effect = lambda key, default="": {
            "server_url": "http://localhost:8765",
            "client_uuid": "test-uuid-123"
        }.get(key, default)

        responses.add(
            responses.GET,
            "http://localhost:8765/api/clients/test-uuid-123/courses",
            json={"success": False, "message": "Download failed"},
            status=200
        )

        result = sync_client.bidirectional_sync()

        assert result["success"] is False
        assert "下载失败" in result["message"]
        assert result["conflicts_found"] == 0
