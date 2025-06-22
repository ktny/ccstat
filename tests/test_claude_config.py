"""Tests for claude_config module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from ccmonitor.claude_config import (
    ClaudeSession,
    ConversationInfo,
    format_conversation_preview,
    get_conversations_by_directory,
    get_last_conversation_for_directory,
    load_claude_config,
)


class TestLoadClaudeConfig:
    """Tests for load_claude_config function."""

    def test_load_config_file_not_exists(self):
        """Test when .claude.json does not exist."""
        with patch("ccmonitor.claude_config.Path.home") as mock_home:
            mock_home.return_value = Path("/nonexistent")
            result = load_claude_config()
            assert result is None

    def test_load_config_valid_json(self):
        """Test loading valid JSON configuration."""
        config_data = {"conversations": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = Path(f.name)

        try:
            with patch("ccmonitor.claude_config.Path.home") as mock_home:
                mock_home.return_value = config_path.parent
                with patch("ccmonitor.claude_config.Path.__truediv__") as mock_div:
                    mock_div.return_value = config_path
                    result = load_claude_config()
                    assert result == config_data
        finally:
            config_path.unlink()

    def test_load_config_invalid_json(self):
        """Test loading invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            config_path = Path(f.name)

        try:
            with patch("ccmonitor.claude_config.Path.home") as mock_home:
                mock_home.return_value = config_path.parent
                with patch("ccmonitor.claude_config.Path.__truediv__") as mock_div:
                    mock_div.return_value = config_path
                    result = load_claude_config()
                    assert result is None
        finally:
            config_path.unlink()


class TestGetConversationsByDirectory:
    """Tests for get_conversations_by_directory function."""

    def test_empty_config(self):
        """Test with empty configuration."""
        result = get_conversations_by_directory({})
        assert result == {}

    def test_no_conversations(self):
        """Test with config that has no projects."""
        config = {"other_key": "value"}
        result = get_conversations_by_directory(config)
        assert result == {}

    def test_conversations_with_directory(self):
        """Test with conversations that have directory information."""
        config = {
            "projects": {
                "/home/user/project1": {
                    "history": [
                        {
                            "display": "Test conversation"
                        }
                    ]
                },
                "/home/user/project2": {
                    "history": [
                        {
                            "display": "Another conversation"
                        }
                    ]
                }
            }
        }

        result = get_conversations_by_directory(config)

        assert len(result) == 2
        assert "/home/user/project1" in result
        assert "/home/user/project2" in result

        session1 = result["/home/user/project1"]
        assert session1.directory == "/home/user/project1"
        assert len(session1.conversations) == 1
        assert session1.last_conversation.display == "Test conversation"

    def test_multiple_conversations_same_directory(self):
        """Test multiple conversations in the same directory."""
        config = {
            "projects": {
                "/home/user/project": {
                    "history": [
                        {
                            "display": "New conversation"
                        },
                        {
                            "display": "Old conversation"
                        }
                    ]
                }
            }
        }

        result = get_conversations_by_directory(config)

        assert len(result) == 1
        session = result["/home/user/project"]
        assert len(session.conversations) == 2
        # First item in history is the most recent
        assert session.last_conversation.display == "New conversation"


class TestGetLastConversationForDirectory:
    """Tests for get_last_conversation_for_directory function."""

    @patch("ccmonitor.claude_config.get_conversations_by_directory")
    def test_exact_match(self, mock_get_conversations):
        """Test exact directory match."""
        conv = ConversationInfo(
            display="Test conversation"
        )
        session = ClaudeSession(
            directory="/home/user/project",
            conversations=[conv],
            last_conversation=conv,
        )
        mock_get_conversations.return_value = {"/home/user/project": session}

        result = get_last_conversation_for_directory("/home/user/project")
        assert result == conv

    @patch("ccmonitor.claude_config.get_conversations_by_directory")
    def test_substring_match(self, mock_get_conversations):
        """Test substring directory match."""
        conv = ConversationInfo(
            display="Test conversation"
        )
        session = ClaudeSession(
            directory="/home/user/my-project",
            conversations=[conv],
            last_conversation=conv,
        )
        mock_get_conversations.return_value = {"/home/user/my-project": session}

        result = get_last_conversation_for_directory("/home/user")
        assert result == conv

    @patch("ccmonitor.claude_config.get_conversations_by_directory")
    def test_no_match(self, mock_get_conversations):
        """Test when no directory matches."""
        mock_get_conversations.return_value = {}

        result = get_last_conversation_for_directory("/nonexistent/path")
        assert result is None


class TestFormatConversationPreview:
    """Tests for format_conversation_preview function."""

    def test_none_conversation(self):
        """Test with None conversation."""
        result = format_conversation_preview(None)
        assert result == "No conversation"

    def test_conversation_with_display(self):
        """Test conversation with display."""
        conv = ConversationInfo(
            display="Short name"
        )
        result = format_conversation_preview(conv)
        assert result == "Short name"

    def test_conversation_with_long_display(self):
        """Test conversation with long display (should be truncated)."""
        conv = ConversationInfo(
            display="This is a very long conversation name that should be truncated"
        )
        result = format_conversation_preview(conv)
        assert result == "This is a very long convers..."
        assert len(result) == 30  # 27 chars + "..."


    def test_conversation_with_no_content(self):
        """Test conversation with no display."""
        conv = ConversationInfo()
        result = format_conversation_preview(conv)
        assert result == "No conversation"
