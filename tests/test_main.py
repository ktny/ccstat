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


@patch("ccmonitor.__main__.RealTimeMonitor")
def test_main_no_save(mock_monitor_class) -> None:
    """Test main command with --no-save flag."""
    mock_monitor = Mock()
    mock_monitor_class.return_value = mock_monitor

    runner = CliRunner()
    result = runner.invoke(main, ["--no-save"])
    assert result.exit_code == 0
    # Should create monitor with no database
    mock_monitor_class.assert_called_once_with(db=None, update_interval=1.0)
    mock_monitor.run.assert_called_once()


def test_main_help() -> None:
    """Test main command help."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Claude Code Monitor" in result.output


@patch("ccmonitor.__main__.ProcessDatabase")
@patch("ccmonitor.__main__.find_claude_processes")
def test_main_exception_handling(mock_find_processes, mock_db_class) -> None:
    """Test error handling in main function."""
    mock_find_processes.side_effect = Exception("Test error")
    mock_db_class.return_value = Mock()

    runner = CliRunner()
    result = runner.invoke(main, ["--once"])
    assert result.exit_code == 0
    assert "❌ Error: Test error" in result.output


@patch("ccmonitor.__main__.ProcessDatabase")
@patch("ccmonitor.__main__.find_claude_processes")
def test_main_once_flag(mock_find_processes, mock_db_class) -> None:
    """Test main command with --once flag."""
    mock_find_processes.return_value = []
    mock_db = Mock()
    mock_db_class.return_value = mock_db

    runner = CliRunner()
    result = runner.invoke(main, ["--once"])
    assert result.exit_code == 0
    assert "No Claude Code processes found" in result.output
    # save_processes is not called when no processes are found
    mock_db.save_processes.assert_not_called()


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


@patch("ccmonitor.__main__.RealTimeMonitor")
def test_main_realtime_no_save(mock_monitor_class) -> None:
    """Test main command with --no-save in real-time mode."""
    mock_monitor = Mock()
    mock_monitor_class.return_value = mock_monitor

    runner = CliRunner()
    runner.invoke(main, ["--no-save"])

    # Should create monitor with no database
    mock_monitor_class.assert_called_once_with(db=None, update_interval=1.0)


def test_main_history_with_no_save() -> None:
    """Test that --history and --no-save together raises an error."""
    runner = CliRunner()
    result = runner.invoke(main, ["--history", "--no-save"])

    assert result.exit_code == 0
    assert "--historyオプションは--no-saveと一緒に使用できません" in result.output
