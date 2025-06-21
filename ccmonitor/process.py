"""Process detection and monitoring functionality."""

from dataclasses import dataclass
from datetime import datetime, timedelta

import psutil


@dataclass
class ProcessInfo:
    """Information about a Claude Code process."""

    pid: int
    name: str
    cpu_time: float
    start_time: datetime
    elapsed_time: timedelta
    cmdline: list[str]
    cpu_usage_percent: float


def find_claude_processes() -> list[ProcessInfo]:
    """Find all Claude Code related processes.

    Returns:
        List of ProcessInfo objects for Claude Code processes.
    """
    claude_processes = []
    current_time = datetime.now()

    for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
        try:
            pinfo = proc.info
            cmdline = pinfo.get("cmdline", [])
            name = pinfo.get("name", "")

            # Check if this is a Claude Code process
            if is_claude_process(name, cmdline):
                # Get additional process information
                cpu_times = proc.cpu_times()
                create_time = datetime.fromtimestamp(pinfo["create_time"])
                elapsed = current_time - create_time

                # Calculate CPU usage percentage
                cpu_time_total = cpu_times.user + cpu_times.system
                elapsed_seconds = elapsed.total_seconds()
                cpu_usage_percent = (cpu_time_total / elapsed_seconds * 100) if elapsed_seconds > 0 else 0.0

                process_info = ProcessInfo(
                    pid=pinfo["pid"],
                    name=name,
                    cpu_time=cpu_time_total,
                    start_time=create_time,
                    elapsed_time=elapsed,
                    cmdline=cmdline,
                    cpu_usage_percent=cpu_usage_percent,
                )
                claude_processes.append(process_info)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Process may have terminated or we don't have permission
            continue

    return claude_processes


def is_claude_process(name: str, cmdline: list[str]) -> bool:
    """Determine if a process is related to Claude Code.

    Args:
        name: Process name
        cmdline: Command line arguments (unused but kept for compatibility)

    Returns:
        True if this appears to be a Claude Code process
    """
    if not name:
        return False

    # Check if process name contains "claude"
    return "claude" in name.lower()


def format_time_duration(total_seconds: float) -> str:
    """Format time duration in hh:mm:ss format.

    Args:
        total_seconds: Total time in seconds

    Returns:
        Formatted time string (e.g., "1:23:45", "0:23:45", "0:00:12")
    """
    total_seconds = int(total_seconds)
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"
