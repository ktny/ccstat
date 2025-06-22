"""Process detection and monitoring functionality."""

from dataclasses import dataclass
from datetime import datetime

import psutil

from .claude_config import get_last_conversation_for_directory
from .constants import CLAUDE_COMMAND


@dataclass
class ProcessInfo:
    """Information about a Claude Code process."""

    pid: int
    name: str
    cpu_time: float
    start_time: datetime
    cwd: str
    last_conversation: str | None = None


def find_claude_processes() -> list[ProcessInfo]:
    """Find all Claude Code related processes.

    Returns:
        List of ProcessInfo objects for Claude Code processes.
    """
    claude_processes = []
    current_time = datetime.now()

    for proc in psutil.process_iter(["pid", "name", "create_time"]):
        try:
            pinfo = proc.info
            name = pinfo.get("name", "")

            # Check if this is a Claude Code process
            if name == CLAUDE_COMMAND:
                # Get additional process information
                cpu_times = proc.cpu_times()
                create_time = datetime.fromtimestamp(pinfo["create_time"])

                # Calculate CPU usage percentage
                cpu_time_total = cpu_times.user + cpu_times.system

                # Get current working directory
                try:
                    cwd = proc.cwd()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cwd = "unknown"

                # Get last conversation for this directory
                last_conversation = None
                if cwd != "unknown":
                    last_conversation = get_last_conversation_for_directory(cwd)

                process_info = ProcessInfo(
                    pid=pinfo["pid"],
                    name=name,
                    cpu_time=cpu_time_total,
                    start_time=create_time,
                    cwd=cwd,
                    last_conversation=last_conversation,
                )
                claude_processes.append(process_info)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Process may have terminated or we don't have permission
            continue

    return claude_processes
