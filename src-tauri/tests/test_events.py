"""
Tests for events.py - Event handler system.
"""
import sys
from pathlib import Path
from datetime import datetime
import pytest

# Add the python module to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from tauri_app.events import EventHandler, ScheduleUpdateEvent, SettingUpdateEvent, SettingsBatchUpdateEvent


class TestEventHandler:
    """Test the EventHandler singleton class."""

    def test_singleton_pattern(self):
        """Test that EventHandler follows singleton pattern."""
        handler1 = EventHandler()
        handler2 = EventHandler()

        assert handler1 is handler2
        assert EventHandler._instance is handler1

    def test_get_instance(self):
        """Test get_instance class method."""
        handler = EventHandler()
        retrieved = EventHandler.get_instance()

        assert retrieved is handler

    def test_is_initialized_false_by_default(self):
        """Test that handler is not initialized by default."""
        # Create a new handler (singleton will return existing, but for this test we check state)
        handler = EventHandler()
        # Reset for testing
        handler._app_handle = None

        assert handler.is_initialized is False

    def test_is_initialized_true_after_init(self, mocker):
        """Test that handler is initialized after initialize() call."""
        handler = EventHandler()
        mock_app_handle = mocker.MagicMock()
        mock_portal = mocker.MagicMock()

        handler.initialize(mock_app_handle, mock_portal)

        assert handler.is_initialized is True
        assert handler._app_handle is mock_app_handle
        assert handler._portal is mock_portal

    def test_initialize_logs_message(self, mocker):
        """Test that initialize logs a message."""
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        mock_app_handle = mocker.MagicMock()
        mock_portal = mocker.MagicMock()

        handler.initialize(mock_app_handle, mock_portal)

        mock_logger.assert_called_with("info", "Event handler initialized with async portal")


class TestEmitStringEvent:
    """Test emit_string_event functionality."""

    def test_emit_string_event_without_init(self, mocker):
        """Test that emitting without initialization logs warning."""
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        handler._app_handle = None

        handler.emit_string_event("test-event", "test message")

        mock_logger.assert_any_call("warning", "Event handler not initialized, cannot emit event")

    def test_emit_string_event_success(self, mocker):
        """Test successful string event emission."""
        mock_emitter = mocker.patch("tauri_app.events.Emitter.emit_str")
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        mock_app_handle = mocker.MagicMock()
        handler._app_handle = mock_app_handle

        handler.emit_string_event("test-event", "test message")

        mock_emitter.assert_called_once_with(mock_app_handle, "test-event", "test message")
        mock_logger.assert_any_call("debug", "String event emitted: test-event - test message")

    def test_emit_string_event_handles_exception(self, mocker):
        """Test that exceptions during emit are caught and logged."""
        mock_emitter = mocker.patch("tauri_app.events.Emitter.emit_str", side_effect=Exception("Emit failed"))
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        mock_app_handle = mocker.MagicMock()
        handler._app_handle = mock_app_handle

        handler.emit_string_event("test-event", "test message")

        mock_logger.assert_any_call("error", "Failed to emit string event: Emit failed")


class TestEmitSettingUpdate:
    """Test emit_setting_update functionality."""

    def test_emit_setting_update_without_init(self, mocker):
        """Test setting update without initialization."""
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        handler._app_handle = None

        handler.emit_setting_update("test_key", "test_value")

        mock_logger.assert_any_call("warning", "Event handler not initialized, cannot emit event")

    def test_emit_setting_update_success(self, mocker):
        """Test successful setting update emission."""
        mock_emitter = mocker.patch("tauri_app.events.Emitter.emit")
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        mock_app_handle = mocker.MagicMock()
        handler._app_handle = mock_app_handle

        handler.emit_setting_update("current_week", "5")

        # Verify emit was called with correct arguments
        assert mock_emitter.call_count == 1
        call_args = mock_emitter.call_args
        assert call_args[0][0] == mock_app_handle
        assert call_args[0][1] == "setting-update"

        # Verify event data structure
        event_data = call_args[0][2]
        assert isinstance(event_data, SettingUpdateEvent)
        assert event_data.key == "current_week"
        assert event_data.value == "5"

        mock_logger.assert_any_call("info", "Setting update event emitted: current_week = 5")

    def test_emit_setting_update_handles_exception(self, mocker):
        """Test exception handling in setting update."""
        mock_emitter = mocker.patch("tauri_app.events.Emitter.emit", side_effect=Exception("Emit failed"))
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        mock_app_handle = mocker.MagicMock()
        handler._app_handle = mock_app_handle

        handler.emit_setting_update("test_key", "test_value")

        mock_logger.assert_any_call("error", "Failed to emit setting update event: Emit failed")


class TestEmitScheduleUpdate:
    """Test emit_schedule_update functionality."""

    def test_emit_schedule_update_without_init(self, mocker):
        """Test schedule update without initialization."""
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        handler._app_handle = None

        handler.emit_schedule_update("course_added", {"id": 1, "name": "Test"})

        mock_logger.assert_any_call("warning", "Event handler not initialized, cannot emit event")

    def test_emit_schedule_update_success(self, mocker):
        """Test successful schedule update emission."""
        mock_emitter = mocker.patch("tauri_app.events.Emitter.emit")
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        mock_app_handle = mocker.MagicMock()
        handler._app_handle = mock_app_handle

        payload = {"id": 1, "name": "Test Course"}
        handler.emit_schedule_update("course_added", payload)

        # Verify emit was called
        assert mock_emitter.call_count == 1
        call_args = mock_emitter.call_args
        assert call_args[0][0] == mock_app_handle
        assert call_args[0][1] == "schedule-update"

        # Verify event data
        event_data = call_args[0][2]
        assert isinstance(event_data, ScheduleUpdateEvent)
        assert event_data.type == "course_added"
        assert event_data.payload == payload

        mock_logger.assert_any_call("debug", "Event emitted successfully: course_added")


class TestConvenienceEmitMethods:
    """Test convenience emit methods."""

    def test_emit_course_added(self, mocker):
        """Test emit_course_added convenience method."""
        mock_emit = mocker.patch.object(EventHandler, "emit_schedule_update")
        handler = EventHandler()

        handler.emit_course_added(1, "Test Course")

        mock_emit.assert_called_once_with("course_added", {"id": 1, "name": "Test Course"})

    def test_emit_course_updated(self, mocker):
        """Test emit_course_updated convenience method."""
        mock_emit = mocker.patch.object(EventHandler, "emit_schedule_update")
        handler = EventHandler()

        handler.emit_course_updated(1, name="Updated Course", teacher="New Teacher")

        mock_emit.assert_called_once_with(
            "course_updated",
            {"id": 1, "name": "Updated Course", "teacher": "New Teacher"}
        )

    def test_emit_course_deleted(self, mocker):
        """Test emit_course_deleted convenience method."""
        mock_emit = mocker.patch.object(EventHandler, "emit_schedule_update")
        handler = EventHandler()

        handler.emit_course_deleted(1)

        mock_emit.assert_called_once_with("course_deleted", {"id": 1})

    def test_emit_schedule_added(self, mocker):
        """Test emit_schedule_added convenience method."""
        mock_emit = mocker.patch.object(EventHandler, "emit_schedule_update")
        handler = EventHandler()

        handler.emit_schedule_added(1, 2, 1, "09:00", "10:30")

        mock_emit.assert_called_once_with(
            "schedule_added",
            {
                "id": 1,
                "course_id": 2,
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "10:30"
            }
        )

    def test_emit_schedule_deleted(self, mocker):
        """Test emit_schedule_deleted convenience method."""
        mock_emit = mocker.patch.object(EventHandler, "emit_schedule_update")
        handler = EventHandler()

        handler.emit_schedule_deleted(1)

        mock_emit.assert_called_once_with("schedule_deleted", {"id": 1})


class TestEmitSettingsBatchUpdate:
    """Test emit_settings_batch_updated functionality."""

    def test_emit_settings_batch_update_without_init(self, mocker):
        """Test batch update without initialization."""
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        handler._app_handle = None

        handler.emit_settings_batch_updated(["key1", "key2"])

        mock_logger.assert_any_call("warning", "Event handler not initialized, cannot emit event")

    def test_emit_settings_batch_update_success(self, mocker):
        """Test successful batch update emission."""
        mock_emitter = mocker.patch("tauri_app.events.Emitter.emit")
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        mock_app_handle = mocker.MagicMock()
        handler._app_handle = mock_app_handle

        updated_keys = ["current_week", "total_weeks", "semester_start_date"]
        handler.emit_settings_batch_updated(updated_keys)

        # Verify emit was called
        assert mock_emitter.call_count == 1
        call_args = mock_emitter.call_args
        assert call_args[0][0] == mock_app_handle
        assert call_args[0][1] == "settings-batch-update"

        # Verify event data
        event_data = call_args[0][2]
        assert isinstance(event_data, SettingsBatchUpdateEvent)
        assert event_data.updated_keys == updated_keys

        mock_logger.assert_any_call("info", "Settings batch update event emitted: 3 settings")


class TestCameraEvents:
    """Test camera-related event emissions."""

    def test_emit_camera_initialized(self, mocker):
        """Test camera initialized event."""
        mock_emit_str = mocker.patch.object(EventHandler, "emit_string_event")
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()

        encoder_info = {"encoder": "H264"}
        handler.emit_camera_initialized(2, encoder_info)

        mock_emit_str.assert_called_once_with(
            "camera-initialized",
            "Camera system initialized: 2 cameras found"
        )
        mock_logger.assert_any_call("info", "Camera system initialized with 2 cameras")

    def test_emit_camera_recording_started(self, mocker):
        """Test recording started event."""
        mock_emit_str = mocker.patch.object(EventHandler, "emit_string_event")
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()

        handler.emit_camera_recording_started(0, "recording_001.mp4")

        mock_emit_str.assert_called_once_with(
            "camera-recording-started",
            "Recording started on camera 0: recording_001.mp4"
        )
        mock_logger.assert_any_call("info", "Recording started: camera 0 -> recording_001.mp4")

    def test_emit_camera_recording_stopped(self, mocker):
        """Test recording stopped event."""
        mock_emit_str = mocker.patch.object(EventHandler, "emit_string_event")
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()

        handler.emit_camera_recording_stopped(0)

        mock_emit_str.assert_called_once_with(
            "camera-recording-stopped",
            "Recording stopped on camera 0"
        )
        mock_logger.assert_any_call("info", "Recording stopped on camera 0")


class TestCustomEvent:
    """Test custom event emission."""

    def test_emit_custom_event_without_init(self, mocker):
        """Test custom event without initialization."""
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        handler._app_handle = None

        handler.emit_custom_event("my-event", {"data": "test"})

        mock_logger.assert_any_call("warning", "Event handler not initialized, cannot emit event")

    def test_emit_custom_event_success(self, mocker):
        """Test successful custom event emission."""
        mock_emitter = mocker.patch("tauri_app.events.Emitter.emit_str")
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        mock_app_handle = mocker.MagicMock()
        handler._app_handle = mock_app_handle

        payload = {"data": "test", "value": 123}
        handler.emit_custom_event("my-custom-event", payload)

        mock_emitter.assert_called_once()
        call_args = mock_emitter.call_args
        assert call_args[0][0] == mock_app_handle
        assert call_args[0][1] == "my-custom-event"
        # Verify JSON string payload
        import json
        assert json.loads(call_args[0][2]) == payload

        mock_logger.assert_any_call("debug", "Custom event emitted: my-custom-event")

    def test_emit_custom_event_handles_exception(self, mocker):
        """Test exception handling in custom event."""
        mock_emitter = mocker.patch("tauri_app.events.Emitter.emit_str", side_effect=Exception("Failed"))
        mock_logger = mocker.patch("tauri_app.events.logger.log_message")
        handler = EventHandler()
        mock_app_handle = mocker.MagicMock()
        handler._app_handle = mock_app_handle

        handler.emit_custom_event("test-event", {"data": "test"})

        mock_logger.assert_any_call("error", "Failed to emit custom event: Failed")


class TestEventModels:
    """Test Pydantic event models."""

    def test_schedule_update_event_model(self):
        """Test ScheduleUpdateEvent model validation."""
        event = ScheduleUpdateEvent(
            type="course_added",
            payload={"id": 1, "name": "Test"},
            timestamp=datetime.now().isoformat()
        )

        assert event.type == "course_added"
        assert event.payload["id"] == 1
        assert event.timestamp is not None

    def test_setting_update_event_model(self):
        """Test SettingUpdateEvent model validation."""
        event = SettingUpdateEvent(
            key="current_week",
            value="5",
            timestamp=datetime.now().isoformat()
        )

        assert event.key == "current_week"
        assert event.value == "5"
        assert event.timestamp is not None

    def test_settings_batch_update_event_model(self):
        """Test SettingsBatchUpdateEvent model validation."""
        event = SettingsBatchUpdateEvent(
            updated_keys=["key1", "key2", "key3"],
            timestamp=datetime.now().isoformat()
        )

        assert len(event.updated_keys) == 3
        assert "key1" in event.updated_keys
        assert event.timestamp is not None
