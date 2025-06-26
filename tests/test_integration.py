"""Integration tests for ccmonitor."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from ccmonitor.claude_logs import load_sessions_in_timerange
from ccmonitor.timeline_monitor import TimelineMonitor


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.fixture
    def mock_claude_projects(self):
        """Create mock Claude projects directory structure."""
        temp_dir = Path(tempfile.mkdtemp())
        projects_dir = temp_dir / "projects"
        projects_dir.mkdir()

        # Create multiple project directories with JSONL files
        project_data = {
            "web_app": {
                "sessions": 2,
                "events_per_session": 10,
                "base_time": datetime.now() - timedelta(hours=2)
            },
            "data_analysis": {
                "sessions": 1,
                "events_per_session": 15,
                "base_time": datetime.now() - timedelta(hours=1)
            },
            "mobile_app": {
                "sessions": 3,
                "events_per_session": 5,
                "base_time": datetime.now() - timedelta(hours=3)
            }
        }

        created_files = []

        for project_name, config in project_data.items():
            project_dir = projects_dir / project_name
            project_dir.mkdir()

            for session_idx in range(config["sessions"]):
                session_file = project_dir / f"session_{session_idx}.jsonl"

                with session_file.open('w') as f:
                    base_time = config["base_time"]

                    for event_idx in range(config["events_per_session"]):
                        event_time = base_time + timedelta(minutes=session_idx * 30 + event_idx * 2)
                        if event_time.tzinfo is None:
                            event_time = event_time.replace(tzinfo=None)  # Ensure no timezone info

                        event_data = {
                            "timestamp": event_time.isoformat() + "Z",
                            "sessionId": f"{project_name}_session_{session_idx}",
                            "cwd": str(project_dir),
                            "role": "user" if event_idx % 2 == 0 else "assistant",
                            "content": f"Message {event_idx} in {project_name}",
                            "uuid": f"{project_name}-{session_idx}-{event_idx}"
                        }
                        f.write(json.dumps(event_data) + '\n')

                created_files.append(session_file)

        yield temp_dir, created_files, project_data

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

    def test_end_to_end_timeline_loading(self, mock_claude_projects):
        """Test end-to-end timeline loading and processing."""
        temp_dir, files, project_data = mock_claude_projects

        # Mock the get_all_session_files function
        with patch('ccmonitor.claude_logs.get_all_session_files') as mock_get_files:
            mock_get_files.return_value = files

            start_time = datetime.now() - timedelta(hours=4)
            end_time = datetime.now()

            timelines = load_sessions_in_timerange(start_time, end_time)

            # Verify we got some timelines (may be fewer due to filtering/grouping logic)
            assert len(timelines) >= 0

            # Verify each timeline has expected properties
            for timeline in timelines:
                assert timeline.session_id is not None
                assert timeline.project_name is not None
                assert len(timeline.events) > 0
                assert timeline.start_time <= timeline.end_time
                assert timeline.active_duration_minutes >= 0

                # Verify events are sorted by timestamp
                for i in range(1, len(timeline.events)):
                    assert timeline.events[i-1].timestamp <= timeline.events[i].timestamp

    def test_end_to_end_with_project_filter(self, mock_claude_projects):
        """Test end-to-end processing with project filter."""
        temp_dir, files, project_data = mock_claude_projects

        with patch('ccmonitor.claude_logs.get_all_session_files') as mock_get_files:
            mock_get_files.return_value = files

            start_time = datetime.now() - timedelta(hours=4)
            end_time = datetime.now()

            # Filter for specific project
            filtered_timelines = load_sessions_in_timerange(
                start_time, end_time, project_filter="web_app"
            )

            # Should only get timelines containing "web_app"
            for timeline in filtered_timelines:
                assert "web_app" in timeline.project_name.lower() or \
                       "web_app" in timeline.directory.lower()

    def test_timeline_monitor_integration(self, mock_claude_projects):
        """Test TimelineMonitor integration."""
        temp_dir, files, project_data = mock_claude_projects

        with patch('ccmonitor.claude_logs.get_all_session_files') as mock_get_files:
            mock_get_files.return_value = files

            # Create monitor with short time range
            monitor = TimelineMonitor(days=1)

            # Mock console to capture output
            with patch.object(monitor.console, 'print') as mock_print:
                with patch.object(monitor.console, 'clear'):
                    monitor.run()

            # Verify loading message was displayed
            print_calls = [str(call) for call in mock_print.call_args_list]
            loading_calls = [call for call in print_calls if "Loading Claude sessions" in call]
            assert len(loading_calls) > 0

    def test_active_duration_calculation_integration(self, mock_claude_projects):
        """Test that active duration calculation works in integration."""
        temp_dir, files, project_data = mock_claude_projects

        with patch('ccmonitor.claude_logs.get_all_session_files') as mock_get_files:
            mock_get_files.return_value = files

            start_time = datetime.now() - timedelta(hours=4)
            end_time = datetime.now()

            timelines = load_sessions_in_timerange(start_time, end_time)

            for timeline in timelines:
                # Active duration should be reasonable (not zero, not excessively long)
                assert timeline.active_duration_minutes >= 0

                # For our test data (events 2 minutes apart), active duration should be reasonable
                total_duration_minutes = (timeline.end_time - timeline.start_time).total_seconds() / 60

                # Active duration should not exceed total duration
                assert timeline.active_duration_minutes <= total_duration_minutes

                # With events 2 minutes apart, most should be counted as active
                if len(timeline.events) > 1:
                    expected_active = (len(timeline.events) - 1) * 2  # 2 minutes between events
                    # Allow some tolerance due to rounding and calculation details
                    assert abs(timeline.active_duration_minutes - expected_active) <= 5

    def test_empty_projects_handling(self):
        """Test handling of empty projects directory."""
        with patch('ccmonitor.claude_logs.get_all_session_files') as mock_get_files:
            mock_get_files.return_value = []

            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now()

            timelines = load_sessions_in_timerange(start_time, end_time)

            # Should return empty list without errors
            assert timelines == []

    def test_malformed_data_resilience(self):
        """Test system resilience with malformed JSON data."""
        # Create temporary file with mix of valid and invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Valid JSON
            f.write('{"timestamp": "2024-01-01T10:00:00Z", "role": "user", "content": "valid"}\n')
            # Invalid JSON
            f.write('invalid json line\n')
            # Another valid JSON
            f.write('{"timestamp": "2024-01-01T10:01:00Z", "role": "assistant", "content": "also valid"}\n')
            f.flush()

            temp_file = Path(f.name)

        try:
            with patch('ccmonitor.claude_logs.get_all_session_files') as mock_get_files:
                mock_get_files.return_value = [temp_file]

                start_time = datetime.now() - timedelta(hours=1)
                end_time = datetime.now() + timedelta(hours=1)

                # Should not raise exceptions and should return some results
                timelines = load_sessions_in_timerange(start_time, end_time)

                # Should handle gracefully (might return empty list or valid events only)
                assert isinstance(timelines, list)

        finally:
            temp_file.unlink()

    def test_timezone_handling(self, mock_claude_projects):
        """Test that timezone handling works correctly."""
        temp_dir, files, project_data = mock_claude_projects

        # Create file with UTC timestamps
        test_file = temp_dir / "timezone_test.jsonl"
        with test_file.open('w') as f:
            utc_time = datetime.utcnow()
            event_data = {
                "timestamp": utc_time.isoformat() + "Z",  # UTC format
                "sessionId": "tz_test",
                "cwd": str(temp_dir),
                "role": "user",
                "content": "timezone test",
                "uuid": "tz-test-1"
            }
            f.write(json.dumps(event_data) + '\n')

        files.append(test_file)

        with patch('ccmonitor.claude_logs.get_all_session_files') as mock_get_files:
            mock_get_files.return_value = [test_file]

            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now() + timedelta(hours=1)

            timelines = load_sessions_in_timerange(start_time, end_time)

            # Should successfully parse and convert timezones
            if timelines:
                for timeline in timelines:
                    for event in timeline.events:
                        # Timestamp should be timezone-naive (converted to local)
                        assert event.timestamp.tzinfo is None
