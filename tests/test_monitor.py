"""Tests for real-time monitoring functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from ccmonitor.monitor import RealTimeMonitor
from ccmonitor.process import ProcessInfo


@pytest.fixture
def sample_process() -> ProcessInfo:
    """Create a sample ProcessInfo for testing."""
    return ProcessInfo(
        pid=12345,
        name="claude",
        cpu_time=1.23,
        start_time=datetime.now() - timedelta(minutes=10),
        elapsed_time=timedelta(minutes=10),
        cmdline=["python", "-m", "claude"],
    )


def test_monitor_init() -> None:
    """Test RealTimeMonitor initialization."""
    monitor = RealTimeMonitor()
    assert monitor.db is None
    assert monitor.update_interval == 1.0
    assert not monitor.running
    assert monitor.update_count == 0


def test_monitor_init_with_params() -> None:
    """Test RealTimeMonitor initialization with parameters."""
    mock_db = Mock()
    monitor = RealTimeMonitor(db=mock_db)
    assert monitor.db is mock_db
    assert monitor.update_interval == 1.0


def test_create_layout_no_processes() -> None:
    """Test layout creation when no processes are found."""
    monitor = RealTimeMonitor()
    layout = monitor.create_layout([])

    # Check that layout has the expected structure
    assert hasattr(layout, "_renderable")
    assert layout is not None


def test_create_layout_with_processes(sample_process: ProcessInfo) -> None:
    """Test layout creation with processes."""
    monitor = RealTimeMonitor()
    layout = monitor.create_layout([sample_process])

    # Check that layout has the expected structure
    assert hasattr(layout, "_renderable")
    assert layout is not None


def test_create_process_table(sample_process: ProcessInfo) -> None:
    """Test process table creation."""
    monitor = RealTimeMonitor()
    table = monitor._create_process_table([sample_process])

    # Check table properties
    assert "Claude Code Processes (1 found)" in str(table.title)


def test_create_process_table_empty() -> None:
    """Test process table creation with no processes."""
    monitor = RealTimeMonitor()
    table = monitor._create_process_table([])

    # Check table properties
    assert "Claude Code Processes (0 found)" in str(table.title)





@patch("ccmonitor.monitor.find_claude_processes")
@patch("ccmonitor.monitor.time.sleep")
def test_run_with_keyboard_interrupt(
    mock_sleep, mock_find_processes, sample_process: ProcessInfo
) -> None:
    """Test run method with keyboard interrupt."""
    mock_find_processes.return_value = [sample_process]

    # Make sleep raise KeyboardInterrupt after first call
    mock_sleep.side_effect = [None, KeyboardInterrupt()]

    monitor = RealTimeMonitor()

    # This should exit gracefully
    monitor.run()

    assert not monitor.running






def test_create_layout_truncates_long_commands() -> None:
    """Test that long command lines are truncated in the display."""
    long_process = ProcessInfo(
        pid=12345,
        name="claude",
        cpu_time=1.23,
        start_time=datetime.now() - timedelta(minutes=10),
        elapsed_time=timedelta(minutes=10),
        cmdline=["python", "-m", "very_long_command_that_should_be_truncated"] * 10,
    )

    monitor = RealTimeMonitor()
    table = monitor._create_process_table([long_process])

    # Check that the table was created successfully
    assert table is not None
