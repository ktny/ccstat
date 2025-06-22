"""Claude session log file reading functionality."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SessionEvent:
    """A single event in a Claude session."""

    timestamp: datetime
    session_id: str
    directory: str
    message_type: str  # "user", "assistant", etc.
    content_preview: str
    uuid: str


@dataclass
class SessionTimeline:
    """Timeline of events for a single Claude session."""

    session_id: str
    directory: str
    directory_name: str  # short name for display
    events: list[SessionEvent]
    start_time: datetime
    end_time: datetime


def parse_jsonl_file(file_path: Path) -> list[SessionEvent]:
    """Parse a JSONL file and extract session events.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of SessionEvent objects
    """
    events = []

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    
                    # Extract timestamp
                    timestamp_str = data.get("timestamp")
                    if not timestamp_str:
                        continue
                    
                    # Parse ISO format timestamp
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    # Convert to local timezone for comparison
                    if timestamp.tzinfo is not None:
                        timestamp = timestamp.replace(tzinfo=None)
                    
                    # Extract message content
                    message = data.get("message", {})
                    content = message.get("content", "")
                    role = message.get("role", data.get("type", "unknown"))
                    
                    # Handle different content types
                    if isinstance(content, list):
                        # Content is a list, extract text from first text item
                        text_parts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
                        content = " ".join(text_parts) if text_parts else str(content)
                    elif not isinstance(content, str):
                        content = str(content)
                    
                    # Create content preview (first 100 chars)
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    content_preview = content_preview.replace("\n", " ")
                    
                    event = SessionEvent(
                        timestamp=timestamp,
                        session_id=data.get("sessionId", ""),
                        directory=data.get("cwd", ""),
                        message_type=role,
                        content_preview=content_preview,
                        uuid=data.get("uuid", ""),
                    )
                    events.append(event)
                    
                except (json.JSONDecodeError, KeyError, ValueError):
                    # Skip malformed lines
                    continue
                    
    except (OSError, PermissionError):
        # Return empty list if file can't be read
        pass
    
    return events


def get_all_session_files() -> list[Path]:
    """Get all Claude session JSONL files.

    Returns:
        List of paths to JSONL files
    """
    projects_dir = Path.home() / ".claude" / "projects"
    
    if not projects_dir.exists():
        return []
    
    jsonl_files = []
    
    # Scan all subdirectories for JSONL files
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            for jsonl_file in project_dir.glob("*.jsonl"):
                jsonl_files.append(jsonl_file)
    
    return jsonl_files


def load_sessions_in_timerange(start_time: datetime, end_time: datetime) -> list[SessionTimeline]:
    """Load all Claude sessions within a time range, grouped by directory.

    Args:
        start_time: Start of time range
        end_time: End of time range

    Returns:
        List of SessionTimeline objects grouped by directory
    """
    all_events = []
    
    # Get all JSONL files
    jsonl_files = get_all_session_files()
    
    # Parse each file and collect events
    for file_path in jsonl_files:
        events = parse_jsonl_file(file_path)
        all_events.extend(events)
    
    # Filter events by time range
    filtered_events = [
        event for event in all_events
        if start_time <= event.timestamp <= end_time
    ]
    
    # Sort events by timestamp
    filtered_events.sort(key=lambda e: e.timestamp)
    
    # Group events by directory instead of session ID
    directories_dict = {}
    for event in filtered_events:
        directory = event.directory
        if directory not in directories_dict:
            directories_dict[directory] = []
        directories_dict[directory].append(event)
    
    # Create SessionTimeline objects for each directory
    timelines = []
    for directory, events in directories_dict.items():
        if not events:
            continue
        
        # Extract directory name for display
        directory_name = directory.rstrip("/").split("/")[-1] or "/"
        
        # Use directory as session_id for unified representation
        # Sort events by timestamp within this directory
        events.sort(key=lambda e: e.timestamp)
        
        timeline = SessionTimeline(
            session_id=f"dir_{directory_name}",  # Unique identifier for directory
            directory=directory,
            directory_name=directory_name,
            events=events,
            start_time=events[0].timestamp,
            end_time=events[-1].timestamp,
        )
        timelines.append(timeline)
    
    # Sort by start time
    timelines.sort(key=lambda t: t.start_time)
    
    return timelines