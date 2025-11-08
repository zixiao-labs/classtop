"""
Tests for commands.py - PyTauri command handlers.
"""
import sys
from pathlib import Path
import pytest

# Add the python module to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from tauri_app import commands


class TestBasicCommands:
    """Test basic command handlers."""

    @pytest.mark.asyncio
    async def test_greet_command(self):
        """Test the greet command returns correct greeting."""
        person = commands.Person(name="TestUser")
        result = await commands.greet(person)

        assert isinstance(result, commands.Greeting)
        assert "TestUser" in result.message
        assert "Hello" in result.message

    @pytest.mark.asyncio
    async def test_log_message_command(self, mocker):
        """Test logging command calls logger correctly."""
        mock_logger = mocker.patch("tauri_app.commands._logger.log_message")

        log_req = commands.LogRequest(level="info", message="Test log message")
        result = await commands.log_message(log_req)

        assert result.ok is True
        mock_logger.assert_called_once_with("info", "Test log message")

    @pytest.mark.asyncio
    async def test_get_logs_command(self, mocker):
        """Test get_logs retrieves log lines."""
        mock_tail = mocker.patch(
            "tauri_app.commands._logger.tail_logs",
            return_value=["Log line 1", "Log line 2"]
        )

        log_req = commands.GetLogsRequest(max_lines=100)
        result = await commands.get_logs(log_req)

        assert isinstance(result, commands.LogsResponse)
        assert len(result.lines) == 2
        assert result.lines[0] == "Log line 1"
        mock_tail.assert_called_once_with(100)


class TestConfigCommands:
    """Test configuration command handlers."""

    @pytest.mark.asyncio
    async def test_set_config_command(self, mocker):
        """Test setting configuration value."""
        mock_set = mocker.patch("tauri_app.commands._db.set_config")

        req = commands.SetConfigRequest(key="test_key", value="test_value")
        result = await commands.set_config(req)

        assert result.key == "test_key"
        assert result.value == "test_value"
        mock_set.assert_called_once_with("test_key", "test_value")

    @pytest.mark.asyncio
    async def test_get_config_command(self, mocker):
        """Test getting configuration value."""
        mock_get = mocker.patch(
            "tauri_app.commands._db.get_config",
            return_value="retrieved_value"
        )

        req = commands.GetConfigRequest(key="test_key")
        result = await commands.get_config(req)

        assert result.key == "test_key"
        assert result.value == "retrieved_value"
        mock_get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_list_configs_command(self, mocker):
        """Test listing all configurations."""
        mock_list = mocker.patch(
            "tauri_app.commands._db.list_configs",
            return_value={"key1": "value1", "key2": "value2"}
        )

        result = await commands.list_configs()

        assert isinstance(result, dict)
        assert len(result) == 2
        assert result["key1"] == "value1"
        mock_list.assert_called_once()


class TestCourseCommands:
    """Test course management command handlers."""

    @pytest.mark.asyncio
    async def test_add_course_command(self, mocker):
        """Test adding a new course."""
        mock_add = mocker.patch("tauri_app.commands._db.add_course", return_value=1)

        req = commands.CourseRequest(
            name="Test Course",
            teacher="Test Teacher",
            location="Room 101",
            color="#FF5733"
        )
        result = await commands.add_course(req)

        assert isinstance(result, commands.CourseResponse)
        assert result.id == 1
        assert result.name == "Test Course"
        assert result.teacher == "Test Teacher"
        mock_add.assert_called_once_with("Test Course", "Test Teacher", "Room 101", "#FF5733")

    @pytest.mark.asyncio
    async def test_get_courses_command(self, mocker):
        """Test retrieving all courses."""
        mock_get = mocker.patch(
            "tauri_app.commands._db.get_courses",
            return_value=[
                {
                    "id": 1,
                    "name": "Course 1",
                    "teacher": "Teacher 1",
                    "location": "Room 1",
                    "color": "#FF0000"
                },
                {
                    "id": 2,
                    "name": "Course 2",
                    "teacher": "Teacher 2",
                    "location": "Room 2",
                    "color": "#00FF00"
                }
            ]
        )

        result = await commands.get_courses()

        assert len(result) == 2
        assert all(isinstance(c, commands.CourseResponse) for c in result)
        assert result[0].name == "Course 1"
        assert result[1].name == "Course 2"
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_course_command(self, mocker):
        """Test updating a course."""
        mock_update = mocker.patch("tauri_app.commands._db.update_course", return_value=True)

        update_data = {
            "id": 1,
            "name": "Updated Course",
            "teacher": "Updated Teacher"
        }
        result = await commands.update_course(update_data)

        assert result["success"] is True
        mock_update.assert_called_once_with(1, name="Updated Course", teacher="Updated Teacher")

    @pytest.mark.asyncio
    async def test_delete_course_command(self, mocker):
        """Test deleting a course."""
        mock_delete = mocker.patch("tauri_app.commands._db.delete_course", return_value=True)

        result = await commands.delete_course({"id": 1})

        assert result["success"] is True
        mock_delete.assert_called_once_with(1)


class TestScheduleCommands:
    """Test schedule management command handlers."""

    @pytest.mark.asyncio
    async def test_add_schedule_entry_command(self, mocker):
        """Test adding a schedule entry."""
        mock_add = mocker.patch("tauri_app.commands._db.add_schedule_entry", return_value=1)

        req = commands.ScheduleEntryRequest(
            course_id=1,
            day_of_week=1,
            start_time="09:00",
            end_time="10:30",
            weeks=[1, 2, 3, 4],
            note="Test note"
        )
        result = await commands.add_schedule_entry(req)

        assert result["id"] == 1
        assert result["success"] is True
        mock_add.assert_called_once_with(1, 1, "09:00", "10:30", [1, 2, 3, 4], "Test note")

    @pytest.mark.asyncio
    async def test_get_schedule_command(self, mocker):
        """Test retrieving schedule for a week."""
        mock_get = mocker.patch(
            "tauri_app.commands._db.get_schedule",
            return_value=[
                {
                    "id": 1,
                    "course_id": 1,
                    "course_name": "Test Course",
                    "teacher": "Test Teacher",
                    "location": "Room 101",
                    "color": "#FF5733",
                    "day_of_week": 1,
                    "start_time": "09:00",
                    "end_time": "10:30",
                    "weeks": [1, 2, 3],
                    "note": "Test note"
                }
            ]
        )

        req = commands.WeekRequest(week=1)
        result = await commands.get_schedule(req)

        assert len(result) == 1
        assert isinstance(result[0], commands.ScheduleEntryResponse)
        assert result[0].course_name == "Test Course"
        mock_get.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_schedule_entry_command(self, mocker):
        """Test deleting a schedule entry."""
        mock_delete = mocker.patch(
            "tauri_app.commands._db.delete_schedule_entry",
            return_value=True
        )

        result = await commands.delete_schedule_entry({"id": 1})

        assert result["success"] is True
        mock_delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_check_schedule_conflict_command_no_manager(self, mocker):
        """Test conflict check when schedule_manager is not available."""
        mocker.patch("tauri_app.commands._db.schedule_manager", None)

        req = commands.ConflictCheckRequest(
            day_of_week=1,
            start_time="09:00",
            end_time="10:30",
            weeks=[1, 2, 3]
        )
        result = await commands.check_schedule_conflict(req)

        assert isinstance(result, commands.ConflictCheckResponse)
        assert result.has_conflict is False
        assert len(result.conflicts) == 0

    @pytest.mark.asyncio
    async def test_check_schedule_conflict_command_with_conflicts(self, mocker):
        """Test conflict check detecting conflicts."""
        mock_manager = mocker.MagicMock()
        mock_manager.check_conflicts.return_value = [
            {
                "id": 2,
                "course_name": "Conflicting Course",
                "teacher": "Teacher",
                "location": "Room 102",
                "start_time": "09:30",
                "end_time": "11:00",
                "day_of_week": 1,
                "weeks": [1, 2, 3],
                "conflict_weeks": [1, 2]
            }
        ]
        mocker.patch("tauri_app.commands._db.schedule_manager", mock_manager)

        req = commands.ConflictCheckRequest(
            day_of_week=1,
            start_time="09:00",
            end_time="10:30",
            weeks=[1, 2, 3]
        )
        result = await commands.check_schedule_conflict(req)

        assert result.has_conflict is True
        assert len(result.conflicts) == 1
        assert result.conflicts[0].course_name == "Conflicting Course"
        assert result.conflicts[0].conflict_weeks == [1, 2]


class TestWeekCommands:
    """Test week calculation command handlers."""

    @pytest.mark.asyncio
    async def test_get_current_week_command(self, mocker):
        """Test getting current week number."""
        mock_get = mocker.patch(
            "tauri_app.commands._db.get_current_week",
            return_value=5
        )

        result = await commands.get_current_week()

        assert result["week"] == 5
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_calculated_week_number_command(self, mocker):
        """Test calculated week number retrieval."""
        from datetime import date

        mock_get = mocker.patch(
            "tauri_app.commands._db.get_calculated_week_number",
            return_value={
                "week": 5,
                "is_automatic": True,
                "semester_start_date": "2025-09-01",
                "today": str(date.today())
            }
        )

        result = await commands.get_calculated_week_number()

        assert result["week"] == 5
        assert result["is_automatic"] is True
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_semester_start_date_command(self, mocker):
        """Test setting semester start date."""
        mock_set = mocker.patch("tauri_app.commands._db.set_semester_start_date")

        req = commands.SetSemesterStartDateRequest(date="2025-09-01")
        result = await commands.set_semester_start_date(req)

        assert result["success"] is True
        mock_set.assert_called_once_with("2025-09-01")


class TestSettingsCommands:
    """Test settings command handlers."""

    @pytest.mark.asyncio
    async def test_get_all_settings_command(self, mocker):
        """Test getting all settings."""
        mock_manager = mocker.MagicMock()
        mock_manager.get_all_settings.return_value = {
            "current_week": "5",
            "total_weeks": "20"
        }
        mocker.patch("tauri_app.commands._db.settings_manager", mock_manager)

        result = await commands.get_all_settings()

        assert isinstance(result, dict)
        assert result["current_week"] == "5"
        mock_manager.get_all_settings.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_settings_command(self, mocker):
        """Test batch updating settings."""
        mock_manager = mocker.MagicMock()
        mocker.patch("tauri_app.commands._db.settings_manager", mock_manager)

        updates = {"current_week": "6", "total_weeks": "18"}
        result = await commands.update_settings(updates)

        assert result["success"] is True
        mock_manager.update_settings.assert_called_once_with(updates)

    @pytest.mark.asyncio
    async def test_reset_settings_command(self, mocker):
        """Test resetting settings to defaults."""
        mock_manager = mocker.MagicMock()
        mocker.patch("tauri_app.commands._db.settings_manager", mock_manager)

        result = await commands.reset_settings()

        assert result["success"] is True
        mock_manager.reset_to_defaults.assert_called_once()


class TestDeprecatedCommands:
    """Test deprecated command handlers."""

    @pytest.mark.asyncio
    async def test_get_current_class_deprecated(self, mocker):
        """Test deprecated get_current_class command."""
        mock_get = mocker.patch(
            "tauri_app.commands._db.get_current_class",
            return_value={
                "id": 1,
                "name": "Current Class",
                "teacher": "Teacher",
                "location": "Room 101",
                "start_time": "09:00",
                "end_time": "10:30",
                "color": "#FF5733"
            }
        )

        result = await commands.get_current_class()

        assert isinstance(result, commands.CurrentClassResponse)
        assert result.name == "Current Class"
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_class_none(self, mocker):
        """Test deprecated get_current_class when no class."""
        mock_get = mocker.patch("tauri_app.commands._db.get_current_class", return_value=None)

        result = await commands.get_current_class()

        assert result is None
        mock_get.assert_called_once()


class TestScheduleByDayCommands:
    """Test schedule by day command handlers."""

    @pytest.mark.asyncio
    async def test_get_schedule_by_day_command(self, mocker):
        """Test getting schedule for specific day."""
        mock_get = mocker.patch(
            "tauri_app.commands._db.get_schedule_by_day",
            return_value=[
                {
                    "id": 1,
                    "course_id": 1,
                    "course_name": "Morning Class",
                    "teacher": "Teacher",
                    "location": "Room 101",
                    "color": "#FF5733",
                    "day_of_week": 1,
                    "start_time": "09:00",
                    "end_time": "10:30",
                    "weeks": [1, 2, 3],
                    "note": None
                }
            ]
        )

        req = commands.ScheduleByDayRequest(day_of_week=1, week=1)
        result = await commands.get_schedule_by_day(req)

        assert len(result) == 1
        assert isinstance(result[0], commands.ScheduleEntryResponse)
        assert result[0].course_name == "Morning Class"
        mock_get.assert_called_once_with(1, 1)

    @pytest.mark.asyncio
    async def test_get_schedule_for_week_command(self, mocker):
        """Test getting full week schedule."""
        mock_get = mocker.patch(
            "tauri_app.commands._db.get_schedule_for_week",
            return_value={
                1: [],  # Monday
                2: [],  # Tuesday
                3: [],  # Wednesday
                4: [],  # Thursday
                5: [],  # Friday
                6: [],  # Saturday
                7: []   # Sunday
            }
        )

        req = commands.WeekRequest(week=1)
        result = await commands.get_schedule_for_week(req)

        assert isinstance(result, dict)
        assert len(result) == 7
        assert all(day in result for day in range(1, 8))
        mock_get.assert_called_once_with(1)
