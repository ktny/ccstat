"""Tests for main entry point."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ccmonitor.__main__ import main


class TestMain:
    """Test main entry point and CLI."""

    def test_main_default_parameters(self):
        """Test main with default parameters."""
        runner = CliRunner()
        
        with patch('ccmonitor.__main__.TimelineMonitor') as mock_monitor_class:
            mock_monitor = mock_monitor_class.return_value
            
            result = runner.invoke(main, [])
            
            assert result.exit_code == 0
            mock_monitor_class.assert_called_once_with(days=1, project=None, threads=False)
            mock_monitor.run.assert_called_once()

    def test_main_with_days_parameter(self):
        """Test main with custom days parameter."""
        runner = CliRunner()
        
        with patch('ccmonitor.__main__.TimelineMonitor') as mock_monitor_class:
            mock_monitor = mock_monitor_class.return_value
            
            result = runner.invoke(main, ['--days', '7'])
            
            assert result.exit_code == 0
            mock_monitor_class.assert_called_once_with(days=7, project=None, threads=False)
            mock_monitor.run.assert_called_once()

    def test_main_with_project_parameter(self):
        """Test main with project filter."""
        runner = CliRunner()
        
        with patch('ccmonitor.__main__.TimelineMonitor') as mock_monitor_class:
            mock_monitor = mock_monitor_class.return_value
            
            result = runner.invoke(main, ['--project', 'myproject'])
            
            assert result.exit_code == 0
            mock_monitor_class.assert_called_once_with(days=1, project='myproject', threads=False)
            mock_monitor.run.assert_called_once()

    def test_main_with_threads_parameter(self):
        """Test main with threads mode enabled."""
        runner = CliRunner()
        
        with patch('ccmonitor.__main__.TimelineMonitor') as mock_monitor_class:
            mock_monitor = mock_monitor_class.return_value
            
            result = runner.invoke(main, ['--threads'])
            
            assert result.exit_code == 0
            mock_monitor_class.assert_called_once_with(days=1, project=None, threads=True)
            mock_monitor.run.assert_called_once()

    def test_main_with_all_parameters(self):
        """Test main with all parameters."""
        runner = CliRunner()
        
        with patch('ccmonitor.__main__.TimelineMonitor') as mock_monitor_class:
            mock_monitor = mock_monitor_class.return_value
            
            result = runner.invoke(main, ['--days', '14', '--project', 'testproj', '--threads'])
            
            assert result.exit_code == 0
            mock_monitor_class.assert_called_once_with(days=14, project='testproj', threads=True)
            mock_monitor.run.assert_called_once()

    def test_main_keyboard_interrupt(self):
        """Test main handling KeyboardInterrupt."""
        runner = CliRunner()
        
        with patch('ccmonitor.__main__.TimelineMonitor') as mock_monitor_class:
            mock_monitor = mock_monitor_class.return_value
            mock_monitor.run.side_effect = KeyboardInterrupt()
            
            result = runner.invoke(main, [])
            
            assert result.exit_code == 0
            assert "Exiting" in result.output

    def test_main_general_exception(self):
        """Test main handling general exceptions."""
        runner = CliRunner()
        
        with patch('ccmonitor.__main__.TimelineMonitor') as mock_monitor_class:
            mock_monitor = mock_monitor_class.return_value
            mock_monitor.run.side_effect = Exception("Test error")
            
            result = runner.invoke(main, [])
            
            assert result.exit_code == 0  # Click handles the exception
            assert "Error: Test error" in result.output

    def test_main_help(self):
        """Test main help output."""
        runner = CliRunner()
        
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "Claude Session Timeline" in result.output
        assert "--days" in result.output
        assert "--project" in result.output
        assert "--threads" in result.output

    def test_main_invalid_days_parameter(self):
        """Test main with invalid days parameter."""
        runner = CliRunner()
        
        result = runner.invoke(main, ['--days', 'invalid'])
        
        assert result.exit_code != 0
        assert "invalid" in result.output.lower()

    def test_cli_option_descriptions(self):
        """Test that CLI options have proper descriptions."""
        runner = CliRunner()
        
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        help_text = result.output
        
        # Check that all options have helpful descriptions
        assert "Number of days to look back" in help_text
        assert "Filter by specific project" in help_text
        assert "Show projects as threads" in help_text