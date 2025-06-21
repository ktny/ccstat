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

                process_info = ProcessInfo(
                    pid=pinfo["pid"],
                    name=name,
                    cpu_time=cpu_times.user + cpu_times.system,
                    start_time=create_time,
                    elapsed_time=elapsed,
                    cmdline=cmdline,
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


def format_elapsed_time(elapsed: timedelta) -> str:
    """Format elapsed time in a human-readable format.

    Args:
        elapsed: Time elapsed since process start

    Returns:
        Formatted time string (e.g., "1h 23m", "45m 30s", "12s")
    """
    total_seconds = int(elapsed.total_seconds())

    if total_seconds < 60:
        return f"{total_seconds}s"

    minutes = total_seconds // 60
    seconds = total_seconds % 60

    if minutes < 60:
        if seconds > 0:
            return f"{minutes}m {seconds}s"
        return f"{minutes}m"

    hours = minutes // 60
    minutes = minutes % 60

    if hours < 24:
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h"

    days = hours // 24
    hours = hours % 24

    if hours > 0:
        return f"{days}d {hours}h"
    return f"{days}d"


def format_cpu_time(cpu_time: float) -> str:
    """Format CPU time in a human-readable format.

    Args:
        cpu_time: CPU time in seconds

    Returns:
        Formatted CPU time string
    """
    if cpu_time < 1:
        return f"{cpu_time:.2f}s"
    elif cpu_time < 60:
        return f"{cpu_time:.1f}s"
    elif cpu_time < 3600:
        minutes = int(cpu_time // 60)
        seconds = cpu_time % 60
        return f"{minutes}m {seconds:.1f}s"
    else:
        hours = int(cpu_time // 3600)
        minutes = int((cpu_time % 3600) // 60)
        return f"{hours}h {minutes}m"
