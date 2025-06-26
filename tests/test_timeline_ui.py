"""Tests for timeline_ui module."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from rich.console import Console

from ccmonitor.claude_logs import SessionEvent, SessionTimeline
from ccmonitor.timeline_ui import TimelineUI


class TestTimelineUI:
    """Test TimelineUI class."""

    @pytest.fixture
    def timeline_ui(self):
        """Create TimelineUI instance for testing."""
        return TimelineUI()

    @pytest.fixture
    def sample_timeline(self):
        """Create sample timeline for testing."""
        base_time = datetime.now()
        events = []

        # Create some sample events
        for i in range(5):
            events.append(SessionEvent(
                timestamp=base_time + timedelta(minutes=i * 10),
                session_id="test_session",
                directory="/test/project",
                message_type="user" if i % 2 == 0 else "assistant",
                content_preview=f"Test message {i}",
                uuid=f"uuid-{i}",
            ))

        return SessionTimeline(
            session_id="test_session",
            directory="/test/project",
            project_name="test_project",
            events=events,
            start_time=base_time,
            end_time=base_time + timedelta(minutes=40),
            active_duration_minutes=30,
        )

    def test_timeline_ui_initialization(self, timeline_ui):
        """Test TimelineUI initialization."""
        assert isinstance(timeline_ui.console, Console)

    def test_create_header(self, timeline_ui):
        """Test header panel creation."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 14, 0, 0)
        session_count = 3

        header = timeline_ui._create_header(start_time, end_time, session_count)

        assert header is not None
        assert header.border_style == "blue"

    def test_create_timeline_string_basic(self, timeline_ui, sample_timeline):
        """Test timeline string creation."""
        start_time = sample_timeline.start_time
        end_time = sample_timeline.end_time
        width = 20

        timeline_str = timeline_ui._create_timeline_string(
            sample_timeline, start_time, end_time, width
        )

        # Should return a string of the specified width
        # Note: Rich markup tags make the actual length longer than visual width
        assert isinstance(timeline_str, str)
        # Check for presence of activity markers (■ characters)
        assert "■" in timeline_str

    def test_create_timeline_string_no_events(self, timeline_ui):
        """Test timeline string creation with no events."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        empty_timeline = SessionTimeline(
            session_id="empty",
            directory="/test",
            project_name="empty_project",
            events=[],
            start_time=start_time,
            end_time=end_time,
            active_duration_minutes=0,
        )

        timeline_str = timeline_ui._create_timeline_string(
            empty_timeline, start_time, end_time, 20
        )

        # Should return string with only idle markers (bright_black)
        assert isinstance(timeline_str, str)
        assert "bright_black" in timeline_str

    def test_determine_time_unit_and_interval_1_day(self, timeline_ui):
        """Test time unit determination for 1 day."""
        start_time = datetime.now()
        end_time = start_time + timedelta(days=1)
        width = 60

        unit, interval, format_str = timeline_ui._determine_time_unit_and_interval(
            start_time, end_time, width
        )

        assert unit == "hour"
        assert interval == 3  # 3-hour intervals for 1 day
        assert format_str == "%H"

    def test_determine_time_unit_and_interval_2_days(self, timeline_ui):
        """Test time unit determination for 2 days."""
        start_time = datetime.now()
        end_time = start_time + timedelta(days=2)
        width = 60

        unit, interval, format_str = timeline_ui._determine_time_unit_and_interval(
            start_time, end_time, width
        )

        assert unit == "hour"
        assert interval == 6  # 6-hour intervals for 2 days
        assert format_str == "%H"

    def test_determine_time_unit_and_interval_7_days(self, timeline_ui):
        """Test time unit determination for 7 days."""
        start_time = datetime.now()
        end_time = start_time + timedelta(days=7)
        width = 60

        unit, interval, format_str = timeline_ui._determine_time_unit_and_interval(
            start_time, end_time, width
        )

        assert unit == "day"
        assert interval == 1  # 1-day intervals for 7 days
        assert format_str == "%m/%d"

    def test_determine_time_unit_and_interval_30_days(self, timeline_ui):
        """Test time unit determination for 30 days."""
        start_time = datetime.now()
        end_time = start_time + timedelta(days=30)
        width = 60

        unit, interval, format_str = timeline_ui._determine_time_unit_and_interval(
            start_time, end_time, width
        )

        assert unit == "day"
        assert interval == 4  # 4-day intervals for 30 days
        assert format_str == "%m/%d"

    def test_determine_time_unit_and_interval_1_year(self, timeline_ui):
        """Test time unit determination for 1 year."""
        start_time = datetime.now()
        end_time = start_time + timedelta(days=400)
        width = 60

        unit, interval, format_str = timeline_ui._determine_time_unit_and_interval(
            start_time, end_time, width
        )

        assert unit == "year"
        assert interval == 365  # 1-year intervals
        assert format_str == "%Y"

    def test_create_time_axis_hours(self, timeline_ui):
        """Test time axis creation for hour-based display."""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 0, 0)
        width = 20

        axis_str = timeline_ui._create_time_axis(start_time, end_time, width)

        assert isinstance(axis_str, str)
        assert len(axis_str) == width
        # Should contain hour markers
        assert any(char.isdigit() for char in axis_str)

    def test_create_time_axis_days(self, timeline_ui):
        """Test time axis creation for day-based display."""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 7, 0, 0, 0)
        width = 30

        axis_str = timeline_ui._create_time_axis(start_time, end_time, width)

        assert isinstance(axis_str, str)
        assert len(axis_str) == width

    def test_create_summary_text(self, timeline_ui, sample_timeline):
        """Test summary text creation."""
        timelines = [sample_timeline]

        summary = timeline_ui.create_summary_text(timelines)

        assert summary is not None
        # Convert to string to check content
        summary_str = str(summary)
        assert "Summary Statistics" in summary_str
        assert "Total Projects" in summary_str
        assert "Total Events" in summary_str
        assert "Average Duration" in summary_str

    def test_create_summary_text_empty(self, timeline_ui):
        """Test summary text creation with empty timeline list."""
        summary = timeline_ui.create_summary_text([])

        # Should return empty text for empty list
        assert str(summary) == ""

    def test_create_timeline_panel(self, timeline_ui, sample_timeline):
        """Test timeline panel creation."""
        timelines = [sample_timeline]
        start_time = sample_timeline.start_time
        end_time = sample_timeline.end_time

        panel = timeline_ui._create_timeline_panel(timelines, start_time, end_time)

        assert panel is not None
        assert panel.title == "Project Activity"
        assert panel.border_style == "cyan"

    def test_display_timeline_with_timelines(self, timeline_ui, sample_timeline):
        """Test display_timeline with actual timelines."""
        timelines = [sample_timeline]
        start_time = sample_timeline.start_time
        end_time = sample_timeline.end_time

        with patch.object(timeline_ui.console, 'print') as mock_print:
            # Should not raise any exceptions
            timeline_ui.display_timeline(timelines, start_time, end_time)

            # Verify console.print was called
            assert mock_print.called

    def test_display_timeline_empty(self, timeline_ui):
        """Test display_timeline with empty timeline list."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        with patch.object(timeline_ui.console, 'print') as mock_print:
            timeline_ui.display_timeline([], start_time, end_time)

            # Should print "no sessions found" message
            assert mock_print.called

    def test_density_levels(self, timeline_ui, sample_timeline):
        """Test that different activity densities produce different colors."""
        # Create timeline with varying event densities
        base_time = datetime.now()
        events = []

        # Create clustered events (high density area)
        for i in range(10):
            events.append(SessionEvent(
                timestamp=base_time + timedelta(seconds=i * 30),  # 30 seconds apart
                session_id="dense_session",
                directory="/test",
                message_type="user" if i % 2 == 0 else "assistant",
                content_preview=f"Dense message {i}",
                uuid=f"dense-{i}",
            ))

        # Add sparse events
        for i in range(3):
            events.append(SessionEvent(
                timestamp=base_time + timedelta(minutes=30 + i * 20),  # 20 minutes apart
                session_id="sparse_session",
                directory="/test",
                message_type="user",
                content_preview=f"Sparse message {i}",
                uuid=f"sparse-{i}",
            ))

        dense_timeline = SessionTimeline(
            session_id="mixed_session",
            directory="/test",
            project_name="mixed_project",
            events=events,
            start_time=base_time,
            end_time=base_time + timedelta(hours=2),
            active_duration_minutes=60,
        )

        timeline_str = timeline_ui._create_timeline_string(
            dense_timeline, base_time, base_time + timedelta(hours=2), 40
        )

        # Should contain different color codes for different density levels
        assert "color(22)" in timeline_str or "color(28)" in timeline_str or \
               "color(34)" in timeline_str or "color(40)" in timeline_str
