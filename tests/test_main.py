"""Tests for main entry point."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from ccmonitor.__main__ import main


@patch("ccmonitor.__main__.ProcessDatabase")
@patch("ccmonitor.__main__.RealTimeMonitor")
def test_main_default(mock_monitor_class, mock_db_class) -> None:
    """Test main command (real-time mode)."""
    mock_db = Mock()
    mock_db_class.return_value = mock_db
    mock_monitor = Mock()
    mock_monitor_class.return_value = mock_monitor

    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    # Should create and run the monitor
    mock_monitor_class.assert_called_once_with(db=mock_db)
    mock_monitor.run.assert_called_once()


def test_main_help() -> None:
    """Test main command help."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Claude Code Monitor" in result.output
