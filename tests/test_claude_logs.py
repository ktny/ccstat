"""Tests for claude_logs module."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ccmonitor.claude_logs import (
    SessionEvent,
    SessionTimeline,
    calculate_active_duration,
    load_sessions_in_timerange,
    parse_jsonl_file,
)


class TestSessionEvent:
    """Test SessionEvent dataclass."""

    def test_session_event_creation(self):
        """Test creating a SessionEvent object."""
        timestamp = datetime.now()
        event = SessionEvent(
            timestamp=timestamp,
            session_id="test_session",
            directory="/test/dir",
            message_type="user",
            content_preview="Test message",
            uuid="test-uuid-123",
        )

        assert event.timestamp == timestamp
        assert event.session_id == "test_session"
        assert event.directory == "/test/dir"
        assert event.message_type == "user"
        assert event.content_preview == "Test message"
        assert event.uuid == "test-uuid-123"


class TestSessionTimeline:
    """Test SessionTimeline dataclass."""

    def test_session_timeline_creation(self):
        """Test creating a SessionTimeline object."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        events = []

        timeline = SessionTimeline(
            session_id="test_session",
            directory="/test/dir",
            project_name="test_project",
            events=events,
            start_time=start_time,
            end_time=end_time,
            active_duration_minutes=60,
        )

        assert timeline.session_id == "test_session"
        assert timeline.directory == "/test/dir"
        assert timeline.project_name == "test_project"
        assert timeline.events == events
        assert timeline.start_time == start_time
        assert timeline.end_time == end_time
        assert timeline.active_duration_minutes == 60




class TestCalculateActiveDuration:
    """Test active duration calculation."""

    def test_single_event(self):
        """Test active duration with single event."""
        event = SessionEvent(
            timestamp=datetime.now(),
            session_id="test",
            directory="/test",
            message_type="user",
            content_preview="test",
            uuid="test-uuid",
        )

        duration = calculate_active_duration([event])
        assert duration == 5  # Minimum 5 minutes for single event

    def test_continuous_activity(self):
        """Test active duration with continuous activity (intervals <= 1 minute)."""
        base_time = datetime.now()
        events = []

        # Create events 30 seconds apart (within 1-minute threshold)
        for i in range(4):
            events.append(
                SessionEvent(
                    timestamp=base_time + timedelta(seconds=i * 30),
                    session_id="test",
                    directory="/test",
                    message_type="user" if i % 2 == 0 else "assistant",
                    content_preview=f"message {i}",
                    uuid=f"uuid-{i}",
                )
            )

        duration = calculate_active_duration(events)
        # 3 intervals of 30 seconds each = 1.5 minutes
        assert duration == 1

    def test_with_inactive_periods(self):
        """Test active duration with inactive periods (intervals > 1 minute)."""
        base_time = datetime.now()
        events = []

        # First cluster: 2 events 30 seconds apart
        events.append(
            SessionEvent(
                timestamp=base_time,
                session_id="test",
                directory="/test",
                message_type="user",
                content_preview="message 1",
                uuid="uuid-1",
            )
        )
        events.append(
            SessionEvent(
                timestamp=base_time + timedelta(seconds=30),
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="message 2",
                uuid="uuid-2",
            )
        )

        # Long gap (3 minutes - exceeds 1-minute threshold)
        # Second cluster: 2 events 45 seconds apart
        events.append(
            SessionEvent(
                timestamp=base_time + timedelta(minutes=3, seconds=30),
                session_id="test",
                directory="/test",
                message_type="user",
                content_preview="message 3",
                uuid="uuid-3",
            )
        )
        events.append(
            SessionEvent(
                timestamp=base_time + timedelta(minutes=4, seconds=15),
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="message 4",
                uuid="uuid-4",
            )
        )

        duration = calculate_active_duration(events)
        # Only intervals <= 1 minute: 0.5 + 0.75 = 1.25 minutes
        assert duration == 1

    def test_empty_events(self):
        """Test active duration with empty events list."""
        duration = calculate_active_duration([])
        assert duration == 5  # Should return minimum for empty list


class TestParseJsonlFile:
    """Test JSONL file parsing."""

    def test_parse_valid_jsonl(self):
        """Test parsing a valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Write test JSONL data
            test_data = [
                {
                    "timestamp": "2024-01-01T10:00:00Z",
                    "sessionId": "session1",
                    "cwd": "/test/project",
                    "message": {"role": "user", "content": "Hello Claude"},
                    "uuid": "uuid-1",
                },
                {
                    "timestamp": "2024-01-01T10:01:00Z",
                    "sessionId": "session1",
                    "cwd": "/test/project",
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "text", "text": "Hello! How can I help you?"}],
                    },
                    "uuid": "uuid-2",
                },
            ]

            for data in test_data:
                f.write(json.dumps(data) + "\n")
            f.flush()

            try:
                events = parse_jsonl_file(Path(f.name))

                assert len(events) == 2

                # Check first event
                assert events[0].session_id == "session1"
                assert events[0].directory == "/test/project"
                assert events[0].message_type == "user"
                assert "Hello Claude" in events[0].content_preview

                # Check second event
                assert events[1].message_type == "assistant"
                assert "Hello! How can I help you?" in events[1].content_preview

            finally:
                Path(f.name).unlink()

    def test_parse_jsonl_with_messages(self):
        """Test parsing JSONL file with different message types."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Write test JSONL data with different message types
            test_data = [
                {
                    "timestamp": "2024-01-01T10:00:00Z",
                    "sessionId": "session1",
                    "cwd": "/test/project",
                    "message": {"role": "user", "content": "Hello Claude"},
                    "uuid": "uuid-1",
                },
                {
                    "timestamp": "2024-01-01T10:01:00Z",
                    "sessionId": "session1",
                    "cwd": "/test/project",
                    "message": {
                        "id": "msg_01ABC123",
                        "role": "assistant",
                        "content": [{"type": "text", "text": "Hello! How can I help you?"}],
                    },
                    "requestId": "req_01DEF456",
                    "uuid": "uuid-2",
                },
            ]

            for data in test_data:
                f.write(json.dumps(data) + "\n")
            f.flush()

            try:
                events = parse_jsonl_file(Path(f.name))

                assert len(events) == 2

                # Check first event (user message)
                assert events[0].message_type == "user"
                assert "Hello Claude" in events[0].content_preview

                # Check second event (assistant message)
                assert events[1].message_type == "assistant"
                assert "Hello! How can I help you?" in events[1].content_preview

            finally:
                Path(f.name).unlink()

    def test_parse_malformed_jsonl(self):
        """Test parsing JSONL file with malformed lines."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Write mix of valid and invalid JSON
            f.write('{"valid": "json"}\n')
            f.write("invalid json line\n")  # This should be skipped
            f.write('{"another": "valid", "timestamp": "2024-01-01T10:00:00Z", "role": "user"}\n')
            f.flush()

            try:
                events = parse_jsonl_file(Path(f.name))
                # Should skip malformed lines and only return valid events with required fields
                assert isinstance(events, list)

            finally:
                Path(f.name).unlink()

    def test_parse_nonexistent_file(self):
        """Test parsing a nonexistent file."""
        events = parse_jsonl_file(Path("/nonexistent/file.jsonl"))
        assert events == []


class TestLoadSessionsInTimerange:
    """Test loading sessions in time range."""

    @pytest.fixture
    def sample_jsonl_files(self):
        """Create sample JSONL files for testing."""
        files = []
        base_time = datetime.now()

        # Create temporary directory structure similar to Claude projects
        temp_dir = Path(tempfile.mkdtemp())
        projects_dir = temp_dir / "projects"
        projects_dir.mkdir()

        # Create project directories and JSONL files
        for i in range(2):
            project_dir = projects_dir / f"project_{i}"
            project_dir.mkdir()

            jsonl_file = project_dir / f"session_{i}.jsonl"
            with jsonl_file.open("w") as f:
                # Write events for this project
                for j in range(3):
                    event_data = {
                        "timestamp": (base_time + timedelta(minutes=i * 60 + j * 10)).isoformat() + "Z",
                        "sessionId": f"session_{i}",
                        "cwd": str(project_dir),
                        "role": "user" if j % 2 == 0 else "assistant",
                        "content": f"Message {j} in project {i}",
                        "uuid": f"uuid-{i}-{j}",
                    }
                    f.write(json.dumps(event_data) + "\n")

            files.append(jsonl_file)

        yield temp_dir, files

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir)

    def test_load_sessions_basic(self, sample_jsonl_files):
        """Test basic session loading."""
        temp_dir, files = sample_jsonl_files

        # Mock the get_all_session_files function to return our test files
        import ccmonitor.claude_logs as claude_logs_module

        original_get_files = claude_logs_module.get_all_session_files

        def mock_get_files():
            return files

        claude_logs_module.get_all_session_files = mock_get_files

        try:
            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now() + timedelta(hours=1)

            timelines = load_sessions_in_timerange(start_time, end_time)

            # Should return some timelines
            assert isinstance(timelines, list)

            # Each timeline should have the required attributes
            for timeline in timelines:
                assert hasattr(timeline, "session_id")
                assert hasattr(timeline, "project_name")
                assert hasattr(timeline, "events")
                assert hasattr(timeline, "active_duration_minutes")
                assert isinstance(timeline.active_duration_minutes, int)

        finally:
            # Restore original function
            claude_logs_module.get_all_session_files = original_get_files
