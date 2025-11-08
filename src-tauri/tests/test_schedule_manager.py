"""
Unit tests for ScheduleManager (schedule_manager.py).
"""
import json
import pytest

from tauri_app.schedule_manager import ScheduleManager


class TestCourseManagement:
    """Tests for course management operations."""

    def test_add_course(self, initialized_schedule_manager, mock_event_handler):
        """Test adding a new course."""
        manager = initialized_schedule_manager

        course_id = manager.add_course(
            name="Test Course",
            teacher="Test Teacher",
            location="Room 101",
            color="#FF5733",
        )

        assert course_id > 0, "Course ID should be positive"

        # Verify course was added
        courses = manager.get_courses()
        assert len(courses) == 1
        assert courses[0]["name"] == "Test Course"
        assert courses[0]["teacher"] == "Test Teacher"
        assert courses[0]["location"] == "Room 101"
        assert courses[0]["color"] == "#FF5733"

        # Verify event was emitted
        mock_event_handler.emit_course_added.assert_called_once()

    def test_get_courses(self, initialized_schedule_manager):
        """Test getting all courses."""
        manager = initialized_schedule_manager

        # Add multiple courses
        manager.add_course("Course 1", "Teacher 1")
        manager.add_course("Course 2", "Teacher 2")
        manager.add_course("Course 3", "Teacher 3")

        courses = manager.get_courses()
        assert len(courses) == 3
        assert courses[0]["name"] == "Course 1"
        assert courses[1]["name"] == "Course 2"
        assert courses[2]["name"] == "Course 3"

    def test_update_course(self, initialized_schedule_manager, mock_event_handler):
        """Test updating course information."""
        manager = initialized_schedule_manager

        course_id = manager.add_course("Original Course")
        mock_event_handler.reset_mock()

        # Update course
        success = manager.update_course(
            course_id, name="Updated Course", teacher="New Teacher", color="#00FF00"
        )

        assert success is True

        # Verify update
        courses = manager.get_courses()
        assert courses[0]["name"] == "Updated Course"
        assert courses[0]["teacher"] == "New Teacher"
        assert courses[0]["color"] == "#00FF00"

        # Verify event was emitted
        mock_event_handler.emit_course_updated.assert_called_once()

    def test_update_nonexistent_course(self, initialized_schedule_manager):
        """Test updating a course that doesn't exist."""
        manager = initialized_schedule_manager

        success = manager.update_course(9999, name="Nonexistent")
        assert success is False

    def test_delete_course(self, initialized_schedule_manager, mock_event_handler):
        """Test deleting a course."""
        manager = initialized_schedule_manager

        course_id = manager.add_course("Course to Delete")
        mock_event_handler.reset_mock()

        # Delete course
        success = manager.delete_course(course_id)
        assert success is True

        # Verify deletion
        courses = manager.get_courses()
        assert len(courses) == 0

        # Verify event was emitted
        mock_event_handler.emit_course_deleted.assert_called_once()

    def test_delete_nonexistent_course(self, initialized_schedule_manager):
        """Test deleting a course that doesn't exist."""
        manager = initialized_schedule_manager

        success = manager.delete_course(9999)
        assert success is False


class TestScheduleManagement:
    """Tests for schedule management operations."""

    def test_add_schedule_entry(
        self, initialized_schedule_manager, mock_event_handler, sample_course
    ):
        """Test adding a schedule entry."""
        manager = initialized_schedule_manager

        course_id = manager.add_course(**sample_course)
        mock_event_handler.reset_mock()

        # Add schedule entry
        entry_id = manager.add_schedule_entry(
            course_id=course_id,
            day_of_week=1,  # Monday
            start_time="09:00",
            end_time="10:30",
            weeks=[1, 2, 3, 4, 5],
        )

        assert entry_id > 0, "Entry ID should be positive"

        # Verify event was emitted
        mock_event_handler.emit_schedule_added.assert_called_once()

    def test_get_schedule(self, initialized_schedule_manager, sample_course):
        """Test getting schedule entries."""
        manager = initialized_schedule_manager

        course_id = manager.add_course(**sample_course)

        # Add multiple schedule entries
        manager.add_schedule_entry(course_id, 1, "09:00", "10:30", [1, 2, 3])
        manager.add_schedule_entry(course_id, 2, "14:00", "15:30", [1, 2, 3])

        # Get all schedules
        schedules = manager.get_schedule()
        assert len(schedules) == 2

    def test_get_schedule_by_day(self, initialized_schedule_manager, sample_course):
        """Test getting schedule entries for a specific day."""
        manager = initialized_schedule_manager

        course_id = manager.add_course(**sample_course)

        # Add entries for different days
        manager.add_schedule_entry(course_id, 1, "09:00", "10:30", [1, 2, 3])
        manager.add_schedule_entry(course_id, 1, "14:00", "15:30", [1, 2, 3])
        manager.add_schedule_entry(course_id, 2, "09:00", "10:30", [1, 2, 3])

        # Get Monday's schedule
        monday_schedule = manager.get_schedule_by_day(1, week=1)
        assert len(monday_schedule) == 2
        assert all(entry["day_of_week"] == 1 for entry in monday_schedule)

        # Get Tuesday's schedule
        tuesday_schedule = manager.get_schedule_by_day(2, week=1)
        assert len(tuesday_schedule) == 1
        assert tuesday_schedule[0]["day_of_week"] == 2

    def test_get_schedule_for_week(self, initialized_schedule_manager, sample_course):
        """Test getting schedule for entire week."""
        manager = initialized_schedule_manager

        course_id = manager.add_course(**sample_course)

        # Add entries for different days
        for day in range(1, 6):  # Monday to Friday
            manager.add_schedule_entry(course_id, day, "09:00", "10:30", [1, 2, 3])

        # Get week 1 schedule
        week_schedule = manager.get_schedule_for_week(1)
        assert len(week_schedule) == 5

    def test_delete_schedule_entry(
        self, initialized_schedule_manager, mock_event_handler, sample_course
    ):
        """Test deleting a schedule entry."""
        manager = initialized_schedule_manager

        course_id = manager.add_course(**sample_course)
        entry_id = manager.add_schedule_entry(course_id, 1, "09:00", "10:30")
        mock_event_handler.reset_mock()

        # Delete entry
        success = manager.delete_schedule_entry(entry_id)
        assert success is True

        # Verify deletion
        schedules = manager.get_schedule()
        assert len(schedules) == 0

        # Verify event was emitted
        mock_event_handler.emit_schedule_deleted.assert_called_once()


class TestWeekCalculation:
    """Tests for week number calculation."""

    def test_calculate_week_number(self, initialized_schedule_manager):
        """Test week number calculation from semester start date."""
        from datetime import datetime, timedelta

        manager = initialized_schedule_manager

        # Test with a date 4 weeks ago
        start_date = (datetime.now() - timedelta(weeks=4)).strftime("%Y-%m-%d")
        week_num = manager.calculate_week_number(start_date)

        # Should be week 5 (4 complete weeks + current week)
        assert week_num == 5

    def test_calculate_week_number_same_day(self, initialized_schedule_manager):
        """Test week number calculation for semester start date = today."""
        from datetime import datetime

        manager = initialized_schedule_manager

        start_date = datetime.now().strftime("%Y-%m-%d")
        week_num = manager.calculate_week_number(start_date)

        # Should be week 1
        assert week_num == 1

    def test_calculate_week_number_future_date(self, initialized_schedule_manager):
        """Test week number calculation for future start date."""
        from datetime import datetime, timedelta

        manager = initialized_schedule_manager

        # Test with a date 2 weeks in the future
        start_date = (datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d")
        week_num = manager.calculate_week_number(start_date)

        # Should handle gracefully (might be 0 or negative, but shouldn't crash)
        assert isinstance(week_num, int)


class TestScheduleStatistics:
    """Tests for schedule statistics."""

    def test_get_statistics_empty(self, initialized_schedule_manager):
        """Test statistics with no data."""
        manager = initialized_schedule_manager

        stats = manager.get_statistics()

        assert stats["total_courses"] == 0
        assert stats["total_schedule_entries"] == 0

    def test_get_statistics_with_data(
        self, initialized_schedule_manager, sample_course
    ):
        """Test statistics with data."""
        manager = initialized_schedule_manager

        # Add courses and schedule entries
        course1_id = manager.add_course("Course 1")
        course2_id = manager.add_course("Course 2")

        manager.add_schedule_entry(course1_id, 1, "09:00", "10:30")
        manager.add_schedule_entry(course1_id, 2, "09:00", "10:30")
        manager.add_schedule_entry(course2_id, 1, "14:00", "15:30")

        stats = manager.get_statistics()

        assert stats["total_courses"] == 2
        assert stats["total_schedule_entries"] == 3
