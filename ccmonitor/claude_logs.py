"""Claude session log file reading functionality."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .git_utils import get_repository_name

# Configure logger for debug output
logger = logging.getLogger(__name__)


@dataclass
class SessionEvent:
    """A single event in a Claude session."""

    timestamp: datetime
    session_id: str
    directory: str  # Keep as directory since it's the actual cwd from logs
    message_type: str  # "user", "assistant", etc.
    content_preview: str
    uuid: str


@dataclass
class SessionTimeline:
    """Timeline of events for a single Claude session."""

    session_id: str
    directory: str  # Full path from logs
    project_name: str  # short name for display
    events: list[SessionEvent]
    start_time: datetime
    end_time: datetime
    active_duration_minutes: int = 0  # Active work time in minutes
    parent_project: str | None = None  # Parent project name for thread display


def parse_jsonl_file(file_path: Path) -> list[SessionEvent]:
    """Parse a JSONL file and extract session events.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of SessionEvent objects
    """
    events = []
    filtered_count = 0  # Track messages filtered out
    total_count = 0  # Track total messages processed

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    total_count += 1

                    # Extract timestamp
                    timestamp_str = data.get("timestamp")
                    if not timestamp_str:
                        filtered_count += 1
                        logger.debug(f"Filtered message at line {line_num}: no timestamp")
                        continue

                    # Parse ISO format timestamp and convert to local time
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    # Convert UTC to local timezone
                    if timestamp.tzinfo is not None:
                        timestamp = timestamp.astimezone().replace(tzinfo=None)

                    # Extract message content
                    message = data.get("message", {})
                    content = message.get("content", "")
                    role = message.get("role", data.get("type", "unknown"))

                    # Handle different content types
                    if isinstance(content, list):
                        # Content is a list, extract text from first text item
                        text_parts = [
                            item.get("text", "")
                            for item in content
                            if isinstance(item, dict) and item.get("type") == "text"
                        ]
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

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # Skip malformed lines
                    filtered_count += 1
                    logger.debug(f"Filtered malformed JSON at line {line_num}: {e}")
                    continue

    except (OSError, PermissionError):
        # Return empty list if file can't be read
        pass

    # Log parsing summary
    if total_count > 0:
        logger.debug(
            f"Parsed {file_path.name}: {len(events)} events included, {filtered_count} filtered out of {total_count} total messages"
        )

    return events


def calculate_active_duration(events: list[SessionEvent]) -> int:
    """Calculate active work duration based on event intervals.

    Args:
        events: List of session events

    Returns:
        Active work time in minutes
    """
    if len(events) <= 1:
        return 5  # Minimum 5 minutes for single event

    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    active_minutes = 0
    inactive_threshold = 3  # 3 minute threshold for inactive periods

    for i in range(1, len(sorted_events)):
        prev_event = sorted_events[i - 1]
        curr_event = sorted_events[i]

        interval_minutes = (curr_event.timestamp - prev_event.timestamp).total_seconds() / 60

        # Only count intervals up to the threshold as active time
        if interval_minutes <= inactive_threshold:
            active_minutes += interval_minutes
        # If interval is longer than threshold, don't add any time
        # (this represents an inactive period)

    return int(active_minutes)


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


def load_sessions_in_timerange(
    start_time: datetime, end_time: datetime, project_filter: str | None = None, threads: bool = False
) -> list[SessionTimeline]:
    """Load all Claude sessions within a time range, grouped by project directory.

    Args:
        start_time: Start of time range
        end_time: End of time range
        project_filter: Optional project name filter (partial match)
        threads: If True, separate projects with same repo name; if False, group them

    Returns:
        List of SessionTimeline objects grouped by project
    """
    all_events = []

    # Get all JSONL files
    jsonl_files = get_all_session_files()

    # Parse each file and collect events (with mtime filtering)
    for file_path in jsonl_files:
        # Check file modification time for performance optimization
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        # Skip files that were last modified before the start time
        # If a file hasn't been modified since before start_time, it cannot contain events within our time range
        if file_mtime < start_time:
            continue
        
        events = parse_jsonl_file(file_path)
        all_events.extend(events)

    # Filter events by time range
    filtered_events = [event for event in all_events if start_time <= event.timestamp <= end_time]

    # Sort events by timestamp
    filtered_events.sort(key=lambda e: e.timestamp)

    # Group events by project directory or repository name
    if threads:
        # When threads=True, keep each directory separate
        projects_dict = {}
        for event in filtered_events:
            directory = event.directory
            if directory not in projects_dict:
                projects_dict[directory] = []
            projects_dict[directory].append(event)
    else:
        # When threads=False, group by repository name
        projects_dict = {}
        repo_names = {}  # Cache for directory -> repo name mapping

        # First pass: collect all directories and identify git repositories
        all_directories = list(set(event.directory for event in filtered_events))
        git_repo_dirs = {}  # directory -> repo_name mapping for existing git repos

        for directory in all_directories:
            repo_name = get_repository_name(directory)
            if repo_name:
                git_repo_dirs[directory] = repo_name

        # Second pass: resolve repository names for all directories
        for directory in all_directories:
            if directory in git_repo_dirs:
                # Direct git repository
                repo_names[directory] = git_repo_dirs[directory]
            else:
                # Check if directory is under any git repository (prefix match)
                matched_repo = None
                for git_dir, git_repo_name in git_repo_dirs.items():
                    if directory.startswith(git_dir + "/"):
                        matched_repo = git_repo_name
                        break

                if matched_repo:
                    repo_names[directory] = matched_repo
                else:
                    # Use directory name as fallback
                    repo_names[directory] = directory.rstrip("/").split("/")[-1] or "/"

        # Group events by resolved repository name
        for event in filtered_events:
            directory = event.directory
            group_key = repo_names[directory]
            if group_key not in projects_dict:
                projects_dict[group_key] = []
            projects_dict[group_key].append(event)

    # Create SessionTimeline objects
    timelines = []
    if threads:
        # Create timeline for each directory with parent-child relationship
        repo_to_dirs = {}  # Map repository name to list of directories

        # Apply same integration logic as non-threads mode
        all_directories = list(projects_dict.keys())
        git_repo_dirs = {}  # directory -> repo_name mapping for existing git repos

        for directory in all_directories:
            repo_name = get_repository_name(directory)
            if repo_name:
                git_repo_dirs[directory] = repo_name

        # Resolve repository names for all directories using integration logic
        repo_names = {}
        for directory in all_directories:
            if directory in git_repo_dirs:
                # Direct git repository
                repo_names[directory] = git_repo_dirs[directory]
            else:
                # Check if directory is under any git repository (prefix match)
                matched_repo = None
                for git_dir, git_repo_name in git_repo_dirs.items():
                    if directory.startswith(git_dir + "/"):
                        matched_repo = git_repo_name
                        break

                if matched_repo:
                    repo_names[directory] = matched_repo
                else:
                    # Use directory name as fallback
                    repo_names[directory] = directory.rstrip("/").split("/")[-1] or "/"

        # Group directories by resolved repository name
        for directory, events in projects_dict.items():
            if not events:
                continue

            key = repo_names[directory]
            if key not in repo_to_dirs:
                repo_to_dirs[key] = []
            repo_to_dirs[key].append((directory, events))

        # Create timelines with parent information
        for repo_name, dir_list in repo_to_dirs.items():
            # Sort directories: main repo first, then by first event time
            def sort_key(item, current_repo_name=repo_name):
                directory, events = item
                # Main repository comes first (exact match)
                is_main_repo = directory in git_repo_dirs and git_repo_dirs[directory] == current_repo_name
                return (not is_main_repo, events[0].timestamp)

            dir_list.sort(key=sort_key)

            for idx, (directory, events) in enumerate(dir_list):
                # Sort events by timestamp
                events.sort(key=lambda e: e.timestamp)

                # First directory (main repo) is parent, others are children
                parent_project = None

                if idx == 0:
                    # Main repository - use repo name as is
                    display_name = repo_name
                else:
                    # Child directory - show as subdirectory name with parent
                    parent_project = repo_name

                    # Find the main repo directory this subdirectory belongs to
                    main_repo_dir = None
                    for git_dir, git_repo_name in git_repo_dirs.items():
                        if directory.startswith(git_dir + "/") and git_repo_name == repo_name:
                            main_repo_dir = git_dir
                            break

                    if main_repo_dir:
                        # Extract relative path from main repo and use only the leaf directory name
                        relative_path = directory[len(main_repo_dir) :].lstrip("/")
                        display_name = (
                            relative_path.split("/")[-1] if relative_path else directory.rstrip("/").split("/")[-1]
                        )
                    else:
                        # Fallback to directory name
                        display_name = directory.rstrip("/").split("/")[-1]

                timeline = SessionTimeline(
                    session_id=f"dir_{directory}",  # Unique identifier
                    directory=directory,
                    project_name=display_name,
                    events=events,
                    start_time=events[0].timestamp,
                    end_time=events[-1].timestamp,
                    active_duration_minutes=calculate_active_duration(events),
                    parent_project=parent_project,
                )
                timelines.append(timeline)
    else:
        # Create timeline for each repository group
        for group_key, events in projects_dict.items():
            if not events:
                continue

            # Use the first directory as representative
            directory = events[0].directory

            # Sort events by timestamp
            events.sort(key=lambda e: e.timestamp)

            timeline = SessionTimeline(
                session_id=f"repo_{group_key}",  # Unique identifier
                directory=directory,
                project_name=group_key,
                events=events,
                start_time=events[0].timestamp,
                end_time=events[-1].timestamp,
                active_duration_minutes=calculate_active_duration(events),
            )
            timelines.append(timeline)

    # Sort by group event count (descending), then group timelines together
    if threads:
        # For threads mode, group timelines by parent project and sort groups by total events
        group_timelines = {}  # parent_project -> list of timelines
        standalone_timelines = []  # timelines without parent

        for timeline in timelines:
            if timeline.parent_project:
                if timeline.parent_project not in group_timelines:
                    group_timelines[timeline.parent_project] = []
                group_timelines[timeline.parent_project].append(timeline)
            else:
                standalone_timelines.append(timeline)

        # Calculate total events for each group (including parent)
        group_totals = {}
        for parent_timeline in standalone_timelines:
            total_events = len(parent_timeline.events)
            if parent_timeline.project_name in group_timelines:
                for child_timeline in group_timelines[parent_timeline.project_name]:
                    total_events += len(child_timeline.events)
            group_totals[parent_timeline.project_name] = total_events

        # Sort standalone timelines by their group total events (descending)
        standalone_timelines.sort(key=lambda t: group_totals.get(t.project_name, 0), reverse=True)

        # Rebuild timelines list with groups together
        sorted_timelines = []
        for parent_timeline in standalone_timelines:
            sorted_timelines.append(parent_timeline)
            # Add child timelines for this group, sorted by event count (descending)
            if parent_timeline.project_name in group_timelines:
                child_timelines = group_timelines[parent_timeline.project_name]
                child_timelines.sort(key=lambda t: len(t.events), reverse=True)
                sorted_timelines.extend(child_timelines)

        timelines = sorted_timelines
    else:
        # For non-threads mode, sort by event count (descending)
        timelines.sort(key=lambda t: len(t.events), reverse=True)

    # Apply project filter if specified
    if project_filter:
        filtered_timelines = []
        for timeline in timelines:
            # Check if project name contains the filter string (case-insensitive)
            if project_filter.lower() in timeline.project_name.lower():
                filtered_timelines.append(timeline)
        return filtered_timelines

    return timelines
