"""
Unit tests for SettingsManager (settings_manager.py).
"""
import pytest
import uuid

from tauri_app.settings_manager import SettingsManager


class TestSettingsInitialization:
    """Tests for settings initialization."""

    def test_initialize_defaults(
        self, initialized_settings_manager, db_connection
    ):
        """Test that default settings are initialized."""
        manager = initialized_settings_manager

        # Verify some key default settings exist
        cur = db_connection.cursor()
        cur.execute("SELECT key, value FROM settings")
        settings = {row[0]: row[1] for row in cur.fetchall()}

        assert "client_uuid" in settings
        assert "server_url" in settings
        assert "sync_enabled" in settings
        assert settings["sync_enabled"] == "false"
        assert "api_server_enabled" in settings
        assert settings["api_server_enabled"] == "false"
        assert "theme_color" in settings
        assert settings["theme_color"] == "#6750A4"

    def test_uuid_generation(self, initialized_settings_manager):
        """Test that client_uuid is properly generated."""
        manager = initialized_settings_manager

        client_uuid = manager.get_setting("client_uuid")

        assert client_uuid is not None
        # Verify it's a valid UUID
        try:
            uuid.UUID(client_uuid)
        except ValueError:
            pytest.fail("client_uuid is not a valid UUID")

    def test_defaults_not_overwritten(
        self, initialized_settings_manager, db_connection
    ):
        """Test that existing settings are not overwritten by defaults."""
        manager = initialized_settings_manager

        # Set a custom value
        manager.set_setting("theme_color", "#FF0000")

        # Re-initialize defaults
        manager.initialize_defaults()

        # Verify custom value is preserved
        theme_color = manager.get_setting("theme_color")
        assert theme_color == "#FF0000", "Custom setting should not be overwritten"


class TestSettingsOperations:
    """Tests for basic settings operations."""

    def test_set_and_get_setting(self, initialized_settings_manager):
        """Test setting and getting a configuration value."""
        manager = initialized_settings_manager

        manager.set_setting("test_key", "test_value")
        value = manager.get_setting("test_key")

        assert value == "test_value"

    def test_get_nonexistent_setting(self, initialized_settings_manager):
        """Test getting a non-existent setting returns None."""
        manager = initialized_settings_manager

        value = manager.get_setting("nonexistent_key")
        assert value is None

    def test_update_existing_setting(
        self, initialized_settings_manager, mock_event_handler
    ):
        """Test updating an existing setting."""
        manager = initialized_settings_manager

        # Set initial value
        manager.set_setting("update_test", "initial")
        mock_event_handler.reset_mock()

        # Update value
        manager.set_setting("update_test", "updated")

        # Verify update
        value = manager.get_setting("update_test")
        assert value == "updated"

        # Verify event was emitted
        mock_event_handler.emit_setting_update.assert_called()

    def test_get_all_settings(self, initialized_settings_manager):
        """Test getting all settings."""
        manager = initialized_settings_manager

        # Set some custom settings
        manager.set_setting("custom1", "value1")
        manager.set_setting("custom2", "value2")

        all_settings = manager.get_all_settings()

        assert isinstance(all_settings, dict)
        assert "custom1" in all_settings
        assert all_settings["custom1"] == "value1"
        assert "custom2" in all_settings
        assert all_settings["custom2"] == "value2"
        # Default settings should also be present
        assert "client_uuid" in all_settings
        assert "sync_enabled" in all_settings


class TestBatchSettingsUpdate:
    """Tests for batch settings updates."""

    def test_update_multiple(
        self, initialized_settings_manager, mock_event_handler
    ):
        """Test updating multiple settings at once."""
        manager = initialized_settings_manager

        settings_to_update = {
            "theme_color": "#00FF00",
            "sync_enabled": "true",
            "api_server_port": "9000",
        }

        mock_event_handler.reset_mock()

        result = manager.update_multiple(settings_to_update)

        assert result is True

        # Verify all settings were updated
        assert manager.get_setting("theme_color") == "#00FF00"
        assert manager.get_setting("sync_enabled") == "true"
        assert manager.get_setting("api_server_port") == "9000"

        # Verify batch event was emitted
        mock_event_handler.emit_settings_batch_updated.assert_called_once()

    def test_batch_update_with_empty_dict(self, initialized_settings_manager):
        """Test batch update with empty dictionary."""
        manager = initialized_settings_manager

        result = manager.update_multiple({})

        # Should handle gracefully
        assert result is True


class TestBooleanSettings:
    """Tests for boolean setting operations."""

    def test_get_setting_bool_true(self, initialized_settings_manager):
        """Test getting a boolean setting that is 'true'."""
        manager = initialized_settings_manager

        manager.set_setting("bool_test", "true")
        value = manager.get_setting_bool("bool_test")

        assert value is True

    def test_get_setting_bool_false(self, initialized_settings_manager):
        """Test getting a boolean setting that is 'false'."""
        manager = initialized_settings_manager

        manager.set_setting("bool_test", "false")
        value = manager.get_setting_bool("bool_test")

        assert value is False

    def test_get_setting_bool_nonexistent(self, initialized_settings_manager):
        """Test getting a non-existent boolean setting with default."""
        manager = initialized_settings_manager

        # Test with default=True
        value = manager.get_setting_bool("nonexistent", default=True)
        assert value is True

        # Test with default=False
        value = manager.get_setting_bool("nonexistent", default=False)
        assert value is False

    def test_get_setting_bool_invalid_value(self, initialized_settings_manager):
        """Test getting a boolean setting with invalid value."""
        manager = initialized_settings_manager

        manager.set_setting("invalid_bool", "not_a_bool")
        value = manager.get_setting_bool("invalid_bool", default=False)

        # Should return default when value is invalid
        assert value is False


class TestIntegerSettings:
    """Tests for integer setting operations."""

    def test_get_setting_int(self, initialized_settings_manager):
        """Test getting an integer setting."""
        manager = initialized_settings_manager

        manager.set_setting("int_test", "42")
        value = manager.get_setting_int("int_test")

        assert value == 42
        assert isinstance(value, int)

    def test_get_setting_int_nonexistent(self, initialized_settings_manager):
        """Test getting a non-existent integer setting with default."""
        manager = initialized_settings_manager

        value = manager.get_setting_int("nonexistent_int", default=100)
        assert value == 100

    def test_get_setting_int_invalid_value(self, initialized_settings_manager):
        """Test getting an integer setting with invalid value."""
        manager = initialized_settings_manager

        manager.set_setting("invalid_int", "not_a_number")
        value = manager.get_setting_int("invalid_int", default=50)

        # Should return default when value is invalid
        assert value == 50


class TestSpecificSettings:
    """Tests for specific application settings."""

    def test_sync_settings(self, initialized_settings_manager):
        """Test sync-related settings."""
        manager = initialized_settings_manager

        # Default sync settings
        assert manager.get_setting_bool("sync_enabled") is False
        assert manager.get_setting_int("sync_interval") == 300

        # Update sync settings
        manager.set_setting("sync_enabled", "true")
        manager.set_setting("sync_interval", "600")

        assert manager.get_setting_bool("sync_enabled") is True
        assert manager.get_setting_int("sync_interval") == 600

    def test_api_server_settings(self, initialized_settings_manager):
        """Test API server settings."""
        manager = initialized_settings_manager

        # Default API server settings
        assert manager.get_setting_bool("api_server_enabled") is False
        assert manager.get_setting("api_server_host") == "0.0.0.0"
        assert manager.get_setting("api_server_port") == "8765"

    def test_camera_settings(self, initialized_settings_manager):
        """Test camera-related settings."""
        manager = initialized_settings_manager

        # Default camera settings
        assert manager.get_setting_bool("camera_enabled") is False
        assert manager.get_setting_int("camera_width") == 1280
        assert manager.get_setting_int("camera_height") == 720
        assert manager.get_setting_int("camera_fps") == 30

    def test_reminder_settings(self, initialized_settings_manager):
        """Test reminder settings."""
        manager = initialized_settings_manager

        # Default reminder settings
        assert manager.get_setting_bool("reminder_enabled") is True
        assert manager.get_setting_int("reminder_minutes") == 10
        assert manager.get_setting_bool("reminder_sound") is True

    def test_display_settings(self, initialized_settings_manager):
        """Test display-related settings."""
        manager = initialized_settings_manager

        # Default display settings
        assert manager.get_setting_bool("show_clock") is True
        assert manager.get_setting_bool("show_schedule") is True
        assert manager.get_setting_bool("show_sync_status") is True
