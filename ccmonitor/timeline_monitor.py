"""Timeline monitoring functionality for Claude sessions."""

from datetime import datetime, timedelta

from rich.console import Console

from .claude_logs import load_sessions_in_timerange
from .timeline_ui import TimelineUI


class TimelineMonitor:
    """Monitor for displaying Claude session timelines."""

    def __init__(self, days: int = 1, project: str | None = None, threads: bool = False):
        """Initialize the timeline monitor.

        Args:
            days: Number of days to look back (default: 1)
            project: Filter by specific project name (default: None)
            threads: Show projects as threads (default: False)
        """
        self.days = days
        self.project = project
        self.threads = threads
        self.console = Console()
        self.ui = TimelineUI()

    def run(self) -> None:
        """Display the timeline visualization."""
        # Calculate time range in local time
        now = datetime.now()
        # Use current time as end_time to include all recent events
        end_time = now
        # Calculate start_time as exactly N days before end_time
        start_time = end_time - timedelta(days=self.days)

        try:
            # Load sessions in the time range
            loading_msg = f"[dim]Loading Claude sessions from the last {self.days} days"
            if self.project:
                loading_msg += f" (filtered by project: {self.project})"
            loading_msg += "...[/dim]"
            self.console.print(loading_msg)
            timelines = load_sessions_in_timerange(
                start_time, end_time, project_filter=self.project, threads=self.threads
            )

            # Clear console
            self.console.clear()

            # Display components separately for better control
            self.ui.display_timeline(timelines, start_time, end_time)

        except Exception as e:
            self.console.print(f"[red]Error loading sessions: {e}[/red]")
