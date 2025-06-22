"""Claude configuration file reading functionality."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any



@dataclass
class ConversationInfo:
    """Information about a Claude conversation."""

    display: str | None = None


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

    # Extract projects from config
    projects = config.get("projects", {})

    for directory, project_data in projects.items():
        # Get history for this directory
        history = project_data.get("history", [])
        if not history:
            continue

        conversations = []
        for conv_data in history:
            # Create conversation info
            conversation_info = ConversationInfo(
                display=conv_data.get("display"),
            )
            conversations.append(conversation_info)

        # Create session for this directory
        session = ClaudeSession(
            directory=directory,
            conversations=conversations,
        )

        # The first conversation in history is the most recent
        if conversations:
            session.last_conversation = conversations[0]

        sessions_by_dir[directory] = session

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
    if not conv or not conv.display:
        return "No conversation"

    if len(conv.display) > 30:
        return conv.display[:27] + "..."
    return conv.display
