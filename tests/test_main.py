"""Tests for main entry point."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from ccmonitor.__main__ import main


@patch("ccmonitor.__main__.ProcessDatabase")
@patch("ccmonitor.__main__.RealTimeMonitor")
def test_main_default_no_processes(mock_monitor_class, mock_db_class) -> None:
    """Test main command without options (real-time mode)."""
    mock_db = Mock()
    mock_db_class.return_value = mock_db
    mock_monitor = Mock()
    mock_monitor_class.return_value = mock_monitor

    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    # Should create and run the monitor
    mock_monitor_class.assert_called_once_with(db=mock_db, update_interval=1.0)
    mock_monitor.run.assert_called_once()


@patch("ccmonitor.__main__.ProcessDatabase")
@patch("ccmonitor.__main__.find_claude_processes")
def test_main_summary_no_processes(mock_find_processes, mock_db_class) -> None:
    """Test main command with summary flag when no processes found."""
    mock_find_processes.return_value = []
    mock_db = Mock()
    mock_db_class.return_value = mock_db

    runner = CliRunner()
    result = runner.invoke(main, ["--summary"])
    assert result.exit_code == 0
    assert "No Claude Code processes found" in result.output


@patch("ccmonitor.__main__.ProcessDatabase")
def test_main_history(mock_db_class) -> None:
    """Test main command with history flag."""
    mock_db = Mock()
    mock_db_class.return_value = mock_db

    runner = CliRunner()
    result = runner.invoke(main, ["--history"])
    assert result.exit_code == 0
    # Should not call find_claude_processes for history mode




def test_main_help() -> None:
    """Test main command help."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Claude Code Monitor" in result.output






@patch("ccmonitor.__main__.ProcessDatabase")
@patch("ccmonitor.__main__.RealTimeMonitor")
def test_main_realtime_mode(mock_monitor_class, mock_db_class) -> None:
    """Test main command in real-time mode (default)."""
    mock_db = Mock()
    mock_db_class.return_value = mock_db
    mock_monitor = Mock()
    mock_monitor_class.return_value = mock_monitor

    runner = CliRunner()
    runner.invoke(main)

    # Should create and run the monitor
    mock_monitor_class.assert_called_once_with(db=mock_db, update_interval=1.0)
    mock_monitor.run.assert_called_once()


@patch("ccmonitor.__main__.ProcessDatabase")
@patch("ccmonitor.__main__.RealTimeMonitor")
def test_main_realtime_with_interval(mock_monitor_class, mock_db_class) -> None:
    """Test main command with custom interval."""
    mock_db = Mock()
    mock_db_class.return_value = mock_db
    mock_monitor = Mock()
    mock_monitor_class.return_value = mock_monitor

    runner = CliRunner()
    runner.invoke(main, ["--interval", "2.5"])

    # Should create monitor with custom interval
    mock_monitor_class.assert_called_once_with(db=mock_db, update_interval=2.5)




