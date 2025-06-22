"""Claude configuration file reading functionality."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ClaudeSession:
    """Information about a Claude session in a directory."""

    directory: str
    last_conversation: str | None = None


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

        # Create session for this directory
        session = ClaudeSession(directory=directory)

        # The first conversation in history is the most recent
        if history and len(history) > 0:
            first_conv = history[0]
            display = first_conv.get("display")
            if display:
                session.last_conversation = format_conversation_preview(display)

        sessions_by_dir[directory] = session

    return sessions_by_dir


def get_last_conversation_for_directory(directory: str) -> str | None:
    """Get the last conversation for a specific directory.

    Args:
        directory: Directory path to search for

    Returns:
        Formatted string for the last conversation, or None if not found.
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


def format_conversation_preview(display: str | None) -> str:
    """Format conversation display text.

    Args:
        display: Display text or None

    Returns:
        Formatted string for display
    """
    if not display:
        return "No conversation"

    if len(display) > 30:
        return display[:27] + "..."
    return display
