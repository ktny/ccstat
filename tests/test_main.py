"""Tests for main entry point."""

from unittest.mock import patch

from click.testing import CliRunner

from ccmonitor.__main__ import main


@patch("ccmonitor.__main__.find_claude_processes")
def test_main_default_no_processes(mock_find_processes) -> None:
    """Test main command without options when no processes found."""
    mock_find_processes.return_value = []

    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "No Claude Code processes found" in result.output


@patch("ccmonitor.__main__.find_claude_processes")
def test_main_summary_no_processes(mock_find_processes) -> None:
    """Test main command with summary flag when no processes found."""
    mock_find_processes.return_value = []

    runner = CliRunner()
    result = runner.invoke(main, ["--summary"])
    assert result.exit_code == 0
    assert "No Claude Code processes found" in result.output


def test_main_help() -> None:
    """Test main command help."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Claude Code Monitor" in result.output


@patch("ccmonitor.__main__.find_claude_processes")
def test_main_exception_handling(mock_find_processes) -> None:
    """Test error handling in main function."""
    mock_find_processes.side_effect = Exception("Test error")

    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "❌ Error: Test error" in result.output
