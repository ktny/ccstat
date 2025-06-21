"""Tests for display functionality."""

from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import Mock, patch

from ccmonitor.display import display_history, display_processes_table, display_summary
from ccmonitor.process import ProcessInfo


def test_display_processes_table_empty():
    """Test displaying empty process list."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        display_processes_table([])
        output = mock_stdout.getvalue()
        assert "No Claude Code processes found" in output


def test_display_processes_table_with_data():
    """Test displaying process table with data."""
    processes = [
        ProcessInfo(
            pid=1234,
            name="claude",
            cpu_time=10.5,
            memory_mb=256.0,
            start_time=datetime.now(),
            elapsed_time=timedelta(hours=1),
            cmdline=["claude", "--config", ".claude.json"],
        )
    ]

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        display_processes_table(processes)
        output = mock_stdout.getvalue()
        assert "1234" in output
        assert "claude" in output
        assert "Total processes found: 1" in output


def test_display_summary_empty():
    """Test displaying summary with empty process list."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        display_summary([])
        output = mock_stdout.getvalue()
        assert "No Claude Code processes found" in output


def test_display_summary_with_data():
    """Test displaying summary with process data."""
    processes = [
        ProcessInfo(
            pid=1234,
            name="claude",
            cpu_time=10.5,
            memory_mb=256.0,
            start_time=datetime.now(),
            elapsed_time=timedelta(hours=1),
            cmdline=["claude", "--config", ".claude.json"],
        ),
        ProcessInfo(
            pid=5678,
            name="claude-helper",
            cpu_time=5.2,
            memory_mb=128.0,
            start_time=datetime.now(),
            elapsed_time=timedelta(minutes=30),
            cmdline=["claude-helper", "--daemon"],
        ),
    ]

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        display_summary(processes)
        output = mock_stdout.getvalue()
        assert "Running Processes" in output
        assert "2" in output  # Process count
        assert "Total Memory Usage" in output
        assert "Total CPU Time" in output
        assert "Longest Running" in output


def test_display_summary_with_database():
    """Test displaying summary with database statistics."""
    processes = [
        ProcessInfo(
            pid=1234,
            name="claude",
            cpu_time=10.5,
            memory_mb=256.0,
            start_time=datetime.now(),
            elapsed_time=timedelta(hours=1),
            cmdline=["claude", "--config", ".claude.json"],
        )
    ]

    # Mock database
    mock_db = Mock()
    mock_db.get_summary_stats.return_value = {
        "total_records": 10,
        "unique_processes": 5,
        "running_processes": 2,
        "total_memory_mb": 500.0,
        "total_cpu_time": 25.5,
        "oldest_record": datetime(2024, 1, 1),
        "newest_record": datetime(2024, 1, 2)
    }
    mock_db.get_database_size.return_value = 1024 * 1024  # 1MB

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        display_summary(processes, mock_db)
        output = mock_stdout.getvalue()
        assert "Current Claude Code Processes" in output
        assert "Historical Database Statistics" in output
        assert "Total Records" in output
        assert "10" in output


def test_display_history():
    """Test displaying historical process data."""
    # Mock database
    mock_db = Mock()
    mock_db.get_recent_processes.return_value = [
        {
            "pid": 1234,
            "name": "claude",
            "cpu_time": 10.5,
            "memory_mb": 256.0,
            "elapsed_seconds": 3600,  # 1 hour
            "recorded_at": datetime(2024, 1, 1, 12, 0),
            "status": "running"
        },
        {
            "pid": 5678,
            "name": "claude-helper",
            "cpu_time": 5.2,
            "memory_mb": 128.0,
            "elapsed_seconds": 1800,  # 30 minutes
            "recorded_at": datetime(2024, 1, 1, 11, 30),
            "status": "terminated"
        }
    ]
    mock_db.get_summary_stats.return_value = {
        "total_records": 10
    }
    mock_db.get_database_size.return_value = 2048

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        display_history(mock_db)
        output = mock_stdout.getvalue()
        assert "Recent Process History" in output
        assert "1234" in output
        assert "5678" in output
        assert "🟢 Running" in output
        assert "Terminated" in output


def test_display_history_empty():
    """Test displaying history with no data."""
    mock_db = Mock()
    mock_db.get_recent_processes.return_value = []

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        display_history(mock_db)
        output = mock_stdout.getvalue()
        assert "No historical process data found" in output
