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
    calculate_token_totals,
    create_unique_hash,
    deduplicate_events,
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
        assert event.input_tokens == 0  # Default value
        assert event.output_tokens == 0  # Default value

    def test_session_event_with_tokens(self):
        """Test creating a SessionEvent object with token information."""
        timestamp = datetime.now()
        event = SessionEvent(
            timestamp=timestamp,
            session_id="test_session",
            directory="/test/dir",
            message_type="assistant",
            content_preview="AI response",
            uuid="test-uuid-456",
            input_tokens=100,
            output_tokens=50,
        )

        assert event.input_tokens == 100
        assert event.output_tokens == 50


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
        assert timeline.total_input_tokens == 0  # Default value
        assert timeline.total_output_tokens == 0  # Default value

    def test_session_timeline_with_tokens(self):
        """Test creating a SessionTimeline object with token information."""
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
            total_input_tokens=1000,
            total_output_tokens=500,
        )

        assert timeline.total_input_tokens == 1000
        assert timeline.total_output_tokens == 500


class TestCalculateTokenTotals:
    """Test token totals calculation."""

    def test_calculate_token_totals_empty_events(self):
        """Test token calculation with empty events list."""
        input_total, output_total = calculate_token_totals([])
        assert input_total == 0
        assert output_total == 0

    def test_calculate_token_totals_with_events(self):
        """Test token calculation with multiple events (following ccusage methodology - only messages with usage)."""
        base_time = datetime.now()
        events = [
            # User messages without usage fields would be filtered out, so only include assistant messages
            SessionEvent(
                timestamp=base_time + timedelta(minutes=1),
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="assistant response",
                uuid="uuid-2",
                input_tokens=100,
                output_tokens=50,
                cache_creation_input_tokens=25,
                cache_read_input_tokens=15,
            ),
            SessionEvent(
                timestamp=base_time + timedelta(minutes=2),
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="another response",
                uuid="uuid-3",
                input_tokens=200,
                output_tokens=150,
                cache_creation_input_tokens=10,
                cache_read_input_tokens=5,
            ),
        ]

        input_total, output_total = calculate_token_totals(events)
        # Following ccusage: input tokens and cache tokens are displayed separately
        # Only count regular input tokens: 100 + 200 = 300
        assert input_total == 300
        assert output_total == 200  # 50 + 150


class TestDeduplication:
    """Test deduplication functionality following ccusage methodology."""

    def test_create_unique_hash(self):
        """Test unique hash creation."""
        # Valid IDs
        hash1 = create_unique_hash("msg_123", "req_456")
        assert hash1 == "msg_123:req_456"

        # Empty IDs should return None
        assert create_unique_hash("", "req_456") is None
        assert create_unique_hash("msg_123", "") is None
        assert create_unique_hash("", "") is None

    def test_deduplicate_events_no_duplicates(self):
        """Test deduplication with no duplicate events."""
        base_time = datetime.now()
        events = [
            SessionEvent(
                timestamp=base_time,
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="message 1",
                uuid="uuid-1",
                message_id="msg_1",
                request_id="req_1",
            ),
            SessionEvent(
                timestamp=base_time + timedelta(minutes=1),
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="message 2",
                uuid="uuid-2",
                message_id="msg_2",
                request_id="req_2",
            ),
        ]

        deduplicated = deduplicate_events(events)
        assert len(deduplicated) == 2
        assert deduplicated == events

    def test_deduplicate_events_with_duplicates(self):
        """Test deduplication with duplicate events."""
        base_time = datetime.now()
        events = [
            SessionEvent(
                timestamp=base_time,
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="message 1",
                uuid="uuid-1",
                message_id="msg_1",
                request_id="req_1",
            ),
            SessionEvent(
                timestamp=base_time + timedelta(minutes=1),
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="duplicate message",
                uuid="uuid-2",
                message_id="msg_1",  # Same message_id
                request_id="req_1",  # Same request_id
            ),
            SessionEvent(
                timestamp=base_time + timedelta(minutes=2),
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="message 3",
                uuid="uuid-3",
                message_id="msg_3",
                request_id="req_3",
            ),
        ]

        deduplicated = deduplicate_events(events)
        assert len(deduplicated) == 2  # One duplicate removed
        assert deduplicated[0].message_id == "msg_1"
        assert deduplicated[1].message_id == "msg_3"

    def test_deduplicate_events_missing_ids(self):
        """Test deduplication with missing message or request IDs."""
        base_time = datetime.now()
        events = [
            SessionEvent(
                timestamp=base_time,
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="message 1",
                uuid="uuid-1",
                message_id="msg_1",
                request_id="req_1",
            ),
            SessionEvent(
                timestamp=base_time + timedelta(minutes=1),
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="message with missing request_id",
                uuid="uuid-2",
                message_id="msg_2",
                request_id="",  # Missing request_id
            ),
            SessionEvent(
                timestamp=base_time + timedelta(minutes=2),
                session_id="test",
                directory="/test",
                message_type="assistant",
                content_preview="message with missing message_id",
                uuid="uuid-3",
                message_id="",  # Missing message_id
                request_id="req_3",
            ),
        ]

        deduplicated = deduplicate_events(events)
        # Only the first event should be kept (others have missing IDs)
        assert len(deduplicated) == 1
        assert deduplicated[0].message_id == "msg_1"


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
        """Test parsing a valid JSONL file with strict validation (only messages with usage fields)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Write test JSONL data - only messages with usage fields will be included
            test_data = [
                {
                    "timestamp": "2024-01-01T10:00:00Z",
                    "sessionId": "session1",
                    "cwd": "/test/project",
                    "message": {"role": "user", "content": "Hello Claude"},  # No usage field - will be skipped
                    "uuid": "uuid-1",
                },
                {
                    "timestamp": "2024-01-01T10:01:00Z",
                    "sessionId": "session1",
                    "cwd": "/test/project",
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "text", "text": "Hello! How can I help you?"}],
                        "usage": {
                            "input_tokens": 10,
                            "output_tokens": 20,
                        },
                    },
                    "uuid": "uuid-2",
                },
            ]

            for data in test_data:
                f.write(json.dumps(data) + "\n")
            f.flush()

            try:
                events = parse_jsonl_file(Path(f.name))

                # Only 1 event should be parsed (user message skipped due to no usage field)
                assert len(events) == 1

                # Check the assistant event (only one included)
                assert events[0].session_id == "session1"
                assert events[0].directory == "/test/project"
                assert events[0].message_type == "assistant"
                assert "Hello! How can I help you?" in events[0].content_preview
                assert events[0].input_tokens == 10
                assert events[0].output_tokens == 20

            finally:
                Path(f.name).unlink()

    def test_parse_jsonl_with_tokens(self):
        """Test parsing JSONL file with token usage information (strict validation)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Write test JSONL data with usage information
            test_data = [
                {
                    "timestamp": "2024-01-01T10:00:00Z",
                    "sessionId": "session1",
                    "cwd": "/test/project",
                    "message": {"role": "user", "content": "Hello Claude"},  # No usage field - will be skipped
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
                        "usage": {
                            "input_tokens": 50,
                            "cache_creation_input_tokens": 100,  # Tracked separately, not counted in input
                            "cache_read_input_tokens": 25,       # Tracked separately, not counted in input
                            "output_tokens": 30,
                        },
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

                # Only 1 event should be parsed (user message skipped due to no usage field)
                assert len(events) == 1

                # Check the assistant event (only one included)
                assert events[0].message_type == "assistant"
                assert events[0].input_tokens == 50  # Regular input tokens
                assert events[0].output_tokens == 30
                assert events[0].cache_creation_input_tokens == 100  # Cache tokens now extracted
                assert events[0].cache_read_input_tokens == 25       # Cache tokens now extracted
                assert events[0].message_id == "msg_01ABC123"
                assert events[0].request_id == "req_01DEF456"

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
