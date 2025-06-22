"""Claude configuration file reading functionality."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .util import parse_datetime


@dataclass
class ConversationInfo:
    """Information about a Claude conversation."""

    conversation_id: str
    last_activity: datetime
    name: str | None = None
    summary: str | None = None


@dataclass
class ClaudeSession:
    """Information about a Claude session in a directory."""

    directory: str
    conversations: list[ConversationInfo]
    last_conversation: ConversationInfo | None = None


def load_claude_config() -> dict[str, Any] | None:
    """Load Claude configuration from ~/.claude.json.

    Returns:
        Dictionary containing Claude configuration, or None if not found.
    """
    config_path = Path.home() / ".claude.json"

    if not config_path.exists():
        return None

    try:
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, PermissionError, OSError):
        return None


def get_conversations_by_directory(config: dict[str, Any] | None = None) -> dict[str, ClaudeSession]:
    """Get conversations organized by directory.

    Args:
        config: Claude configuration dictionary. If None, will load from file.

    Returns:
        Dictionary mapping directory paths to ClaudeSession objects.
    """
    if config is None:
        config = load_claude_config()

    if not config:
        return {}

    sessions_by_dir = {}

    # Extract conversations from config
    conversations = config.get("conversations", [])

    for conv_data in conversations:
        # Get directory information
        directory = conv_data.get("directory", "")
        if not directory:
            continue

        # Create conversation info
        conversation_info = ConversationInfo(
            conversation_id=conv_data.get("id", ""),
            last_activity=parse_datetime(conv_data.get("last_activity")),
            name=conv_data.get("name"),
            summary=conv_data.get("summary"),
        )

        # Add to directory session
        if directory not in sessions_by_dir:
            sessions_by_dir[directory] = ClaudeSession(
                directory=directory,
                conversations=[],
            )

        sessions_by_dir[directory].conversations.append(conversation_info)

    # Set last conversation for each directory
    for session in sessions_by_dir.values():
        if session.conversations:
            # Sort by last activity and get the most recent
            session.conversations.sort(key=lambda c: c.last_activity, reverse=True)
            session.last_conversation = session.conversations[0]

    return sessions_by_dir


def get_last_conversation_for_directory(directory: str) -> ConversationInfo | None:
    """Get the last conversation for a specific directory.

    Args:
        directory: Directory path to search for

    Returns:
        ConversationInfo for the last conversation, or None if not found.
    """
    sessions = get_conversations_by_directory()

    # Try exact match first
    if directory in sessions:
        return sessions[directory].last_conversation

    # Try to find a session that contains the directory as a substring
    for session_dir, session in sessions.items():
        if directory in session_dir or session_dir in directory:
            return session.last_conversation

    return None


def format_conversation_preview(conv: ConversationInfo | None) -> str:
    """Format conversation information for display.

    Args:
        conv: ConversationInfo object or None

    Returns:
        Formatted string for display
    """
    if not conv:
        return "No conversation"

    if conv.name:
        if len(conv.name) > 30:
            return conv.name[:27] + "..."
        return conv.name
    elif conv.summary:
        if len(conv.summary) > 30:
            return conv.summary[:27] + "..."
        return conv.summary
    else:
        return f"Conv {conv.conversation_id[:8]}"
