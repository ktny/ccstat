"""Tests for process detection functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ccmonitor.process import (
    ProcessInfo,
    find_claude_processes,
    format_cpu_time,
    format_elapsed_time,
    is_claude_process,
)


def test_is_claude_process():
    """Test Claude process detection logic."""
    # Test positive cases (only name matters now)
    assert is_claude_process("claude", ["claude", "--some-arg"])
    assert is_claude_process("claude-code", ["./claude-code"])
    assert is_claude_process("Claude", [])  # Case insensitive
    assert is_claude_process("some-claude-app", [])

    # Test negative cases
    assert not is_claude_process("python", ["python", "/path/to/.claude/script.py"])
    assert not is_claude_process("node", ["node", "claude.ai/app.js"])
    assert not is_claude_process("anthropic-cli", ["anthropic-cli", "run"])
    assert not is_claude_process("", [])
    assert not is_claude_process("vim", ["vim", "file.txt"])


def test_format_elapsed_time():
    """Test elapsed time formatting."""
    assert format_elapsed_time(timedelta(seconds=30)) == "30s"
    assert format_elapsed_time(timedelta(seconds=90)) == "1m 30s"
    assert format_elapsed_time(timedelta(minutes=5)) == "5m"
    assert format_elapsed_time(timedelta(hours=2, minutes=30)) == "2h 30m"
    assert format_elapsed_time(timedelta(hours=1)) == "1h"
    assert format_elapsed_time(timedelta(days=1, hours=3)) == "1d 3h"
    assert format_elapsed_time(timedelta(days=2)) == "2d"


def test_format_cpu_time():
    """Test CPU time formatting."""
    assert format_cpu_time(0.5) == "0.50s"
    assert format_cpu_time(1.5) == "1.5s"
    assert format_cpu_time(45.0) == "45.0s"
    assert format_cpu_time(90.5) == "1m 30.5s"
    assert format_cpu_time(3661.0) == "1h 1m"


@patch("ccmonitor.process.psutil.process_iter")
def test_find_claude_processes(mock_process_iter):
    """Test finding Claude processes."""
    # Mock process data
    mock_proc = Mock()
    mock_proc.info = {
        "pid": 1234,
        "name": "claude",
        "cmdline": ["claude", "--config", ".claude.json"],
        "create_time": datetime.now().timestamp() - 3600,  # 1 hour ago
    }

    # Mock CPU info
    mock_cpu_times = Mock()
    mock_cpu_times.user = 5.0
    mock_cpu_times.system = 1.0
    mock_proc.cpu_times.return_value = mock_cpu_times

    mock_process_iter.return_value = [mock_proc]

    processes = find_claude_processes()

    assert len(processes) == 1
    assert processes[0].pid == 1234
    assert processes[0].name == "claude"
    assert processes[0].cpu_time == 6.0  # user + system
    assert isinstance(processes[0].elapsed_time, timedelta)


def test_process_info_dataclass():
    """Test ProcessInfo dataclass."""
    now = datetime.now()
    elapsed = timedelta(hours=1)

    process_info = ProcessInfo(
        pid=1234,
        name="claude",
        cpu_time=10.5,
        start_time=now,
        elapsed_time=elapsed,
        cmdline=["claude", "--verbose"],
        cpu_usage_percent=2.92,
    )

    assert process_info.pid == 1234
    assert process_info.name == "claude"
    assert process_info.cpu_time == 10.5
    assert process_info.start_time == now
    assert process_info.elapsed_time == elapsed
    assert process_info.cmdline == ["claude", "--verbose"]
    assert process_info.cpu_usage_percent == 2.92
