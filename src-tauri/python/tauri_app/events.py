"""
Global event handler for ClassTop application.
Manages all event emissions to the frontend in a thread-safe manner.
"""

import asyncio
import json
import threading
from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel
from pytauri import AppHandle, Emitter
from . import logger


class ScheduleUpdateEvent(BaseModel):
    """Model for schedule update events."""
    type: str
    payload: Dict[str, Any]
    timestamp: str

class SettingUpdateEvent(BaseModel):
    """Model for setting updated events."""
    key: str
    value: Any
    timestamp: str


class SettingsBatchUpdateEvent(BaseModel):
    """Model for batch settings update events."""
    updated_keys: list[str]
    timestamp: str


class EventHandler:
    """Thread-safe event handler for emitting events to the frontend."""

    _instance: Optional['EventHandler'] = None
    _app_handle: Optional[AppHandle] = None
    _portal = None  # Async portal for thread-safe operations

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventHandler, cls).__new__(cls)
        return cls._instance

    def initialize(self, app_handle: AppHandle, portal) -> None:
        """Initialize the event handler with app handle and async portal."""
        self._app_handle = app_handle
        self._portal = portal
        logger.log_message("info", "Event handler initialized with async portal")
        
    def emit_string_event(self, event_name: str, message: str) -> None:
        """Emit a simple string event to the frontend."""
        if not self._app_handle:
            logger.log_message("warning", "Event handler not initialized, cannot emit event")
            return

        try:
            Emitter.emit_str(self._app_handle, event_name, message)
            logger.log_message("debug", f"String event emitted: {event_name} - {message}")
        except Exception as e:
            logger.log_message("error", f"Failed to emit string event: {e}")
    
    def emit_setting_update(self, key: str, value: Any) -> None:
        """Emit an event when a setting is updated."""
        if not self._app_handle:
            logger.log_message("warning", "Event handler not initialized, cannot emit event")
            return

        try:
            event_data = SettingUpdateEvent(
                key=key,
                value=value,
                timestamp=datetime.now().isoformat()
            )
            Emitter.emit(self._app_handle, "setting-update", event_data)
            logger.log_message("info", f"Setting update event emitted: {key} = {value}")
        except Exception as e:
            logger.log_message("error", f"Failed to emit setting update event: {e}")

    def emit_schedule_update(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit a schedule update event to the frontend."""
        if not self._app_handle:
            logger.log_message("warning", "Event handler not initialized, cannot emit event")
            return

        try:
            # Create event data
            event_data = ScheduleUpdateEvent(
                type=event_type,
                payload=payload,
                timestamp=datetime.now().isoformat()
            )

            # Try to emit directly - PyTauri's Emitter should be thread-safe
            try:
                Emitter.emit(self._app_handle, "schedule-update", event_data)
                logger.log_message("debug", f"Event emitted successfully: {event_type}")
            except RuntimeError as e:
                # If we get a runtime error about event loop, try using portal
                if "event loop" in str(e).lower() and self._portal:
                    logger.log_message("debug", "Direct emit failed, trying portal approach")

                    # Define the emit task
                    async def emit_task():
                        try:
                            # In async context, we can safely emit
                            Emitter.emit(self._app_handle, "schedule-update", event_data)
                            logger.log_message("debug", f"Event emitted via portal: {event_type}")
                        except Exception as e2:
                            logger.log_message("error", f"Failed to emit via portal: {e2}")

                    # Check if we're in a thread that can use portal
                    try:
                        # Try to get the current event loop
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # We're in the event loop thread, schedule as a task
                            asyncio.create_task(emit_task())
                            logger.log_message("debug", "Scheduled emit as async task")
                        else:
                            # Event loop exists but not running, use portal
                            self._portal.start_task_soon(emit_task)
                            logger.log_message("debug", "Scheduled emit via portal")
                    except RuntimeError:
                        # No event loop in current thread, use portal
                        if self._portal:
                            self._portal.start_task_soon(emit_task)
                            logger.log_message("debug", "Scheduled emit via portal (no loop)")
                        else:
                            logger.log_message("error", "Cannot emit: no portal available")
                else:
                    logger.log_message("error", f"Failed to emit event: {e}")
            except Exception as e:
                logger.log_message("error", f"Unexpected error emitting event: {e}")

        except Exception as e:
            logger.log_message("error", f"Failed to prepare event: {e}")

    def emit_course_added(self, course_id: int, name: str) -> None:
        """Emit event when a course is added."""
        self.emit_schedule_update("course_added", {"id": course_id, "name": name})

    def emit_course_updated(self, course_id: int, **updates) -> None:
        """Emit event when a course is updated."""
        self.emit_schedule_update("course_updated", {"id": course_id, **updates})

    def emit_course_deleted(self, course_id: int) -> None:
        """Emit event when a course is deleted."""
        self.emit_schedule_update("course_deleted", {"id": course_id})

    def emit_schedule_added(self, entry_id: int, course_id: int, day: int, start: str, end: str) -> None:
        """Emit event when a schedule entry is added."""
        self.emit_schedule_update("schedule_added", {
            "id": entry_id,
            "course_id": course_id,
            "day_of_week": day,
            "start_time": start,
            "end_time": end
        })

    def emit_schedule_deleted(self, entry_id: int) -> None:
        """Emit event when a schedule entry is deleted."""
        self.emit_schedule_update("schedule_deleted", {"id": entry_id})

    def emit_settings_batch_updated(self, updated_keys: list) -> None:
        """Emit event when multiple settings are updated at once."""
        if not self._app_handle:
            logger.log_message("warning", "Event handler not initialized, cannot emit event")
            return

        try:
            event_data = SettingsBatchUpdateEvent(
                updated_keys=updated_keys,
                timestamp=datetime.now().isoformat()
            )
            Emitter.emit(self._app_handle, "settings-batch-update", event_data)
            logger.log_message("info", f"Settings batch update event emitted: {len(updated_keys)} settings")
        except Exception as e:
            logger.log_message("error", f"Failed to emit settings batch update event: {e}")

    def emit_camera_initialized(self, camera_count: int, encoder_info: Dict) -> None:
        """Emit event when camera system is initialized."""
        self.emit_string_event("camera-initialized",
                               f"Camera system initialized: {camera_count} cameras found")
        logger.log_message("info", f"Camera system initialized with {camera_count} cameras")

    def emit_camera_recording_started(self, camera_index: int, filename: str) -> None:
        """Emit event when recording starts."""
        self.emit_string_event("camera-recording-started",
                               f"Recording started on camera {camera_index}: {filename}")
        logger.log_message("info", f"Recording started: camera {camera_index} -> {filename}")

    def emit_camera_recording_stopped(self, camera_index: int) -> None:
        """Emit event when recording stops."""
        self.emit_string_event("camera-recording-stopped",
                               f"Recording stopped on camera {camera_index}")
        logger.log_message("info", f"Recording stopped on camera {camera_index}")

    def emit_custom_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Emit a custom event with arbitrary payload."""
        if not self._app_handle:
            logger.log_message("warning", "Event handler not initialized, cannot emit event")
            return

        try:
            Emitter.emit_str(self._app_handle, event_name, json.dumps(payload))
            logger.log_message("debug", f"Custom event emitted: {event_name}")
        except Exception as e:
            logger.log_message("error", f"Failed to emit custom event: {e}")

    @classmethod
    def get_instance(cls) -> Optional['EventHandler']:
        """Get the singleton instance of EventHandler."""
        return cls._instance

    @property
    def is_initialized(self) -> bool:
        """Check if the event handler is initialized."""
        return self._app_handle is not None


# Global event handler instance
event_handler = EventHandler()