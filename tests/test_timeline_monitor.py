"""Tests for timeline_monitor module."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from rich.console import Console

from ccmonitor.claude_logs import SessionTimeline
from ccmonitor.timeline_monitor import TimelineMonitor


class TestTimelineMonitor:
    """Test TimelineMonitor class."""

    def test_timeline_monitor_initialization_defaults(self):
        """Test TimelineMonitor initialization with default parameters."""
        monitor = TimelineMonitor()

        assert monitor.days == 1
        assert monitor.project is None
        assert monitor.threads is False
        assert isinstance(monitor.console, Console)

    def test_timeline_monitor_initialization_custom(self):
        """Test TimelineMonitor initialization with custom parameters."""
        monitor = TimelineMonitor(days=7, project="test_project", threads=True)

        assert monitor.days == 7
        assert monitor.project == "test_project"
        assert monitor.threads is True

    @patch("ccmonitor.timeline_monitor.load_sessions_in_timerange")
    @patch("ccmonitor.timeline_monitor.TimelineUI")
    def test_run_success(self, mock_timeline_ui, mock_load_sessions):
        """Test successful run of timeline monitor."""
        # Setup mocks
        mock_timeline = SessionTimeline(
            session_id="test",
            directory="/test",
            project_name="test_project",
            events=[],
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            active_duration_minutes=30,
        )
        mock_load_sessions.return_value = [mock_timeline]

        mock_ui_instance = Mock()
        mock_timeline_ui.return_value = mock_ui_instance

        # Create monitor and run
        monitor = TimelineMonitor(days=1)
        monitor.run()

        # Verify load_sessions_in_timerange was called with correct parameters
        assert mock_load_sessions.called
        call_args = mock_load_sessions.call_args
        start_time, end_time = call_args[0]

        # Check that time range is approximately 1 day
        time_diff = end_time - start_time
        assert abs(time_diff.total_seconds() - 86400) < 60  # Within 1 minute of 24 hours

        # Verify UI display was called
        mock_ui_instance.display_timeline.assert_called_once()

    @patch("ccmonitor.timeline_monitor.load_sessions_in_timerange")
    def test_run_with_project_filter(self, mock_load_sessions):
        """Test run with project filter."""
        mock_load_sessions.return_value = []

        monitor = TimelineMonitor(days=3, project="specific_project")

        with patch.object(monitor.console, "print") as mock_print:
            with patch.object(monitor.console, "clear"):
                monitor.run()

        # Verify project filter was passed
        call_args = mock_load_sessions.call_args
        assert call_args[1]["project_filter"] == "specific_project"

        # Verify loading message includes project filter
        mock_print.assert_called()
        loading_call = mock_print.call_args_list[0]
        assert "specific_project" in str(loading_call)

    @patch("ccmonitor.timeline_monitor.load_sessions_in_timerange")
    def test_run_with_threads_mode(self, mock_load_sessions):
        """Test run with threads mode enabled."""
        mock_load_sessions.return_value = []

        monitor = TimelineMonitor(days=5, threads=True)

        with patch.object(monitor.console, "print"):
            with patch.object(monitor.console, "clear"):
                monitor.run()

        # Verify threads mode was passed
        call_args = mock_load_sessions.call_args
        assert call_args[1]["threads"] is True

    @patch("ccmonitor.timeline_monitor.load_sessions_in_timerange")
    def test_run_exception_handling(self, mock_load_sessions):
        """Test exception handling in run method."""
        # Make load_sessions_in_timerange raise an exception
        mock_load_sessions.side_effect = Exception("Test error")

        monitor = TimelineMonitor()

        with patch.object(monitor.console, "print") as mock_print:
            monitor.run()

        # Verify error message was printed
        error_calls = [call for call in mock_print.call_args_list if "Error loading sessions" in str(call)]
        assert len(error_calls) > 0

    def test_time_range_calculation(self):
        """Test that time range calculation is correct."""
        monitor = TimelineMonitor(days=7)

        # Patch datetime.now to control the current time
        fixed_now = datetime(2024, 1, 15, 14, 30, 0)

        with patch("ccmonitor.timeline_monitor.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now

            with patch("ccmonitor.timeline_monitor.load_sessions_in_timerange") as mock_load:
                mock_load.return_value = []

                with patch.object(monitor.console, "print"):
                    with patch.object(monitor.console, "clear"):
                        monitor.run()

                # Check the time range passed to load_sessions_in_timerange
                call_args = mock_load.call_args[0]
                start_time, end_time = call_args

                assert end_time == fixed_now
                expected_start = fixed_now - timedelta(days=7)
                assert start_time == expected_start

    @patch("ccmonitor.timeline_monitor.load_sessions_in_timerange")
    def test_console_clearing(self, mock_load_sessions):
        """Test that console is cleared before displaying results."""
        mock_load_sessions.return_value = []

        monitor = TimelineMonitor()

        with patch.object(monitor.console, "clear") as mock_clear:
            with patch.object(monitor.console, "print"):
                monitor.run()

        # Verify console.clear was called
        mock_clear.assert_called_once()

    def test_loading_message_content(self):
        """Test loading message content for different configurations."""
        # Test default message
        monitor1 = TimelineMonitor(days=1)
        with patch.object(monitor1.console, "print") as mock_print:
            with patch("ccmonitor.timeline_monitor.load_sessions_in_timerange", return_value=[]):
                with patch.object(monitor1.console, "clear"):
                    monitor1.run()

        loading_call = mock_print.call_args_list[0][0][0]
        assert "1 days" in loading_call
        assert "project" not in loading_call.lower()

        # Test with project filter
        monitor2 = TimelineMonitor(days=5, project="myproject")
        with patch.object(monitor2.console, "print") as mock_print:
            with patch("ccmonitor.timeline_monitor.load_sessions_in_timerange", return_value=[]):
                with patch.object(monitor2.console, "clear"):
                    monitor2.run()

        loading_call = mock_print.call_args_list[0][0][0]
        assert "5 days" in loading_call
        assert "myproject" in loading_call
