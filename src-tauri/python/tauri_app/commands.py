"""
Command handlers for ClassTop application.
"""

import sys
import numpy as np
from typing import Optional, List, Dict

from pydantic import BaseModel
from pytauri import Commands
from pytauri.ipc import Channel, JavaScriptChannelId, WebviewWindow

from . import logger as _logger
from . import db as _db


# Command registration
commands: Commands = Commands()

# 全局存储 audio channel 以避免重复创建
_audio_channel = None


# Request/Response models
class Person(BaseModel):
    name: str


class Greeting(BaseModel):
    message: str


class LogRequest(BaseModel):
    level: Optional[str] = "info"
    message: str


class LogResponse(BaseModel):
    ok: bool


class LogsResponse(BaseModel):
    lines: List[str]


class SetConfigRequest(BaseModel):
    key: str
    value: str


class ConfigResponse(BaseModel):
    key: str
    value: Optional[str]


class GetLogsRequest(BaseModel):
    max_lines: Optional[int] = 200


class GetConfigRequest(BaseModel):
    key: str


# Command handlers
@commands.command()
async def greet(body: Person) -> Greeting:
    return Greeting(
        message=f"Hello, {body.name}! You've been greeted from Python {sys.version}!"
    )


@commands.command()
async def log_message(body: LogRequest) -> LogResponse:
    lvl = body.level or "info"
    _logger.log_message(lvl, body.message)
    return LogResponse(ok=True)


@commands.command()
async def get_logs(body: GetLogsRequest) -> LogsResponse:
    lines = _logger.tail_logs(int(body.max_lines or 200))
    return LogsResponse(lines=lines)


@commands.command()
async def set_config(body: SetConfigRequest) -> ConfigResponse:
    _db.set_config(body.key, body.value)
    return ConfigResponse(key=body.key, value=body.value)


@commands.command()
async def get_config(body: GetConfigRequest) -> ConfigResponse:
    val = _db.get_config(body.key)
    return ConfigResponse(key=body.key, value=val)


@commands.command()
async def list_configs() -> Dict[str, str]:
    return _db.list_configs()


# Schedule commands
class CourseRequest(BaseModel):
    name: str
    teacher: Optional[str] = None
    location: Optional[str] = None
    color: Optional[str] = None


class CourseResponse(BaseModel):
    id: int
    name: str
    teacher: Optional[str]
    location: Optional[str]
    color: Optional[str]


class ScheduleEntryRequest(BaseModel):
    course_id: int
    day_of_week: int
    start_time: str
    end_time: str
    weeks: Optional[List[int]] = None
    note: Optional[str] = None


class ScheduleEntryResponse(BaseModel):
    id: int
    course_id: int
    course_name: str
    teacher: Optional[str]
    location: Optional[str]
    color: Optional[str]
    day_of_week: int
    start_time: str
    end_time: str
    weeks: List[int]
    note: Optional[str]


class CurrentClassResponse(BaseModel):
    id: int
    name: str
    teacher: Optional[str]
    location: Optional[str]
    start_time: str
    end_time: str
    color: Optional[str]


class NextClassResponse(BaseModel):
    id: int
    name: str
    teacher: Optional[str]
    location: Optional[str]
    day_of_week: int
    start_time: str
    end_time: str
    color: Optional[str]


class WeekRequest(BaseModel):
    week: Optional[int] = None


@commands.command()
async def add_course(body: CourseRequest) -> CourseResponse:
    course_id = _db.add_course(body.name, body.teacher, body.location, body.color)
    return CourseResponse(
        id=course_id,
        name=body.name,
        teacher=body.teacher,
        location=body.location,
        color=body.color
    )


@commands.command()
async def get_courses() -> List[CourseResponse]:
    courses = _db.get_courses()
    return [CourseResponse(**course) for course in courses]


@commands.command()
async def update_course(body: Dict) -> Dict:
    course_id = body.pop("id")
    success = _db.update_course(course_id, **body)
    return {"success": success}


@commands.command()
async def delete_course(body: Dict) -> Dict:
    success = _db.delete_course(body["id"])
    return {"success": success}


@commands.command()
async def add_schedule_entry(body: ScheduleEntryRequest) -> Dict:
    entry_id = _db.add_schedule_entry(
        body.course_id,
        body.day_of_week,
        body.start_time,
        body.end_time,
        body.weeks,
        body.note
    )
    return {"id": entry_id, "success": entry_id > 0}


class ConflictCheckRequest(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    weeks: Optional[List[int]] = None
    exclude_entry_id: Optional[int] = None  # 编辑时排除当前课程


class ConflictEntry(BaseModel):
    id: int
    course_name: str
    teacher: Optional[str]
    location: Optional[str]
    start_time: str
    end_time: str
    day_of_week: int
    weeks: List[int]
    conflict_weeks: List[int]  # 实际冲突的周数


class ConflictCheckResponse(BaseModel):
    has_conflict: bool
    conflicts: List[ConflictEntry]


@commands.command()
async def check_schedule_conflict(body: ConflictCheckRequest) -> ConflictCheckResponse:
    """Check if a schedule entry conflicts with existing entries."""
    if not _db.schedule_manager:
        return ConflictCheckResponse(has_conflict=False, conflicts=[])

    conflicts = _db.schedule_manager.check_conflicts(
        body.day_of_week,
        body.start_time,
        body.end_time,
        body.weeks,
        body.exclude_entry_id
    )

    conflict_entries = [ConflictEntry(**conflict) for conflict in conflicts]

    return ConflictCheckResponse(
        has_conflict=len(conflict_entries) > 0,
        conflicts=conflict_entries
    )


@commands.command()
async def get_schedule(body: WeekRequest) -> List[ScheduleEntryResponse]:
    schedule = _db.get_schedule(body.week)
    return [ScheduleEntryResponse(**entry) for entry in schedule]


@commands.command()
async def delete_schedule_entry(body: Dict) -> Dict:
    success = _db.delete_schedule_entry(body["id"])
    return {"success": success}


@commands.command()
async def get_current_class() -> Optional[CurrentClassResponse]:
    """DEPRECATED: Use get_schedule_by_day and calculate on frontend."""
    current = _db.get_current_class()
    if current:
        return CurrentClassResponse(**current)
    return None


@commands.command()
async def get_next_class() -> Optional[NextClassResponse]:
    """DEPRECATED: Use get_schedule_by_day and calculate on frontend."""
    next_class = _db.get_next_class()
    if next_class:
        return NextClassResponse(**next_class)
    return None


@commands.command()
async def get_last_class() -> Optional[NextClassResponse]:
    """DEPRECATED: Use get_schedule_by_day and calculate on frontend."""
    last_class = _db.get_last_class()
    if last_class:
        return NextClassResponse(**last_class)
    return None


class ScheduleByDayRequest(BaseModel):
    day_of_week: int
    week: Optional[int] = None


@commands.command()
async def get_schedule_by_day(body: ScheduleByDayRequest) -> List[NextClassResponse]:
    """Get all classes for a specific day, optionally filtered by week."""
    classes = _db.get_schedule_by_day(body.day_of_week, body.week)
    return [NextClassResponse(**cls) for cls in classes]


@commands.command()
async def get_schedule_for_week(body: WeekRequest) -> List[NextClassResponse]:
    """Get all classes for the entire week."""
    classes = _db.get_schedule_for_week(body.week)
    return [NextClassResponse(**cls) for cls in classes]


@commands.command()
async def get_current_week() -> Dict:
    """Get the current week number, either calculated or manually set."""
    week = _db.get_calculated_week_number()
    semester_start = _db.get_config("semester_start_date")
    return {
        "week": week,
        "semester_start_date": semester_start,
        "is_calculated": bool(semester_start and semester_start.strip())
    }


@commands.command()
async def get_calculated_week_number() -> int:
    """Get current week number (calculated from semester start date or fallback to manual)."""
    return _db.get_calculated_week_number()


@commands.command()
async def set_semester_start_date(body: Dict) -> Dict:
    """Set the semester start date for automatic week calculation."""
    start_date = body.get("date", "")
    _db.set_config("semester_start_date", start_date)

    # Calculate and return the current week
    if start_date:
        week = _db.get_calculated_week_number()
        return {"success": True, "semester_start_date": start_date, "calculated_week": week}
    else:
        return {"success": True, "semester_start_date": "", "calculated_week": 1}


# ========== Settings Management Commands ==========

@commands.command()
async def get_all_settings() -> Dict[str, str]:
    """Get all application settings."""
    return _db.list_configs()


@commands.command()
async def update_settings(body: Dict) -> Dict:
    """Update multiple settings at once."""
    settings = body.get("settings", {})

    if not settings:
        return {"success": False, "message": "No settings provided"}

    # Update through settings manager if available
    if _db.settings_manager:
        success = _db.settings_manager.update_multiple(settings)
        return {"success": success}
    else:
        # Fallback to individual updates
        for key, value in settings.items():
            _db.set_config(key, str(value))
        return {"success": True}


@commands.command()
async def regenerate_uuid() -> Dict:
    """Regenerate client UUID."""
    if _db.settings_manager:
        new_uuid = _db.settings_manager.regenerate_uuid()
        return {"success": True, "uuid": new_uuid}
    else:
        import uuid
        new_uuid = str(uuid.uuid4())
        _db.set_config('client_uuid', new_uuid)
        return {"success": True, "uuid": new_uuid}


@commands.command()
async def reset_settings(body: Dict) -> Dict:
    """Reset settings to default values."""
    exclude_keys = body.get("exclude", [])

    if _db.settings_manager:
        success = _db.settings_manager.reset_to_defaults(exclude_keys)
        return {"success": success}
    else:
        return {"success": False, "message": "Settings manager not available"}


# Camera commands
class CameraInitResponse(BaseModel):
    success: bool
    camera_count: int
    message: str


class CameraListResponse(BaseModel):
    cameras: List[Dict]


class CameraEncodersResponse(BaseModel):
    h264: Dict
    h265: Dict


class StartRecordingRequest(BaseModel):
    camera_index: int
    filename: Optional[str] = None
    codec_type: Optional[str] = None  # 'H.264' or 'H.265'
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    preset: Optional[str] = None
    bitrate: Optional[str] = None


class RecordingResponse(BaseModel):
    success: bool
    message: str


class StopRecordingRequest(BaseModel):
    camera_index: int


class CameraStatusRequest(BaseModel):
    camera_index: Optional[int] = None


class CameraStatusResponse(BaseModel):
    status: Dict


@commands.command()
async def initialize_camera() -> CameraInitResponse:
    """Initialize camera monitoring system."""
    if not _db.camera_manager:
        return CameraInitResponse(
            success=False,
            camera_count=0,
            message="Camera manager not available"
        )

    success = _db.camera_manager.initialize()
    if success:
        cameras = _db.camera_manager.get_cameras()
        return CameraInitResponse(
            success=True,
            camera_count=len(cameras),
            message=f"Camera system initialized with {len(cameras)} cameras"
        )
    else:
        return CameraInitResponse(
            success=False,
            camera_count=0,
            message="Failed to initialize camera system"
        )


@commands.command()
async def get_cameras() -> CameraListResponse:
    """Get list of available cameras."""
    if not _db.camera_manager:
        return CameraListResponse(cameras=[])

    cameras = _db.camera_manager.get_cameras()
    return CameraListResponse(cameras=cameras)


@commands.command()
async def get_camera_encoders() -> CameraEncodersResponse:
    """Get available video encoders."""
    if not _db.camera_manager:
        return CameraEncodersResponse(
            h264={"available": 0, "encoders": [], "preferred": "libx264"},
            h265={"available": 0, "encoders": [], "preferred": "libx265"}
        )

    encoders = _db.camera_manager.get_encoders()
    return CameraEncodersResponse(**encoders)


@commands.command()
async def start_camera_recording(body: StartRecordingRequest) -> RecordingResponse:
    """Start recording from camera."""
    if not _db.camera_manager:
        return RecordingResponse(
            success=False,
            message="Camera manager not available"
        )

    success = _db.camera_manager.start_recording(
        camera_index=body.camera_index,
        filename=body.filename,
        codec_type=body.codec_type,
        width=body.width,
        height=body.height,
        fps=body.fps,
        preset=body.preset,
        bitrate=body.bitrate
    )

    if success:
        return RecordingResponse(
            success=True,
            message=f"Recording started on camera {body.camera_index}"
        )
    else:
        return RecordingResponse(
            success=False,
            message=f"Failed to start recording on camera {body.camera_index}"
        )


@commands.command()
async def stop_camera_recording(body: StopRecordingRequest) -> RecordingResponse:
    """Stop recording from camera."""
    if not _db.camera_manager:
        return RecordingResponse(
            success=False,
            message="Camera manager not available"
        )

    success = _db.camera_manager.stop_recording(body.camera_index)

    if success:
        return RecordingResponse(
            success=True,
            message=f"Recording stopped on camera {body.camera_index}"
        )
    else:
        return RecordingResponse(
            success=False,
            message=f"Failed to stop recording on camera {body.camera_index}"
        )


@commands.command()
async def get_camera_status(body: CameraStatusRequest) -> CameraStatusResponse:
    """Get camera status."""
    if not _db.camera_manager:
        return CameraStatusResponse(status={"active_cameras": 0, "streamers": {}})

    status = _db.camera_manager.get_status(body.camera_index)
    return CameraStatusResponse(status=status)


# ========== Audio Monitoring Commands ==========

class AudioLevelData(BaseModel):
    """音频响度数据 - 用于 Channel 传输"""
    timestamp: str  # ISO format datetime string
    rms: float      # 均方根值 (0-1)
    db: float       # 分贝值
    peak: float     # 峰值 (0-1)
    source: str     # 数据源: "microphone" or "system"


class StartAudioMonitoringRequest(BaseModel):
    """启动音频监控请求"""
    monitor_type: str  # "microphone" or "system" or "both"
    channel_id: JavaScriptChannelId[AudioLevelData]  # Channel ID from frontend


class StopAudioMonitoringRequest(BaseModel):
    """停止音频监控请求"""
    monitor_type: str  # "microphone" or "system" or "all"


class AudioMonitoringResponse(BaseModel):
    """音频监控响应"""
    success: bool
    message: str


class AudioDevicesResponse(BaseModel):
    """音频设备列表响应"""
    input_devices: List[Dict]
    output_devices: List[Dict]


@commands.command()
async def start_audio_monitoring(
    body: StartAudioMonitoringRequest,
    webview_window: WebviewWindow
) -> AudioMonitoringResponse:
    """启动音频监控并通过 Channel 实时传输数据"""
    global _audio_channel

    if not _db.audio_manager:
        return AudioMonitoringResponse(
            success=False,
            message="Audio manager not available"
        )

    try:
        # 复用或创建 Channel 对象
        if _audio_channel is None:
            _audio_channel = body.channel_id.channel_on(webview_window.as_ref_webview())

        channel = _audio_channel

        if body.monitor_type == "microphone":
            def mic_callback(level):
                try:
                    # 确保 db 值是有限数值，避免 JSON 序列化问题
                    db_value = level.db if np.isfinite(level.db) else -100.0

                    data = AudioLevelData(
                        timestamp=level.timestamp.isoformat(),
                        rms=level.rms,
                        db=db_value,
                        peak=level.peak,
                        source="microphone"
                    )
                    channel.send_model(data)
                except Exception as e:
                    _logger.log_message("error", f"Failed to send mic audio data: {e}")

            _db.audio_manager.start_microphone_monitoring(callback=mic_callback)
            return AudioMonitoringResponse(
                success=True,
                message="Microphone monitoring started"
            )
        elif body.monitor_type == "system":
            def sys_callback(level):
                try:
                    # 确保 db 值是有限数值，避免 JSON 序列化问题
                    db_value = level.db if np.isfinite(level.db) else -100.0

                    data = AudioLevelData(
                        timestamp=level.timestamp.isoformat(),
                        rms=level.rms,
                        db=db_value,
                        peak=level.peak,
                        source="system"
                    )
                    channel.send_model(data)
                except Exception as e:
                    _logger.log_message("error", f"Failed to send sys audio data: {e}")

            _db.audio_manager.start_system_monitoring(callback=sys_callback)
            return AudioMonitoringResponse(
                success=True,
                message="System audio monitoring started"
            )
        elif body.monitor_type == "both":
            # 为 both 模式创建两个不同的 callback
            def mic_callback(level):
                try:
                    # 确保 db 值是有限数值，避免 JSON 序列化问题
                    db_value = level.db if np.isfinite(level.db) else -100.0

                    data = AudioLevelData(
                        timestamp=level.timestamp.isoformat(),
                        rms=level.rms,
                        db=db_value,
                        peak=level.peak,
                        source="microphone"
                    )
                    channel.send_model(data)
                except Exception as e:
                    _logger.log_message("error", f"Failed to send mic audio data: {e}")

            def sys_callback(level):
                try:
                    # 确保 db 值是有限数值，避免 JSON 序列化问题
                    db_value = level.db if np.isfinite(level.db) else -100.0

                    data = AudioLevelData(
                        timestamp=level.timestamp.isoformat(),
                        rms=level.rms,
                        db=db_value,
                        peak=level.peak,
                        source="system"
                    )
                    channel.send_model(data)
                except Exception as e:
                    _logger.log_message("error", f"Failed to send sys audio data: {e}")

            _db.audio_manager.start_all(
                mic_callback=mic_callback,
                sys_callback=sys_callback
            )
            return AudioMonitoringResponse(
                success=True,
                message="Both microphone and system monitoring started"
            )
        else:
            return AudioMonitoringResponse(
                success=False,
                message=f"Invalid monitor_type: {body.monitor_type}"
            )
    except Exception as e:
        _logger.log_message("error", f"Failed to start audio monitoring: {e}")
        return AudioMonitoringResponse(
            success=False,
            message=str(e)
        )


@commands.command()
async def stop_audio_monitoring(body: StopAudioMonitoringRequest) -> AudioMonitoringResponse:
    """停止音频监控"""
    global _audio_channel

    if not _db.audio_manager:
        return AudioMonitoringResponse(
            success=False,
            message="Audio manager not available"
        )

    try:
        if body.monitor_type == "microphone":
            _db.audio_manager.stop_microphone_monitoring()
            return AudioMonitoringResponse(
                success=True,
                message="Microphone monitoring stopped"
            )
        elif body.monitor_type == "system":
            _db.audio_manager.stop_system_monitoring()
            return AudioMonitoringResponse(
                success=True,
                message="System audio monitoring stopped"
            )
        elif body.monitor_type == "all":
            _db.audio_manager.stop_all()
            # 当停止所有监控时，清理 channel
            _audio_channel = None
            return AudioMonitoringResponse(
                success=True,
                message="All audio monitoring stopped"
            )
        else:
            return AudioMonitoringResponse(
                success=False,
                message=f"Invalid monitor_type: {body.monitor_type}"
            )
    except Exception as e:
        _logger.log_message("error", f"Failed to stop audio monitoring: {e}")
        return AudioMonitoringResponse(
            success=False,
            message=str(e)
        )


@commands.command()
async def get_audio_devices() -> AudioDevicesResponse:
    """获取所有可用的音频设备"""
    try:
        from .audio_manager import AudioManager
        devices = AudioManager.list_devices()
        return AudioDevicesResponse(
            input_devices=devices.get("input", []),
            output_devices=devices.get("output", [])
        )
    except Exception as e:
        _logger.log_message("error", f"Failed to list audio devices: {e}")
        return AudioDevicesResponse(
            input_devices=[],
            output_devices=[]
        )


# ========== Theme Commands ==========

class DownloadThemeImageResponse(BaseModel):
    """Response for downloading theme image from GitHub"""
    success: bool
    image_data: Optional[str] = None  # base64 encoded image
    image_name: Optional[str] = None
    message: str


@commands.command()
async def download_random_theme_image() -> DownloadThemeImageResponse:
    """Download a random image from color_ref folder on GitHub for theme generation."""
    try:
        import urllib.request
        import base64
        import random
        import json

        # GitHub API endpoint for color_ref folder
        api_url = "https://api.github.com/repos/Zixiao-System/classtop/contents/color_ref"

        _logger.log_message("info", "Fetching color_ref folder from GitHub...")

        # Fetch folder contents
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'ClassTop-Dynamic-Theme/1.0')

        with urllib.request.urlopen(req, timeout=10) as response:
            files = json.loads(response.read().decode('utf-8'))

        # Filter image files
        image_files = [f for f in files if f['type'] == 'file' and
                      f['name'].lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not image_files:
            return DownloadThemeImageResponse(
                success=False,
                message="No image files found in color_ref folder"
            )

        # Select random image
        selected_image = random.choice(image_files)
        image_url = selected_image['download_url']
        image_name = selected_image['name']

        _logger.log_message("info", f"Downloading theme image: {image_name}")

        # Download image
        req = urllib.request.Request(image_url)
        req.add_header('User-Agent', 'ClassTop-Dynamic-Theme/1.0')

        with urllib.request.urlopen(req, timeout=30) as response:
            image_data = response.read()

        # Encode to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        _logger.log_message("info", f"Successfully downloaded theme image: {image_name}")

        return DownloadThemeImageResponse(
            success=True,
            image_data=image_base64,
            image_name=image_name,
            message=f"Successfully downloaded {image_name}"
        )

    except urllib.error.URLError as e:
        _logger.log_message("error", f"Network error downloading theme image: {e}")
        return DownloadThemeImageResponse(
            success=False,
            message=f"Network error: {str(e)}"
        )
    except Exception as e:
        _logger.log_message("error", f"Failed to download theme image: {e}")
        return DownloadThemeImageResponse(
            success=False,
            message=f"Failed to download theme image: {str(e)}"
        )


# ========== Data Import/Export Commands ==========

class ExportDataRequest(BaseModel):
    format: str  # "json" or "csv"
    include_courses: bool = True
    include_schedule: bool = True
    include_settings: bool = False


class ExportDataResponse(BaseModel):
    success: bool
    data: Optional[str] = None
    message: str


class ImportDataRequest(BaseModel):
    format: str  # "json" or "csv"
    data: str
    replace_existing: bool = False  # 是否替换现有数据


class ImportDataResponse(BaseModel):
    success: bool
    message: str
    courses_imported: int = 0
    schedule_imported: int = 0


@commands.command()
async def export_schedule_data(body: ExportDataRequest) -> ExportDataResponse:
    """Export schedule data to JSON or CSV format."""
    try:
        import json
        import csv
        import io

        data_dict = {}

        # Export courses
        if body.include_courses:
            courses = _db.get_courses()
            data_dict['courses'] = courses

        # Export schedule
        if body.include_schedule:
            schedule = _db.get_schedule(week=None)
            data_dict['schedule'] = schedule

        # Export settings (optional)
        if body.include_settings:
            settings = _db.list_configs()
            # Exclude sensitive settings
            safe_settings = {k: v for k, v in settings.items()
                           if k not in ['client_uuid', 'server_url', 'api_server_enabled']}
            data_dict['settings'] = safe_settings

        if body.format == 'json':
            # Export as JSON
            json_data = json.dumps(data_dict, ensure_ascii=False, indent=2)
            return ExportDataResponse(
                success=True,
                data=json_data,
                message="数据已导出为 JSON 格式"
            )

        elif body.format == 'csv':
            # Export as CSV (schedule entries only)
            output = io.StringIO()
            writer = csv.writer(output)

            # Write CSV header
            writer.writerow([
                'course_id', 'course_name', 'teacher', 'location', 'color',
                'day_of_week', 'start_time', 'end_time', 'weeks', 'note'
            ])

            # Write schedule entries
            for entry in data_dict.get('schedule', []):
                writer.writerow([
                    entry.get('course_id', ''),
                    entry.get('course_name', ''),
                    entry.get('teacher', ''),
                    entry.get('location', ''),
                    entry.get('color', ''),
                    entry.get('day_of_week', ''),
                    entry.get('start_time', ''),
                    entry.get('end_time', ''),
                    json.dumps(entry.get('weeks', [])),
                    entry.get('note', '')
                ])

            csv_data = output.getvalue()
            return ExportDataResponse(
                success=True,
                data=csv_data,
                message="数据已导出为 CSV 格式"
            )

        else:
            return ExportDataResponse(
                success=False,
                message=f"不支持的导出格式: {body.format}"
            )

    except Exception as e:
        _logger.log_message("error", f"Failed to export data: {e}")
        return ExportDataResponse(
            success=False,
            message=f"导出失败: {str(e)}"
        )


@commands.command()
async def import_schedule_data(body: ImportDataRequest) -> ImportDataResponse:
    """Import schedule data from JSON or CSV format."""
    try:
        import json
        import csv
        import io

        courses_imported = 0
        schedule_imported = 0

        if body.format == 'json':
            # Parse JSON data
            data_dict = json.loads(body.data)

            # Clear existing data if requested
            if body.replace_existing:
                # Delete all schedule entries and courses
                all_courses = _db.get_courses()
                for course in all_courses:
                    _db.delete_course(course['id'])

            # Import courses
            if 'courses' in data_dict:
                course_id_map = {}  # Map old IDs to new IDs
                for course_data in data_dict['courses']:
                    # Remove ID to create new course
                    course_name = course_data.get('name')
                    teacher = course_data.get('teacher')
                    location = course_data.get('location')
                    color = course_data.get('color')

                    new_id = _db.add_course(course_name, teacher, location, color)
                    if new_id > 0:
                        old_id = course_data.get('id')
                        course_id_map[old_id] = new_id
                        courses_imported += 1

            # Import schedule entries
            if 'schedule' in data_dict:
                for entry_data in data_dict['schedule']:
                    old_course_id = entry_data.get('course_id')
                    new_course_id = course_id_map.get(old_course_id)

                    if new_course_id:
                        entry_id = _db.add_schedule_entry(
                            course_id=new_course_id,
                            day_of_week=entry_data.get('day_of_week'),
                            start_time=entry_data.get('start_time'),
                            end_time=entry_data.get('end_time'),
                            weeks=entry_data.get('weeks'),
                            note=entry_data.get('note')
                        )
                        if entry_id > 0:
                            schedule_imported += 1

            return ImportDataResponse(
                success=True,
                message=f"成功导入 {courses_imported} 门课程和 {schedule_imported} 条课程表",
                courses_imported=courses_imported,
                schedule_imported=schedule_imported
            )

        elif body.format == 'csv':
            # Parse CSV data
            reader = csv.DictReader(io.StringIO(body.data))

            # Clear existing data if requested
            if body.replace_existing:
                all_courses = _db.get_courses()
                for course in all_courses:
                    _db.delete_course(course['id'])

            # Map to track created courses
            course_map = {}  # name -> course_id

            for row in reader:
                course_name = row.get('course_name', '').strip()
                if not course_name:
                    continue

                # Create or get course
                if course_name not in course_map:
                    course_id = _db.add_course(
                        name=course_name,
                        teacher=row.get('teacher'),
                        location=row.get('location'),
                        color=row.get('color')
                    )
                    if course_id > 0:
                        course_map[course_name] = course_id
                        courses_imported += 1
                else:
                    course_id = course_map[course_name]

                # Add schedule entry
                try:
                    weeks_str = row.get('weeks', '[]')
                    weeks = json.loads(weeks_str) if weeks_str else None
                except:
                    weeks = None

                entry_id = _db.add_schedule_entry(
                    course_id=course_id,
                    day_of_week=int(row.get('day_of_week', 1)),
                    start_time=row.get('start_time'),
                    end_time=row.get('end_time'),
                    weeks=weeks,
                    note=row.get('note')
                )
                if entry_id > 0:
                    schedule_imported += 1

            return ImportDataResponse(
                success=True,
                message=f"成功导入 {courses_imported} 门课程和 {schedule_imported} 条课程表",
                courses_imported=courses_imported,
                schedule_imported=schedule_imported
            )

        else:
            return ImportDataResponse(
                success=False,
                message=f"不支持的导入格式: {body.format}"
            )

    except Exception as e:
        _logger.log_message("error", f"Failed to import data: {e}")
        return ImportDataResponse(
            success=False,
            message=f"导入失败: {str(e)}"
        )


# ============= Management Server Sync Commands =============

class SyncResponse(BaseModel):
    success: bool
    message: str


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None


@commands.command()
async def test_server_connection() -> TestConnectionResponse:
    """测试与 Management Server 的连接"""
    try:
        # 从 db 模块获取 sync_client
        if _db.sync_client:
            result = _db.sync_client.test_connection()
        else:
            # 如果没有初始化，创建临时实例
            from .sync_client import SyncClient
            sync_client = SyncClient(_db.settings_manager, _db.schedule_manager)
            result = sync_client.test_connection()

        return TestConnectionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            data=result.get("data")
        )
    except Exception as e:
        _logger.log_message("error", f"Failed to test server connection: {e}")
        return TestConnectionResponse(
            success=False,
            message=f"测试连接失败: {str(e)}"
        )


@commands.command()
async def sync_now() -> SyncResponse:
    """立即同步数据到 Management Server"""
    try:
        # 从 db 模块获取 sync_client
        if _db.sync_client:
            success = _db.sync_client.sync_to_server()
        else:
            # 如果没有初始化，创建临时实例
            from .sync_client import SyncClient
            sync_client = SyncClient(_db.settings_manager, _db.schedule_manager)
            success = sync_client.sync_to_server()

        return SyncResponse(
            success=success,
            message="同步成功" if success else "同步失败"
        )
    except Exception as e:
        _logger.log_message("error", f"Failed to sync: {e}")
        return SyncResponse(
            success=False,
            message=f"同步失败: {str(e)}"
        )


@commands.command()
async def register_to_server() -> SyncResponse:
    """注册客户端到 Management Server"""
    try:
        # 从 db 模块获取 sync_client
        if _db.sync_client:
            success = _db.sync_client.register_client()
        else:
            # 如果没有初始化，创建临时实例
            from .sync_client import SyncClient
            sync_client = SyncClient(_db.settings_manager, _db.schedule_manager)
            success = sync_client.register_client()

        return SyncResponse(
            success=success,
            message="注册成功" if success else "注册失败"
        )
    except Exception as e:
        _logger.log_message("error", f"Failed to register: {e}")
        return SyncResponse(
            success=False,
            message=f"注册失败: {str(e)}"
        )


class SyncStatusResponse(BaseModel):
    enabled: bool
    connected: bool
    server_url: str
    last_sync_time: Optional[str] = None


@commands.command()
async def get_sync_status() -> SyncStatusResponse:
    """获取 Management Server 同步状态"""
    try:
        sync_enabled = _db.settings_manager.get_setting_bool("sync_enabled", False)
        server_url = _db.settings_manager.get_setting("server_url", "")

        # 检查连接状态
        connected = False
        if sync_enabled and server_url and _db.sync_client:
            result = _db.sync_client.test_connection()
            connected = result.get("success", False)

        return SyncStatusResponse(
            enabled=sync_enabled,
            connected=connected,
            server_url=server_url,
            last_sync_time=None  # 可以后续添加最后同步时间的跟踪
        )
    except Exception as e:
        _logger.log_message("error", f"Failed to get sync status: {e}")
        return SyncStatusResponse(
            enabled=False,
            connected=False,
            server_url=""
        )


# Bidirectional Sync Commands
class PullDataResponse(BaseModel):
    success: bool
    message: str
    courses_count: int = 0
    entries_count: int = 0


@commands.command()
async def pull_from_server() -> PullDataResponse:
    """从 Management Server 下载数据"""
    try:
        if not _db.sync_client:
            return PullDataResponse(
                success=False,
                message="同步客户端未初始化"
            )

        result = _db.sync_client.download_from_server()
        if result.get("success"):
            # 应用下载的数据到本地
            apply_success = _db.sync_client.apply_server_data(result)
            if apply_success:
                return PullDataResponse(
                    success=True,
                    message="下载并应用数据成功",
                    courses_count=len(result.get("courses", [])),
                    entries_count=len(result.get("schedule_entries", []))
                )
            else:
                return PullDataResponse(
                    success=False,
                    message="应用数据失败"
                )
        else:
            return PullDataResponse(
                success=False,
                message=result.get("message", "下载失败")
            )
    except Exception as e:
        _logger.log_message("error", f"Pull from server failed: {e}")
        return PullDataResponse(
            success=False,
            message=f"下载失败: {str(e)}"
        )


class ConflictItem(BaseModel):
    id: int
    local: Dict
    server: Dict


class CheckConflictsResponse(BaseModel):
    success: bool
    message: str
    has_conflicts: bool = False
    conflicted_courses: List[ConflictItem] = []
    conflicted_entries: List[ConflictItem] = []


@commands.command()
async def check_sync_conflicts() -> CheckConflictsResponse:
    """检查本地和服务器数据冲突"""
    try:
        if not _db.sync_client:
            return CheckConflictsResponse(
                success=False,
                message="同步客户端未初始化"
            )

        # 下载服务器数据
        server_result = _db.sync_client.download_from_server()
        if not server_result.get("success"):
            return CheckConflictsResponse(
                success=False,
                message=f"下载服务器数据失败: {server_result.get('message')}"
            )

        server_data = {
            "courses": server_result.get("courses", []),
            "schedule_entries": server_result.get("schedule_entries", [])
        }

        # 获取本地数据
        local_data = {
            "courses": _db.schedule_manager.get_all_courses(),
            "schedule_entries": _db.schedule_manager.get_all_schedule_entries()
        }

        # 检测冲突
        conflicts = _db.sync_client.detect_conflicts(local_data, server_data)

        return CheckConflictsResponse(
            success=True,
            message="冲突检测完成",
            has_conflicts=conflicts.get("has_conflicts", False),
            conflicted_courses=[
                ConflictItem(**item) for item in conflicts.get("conflicted_courses", [])
            ],
            conflicted_entries=[
                ConflictItem(**item) for item in conflicts.get("conflicted_entries", [])
            ]
        )

    except Exception as e:
        _logger.log_message("error", f"Check conflicts failed: {e}")
        return CheckConflictsResponse(
            success=False,
            message=f"检测冲突失败: {str(e)}"
        )


class BidirectionalSyncRequest(BaseModel):
    strategy: str = "server_wins"  # "server_wins", "local_wins", "newest_wins"


class BidirectionalSyncResponse(BaseModel):
    success: bool
    message: str
    conflicts_found: int = 0
    courses_updated: int = 0
    entries_updated: int = 0


@commands.command()
async def bidirectional_sync_now(body: BidirectionalSyncRequest) -> BidirectionalSyncResponse:
    """执行双向同步（包含冲突解决）"""
    try:
        if not _db.sync_client:
            return BidirectionalSyncResponse(
                success=False,
                message="同步客户端未初始化"
            )

        result = _db.sync_client.bidirectional_sync(strategy=body.strategy)

        return BidirectionalSyncResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            conflicts_found=result.get("conflicts_found", 0),
            courses_updated=result.get("courses_updated", 0),
            entries_updated=result.get("entries_updated", 0)
        )

    except Exception as e:
        _logger.log_message("error", f"Bidirectional sync failed: {e}")
        return BidirectionalSyncResponse(
            success=False,
            message=f"双向同步失败: {str(e)}"
        )



