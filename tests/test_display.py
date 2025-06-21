"""Tests for display functionality."""

from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch

from ccmonitor.display import display_processes_table, display_summary
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
        assert "Total Processes" in output
        assert "2" in output  # Process count
        assert "Total Memory Usage" in output
        assert "Total CPU Time" in output
        assert "Longest Running" in output
