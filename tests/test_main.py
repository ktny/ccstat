"""Tests for main entry point."""

from click.testing import CliRunner

from ccmonitor.__main__ import main


def test_main_default() -> None:
    """Test main command without options."""
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "📊 Real-time monitoring: Claude Code process monitor" in result.output
    assert "This is a dummy output for real-time monitoring mode." in result.output
    assert "Press Ctrl+C to exit." in result.output


def test_main_summary() -> None:
    """Test main command with summary flag."""
    runner = CliRunner()
    result = runner.invoke(main, ["--summary"])
    assert result.exit_code == 0
    assert "🔍 Summary mode: Claude Code process monitoring summary" in result.output
    assert "This is a dummy output for summary mode." in result.output


def test_main_help() -> None:
    """Test main command help."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Claude Code Monitor" in result.output
