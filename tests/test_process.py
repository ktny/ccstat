"""Tests for process detection functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ccmonitor.claude_config import ConversationInfo
from ccmonitor.process import ProcessInfo, find_claude_processes


@patch("ccmonitor.process.get_last_conversation_for_directory")
@patch("ccmonitor.process.psutil.process_iter")
def test_find_claude_processes(mock_process_iter, mock_get_conversation):
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

    # Mock cwd
    mock_proc.cwd.return_value = "/home/user/project"

    # Mock conversation info
    mock_conversation = ConversationInfo(
        conversation_id="conv123",
        last_activity=datetime.now(),
        name="Test conversation",
    )
    mock_get_conversation.return_value = mock_conversation

    mock_process_iter.return_value = [mock_proc]

    processes = find_claude_processes()

    assert len(processes) == 1
    assert processes[0].pid == 1234
    assert processes[0].name == "claude"
    assert processes[0].cpu_time == 6.0  # user + system
    assert isinstance(processes[0].elapsed_time, timedelta)
    assert processes[0].cwd == "/home/user/project"
    assert processes[0].last_conversation == mock_conversation


@patch("ccmonitor.process.get_last_conversation_for_directory")
@patch("ccmonitor.process.psutil.process_iter")
def test_find_claude_processes_no_cwd_access(mock_process_iter, mock_get_conversation):
    """Test finding Claude processes when cwd access is denied."""
    # Mock process data
    mock_proc = Mock()
    mock_proc.info = {
        "pid": 1234,
        "name": "claude",
        "cmdline": ["claude"],
        "create_time": datetime.now().timestamp() - 60,
    }

    # Mock CPU info
    mock_cpu_times = Mock()
    mock_cpu_times.user = 1.0
    mock_cpu_times.system = 0.5
    mock_proc.cpu_times.return_value = mock_cpu_times

    # Mock cwd access denied
    from psutil import AccessDenied

    mock_proc.cwd.side_effect = AccessDenied("Access denied")

    mock_get_conversation.return_value = None
    mock_process_iter.return_value = [mock_proc]

    processes = find_claude_processes()

    assert len(processes) == 1
    assert processes[0].cwd == "unknown"
    assert processes[0].last_conversation is None


def test_process_info_dataclass():
    """Test ProcessInfo dataclass."""
    now = datetime.now()
    elapsed = timedelta(hours=1)

    conv = ConversationInfo(
        conversation_id="conv123",
        last_activity=now,
        name="Test conversation",
    )

    process_info = ProcessInfo(
        pid=1234,
        name="claude",
        cpu_time=10.5,
        start_time=now,
        elapsed_time=elapsed,
        cmdline=["claude", "--verbose"],
        cpu_usage_percent=2.92,
        cwd="/home/user/project",
        last_conversation=conv,
    )

    assert process_info.pid == 1234
    assert process_info.name == "claude"
    assert process_info.cpu_time == 10.5
    assert process_info.start_time == now
    assert process_info.elapsed_time == elapsed
    assert process_info.cmdline == ["claude", "--verbose"]
    assert process_info.cpu_usage_percent == 2.92
    assert process_info.cwd == "/home/user/project"
    assert process_info.last_conversation == conv


def test_process_info_dataclass_without_conversation():
    """Test ProcessInfo dataclass with no conversation."""
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
        cwd="/home/user/project",
    )

    assert process_info.last_conversation is None
