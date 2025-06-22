"""Timeline monitoring functionality for Claude sessions."""

from datetime import datetime, timedelta

from rich.console import Console

from .claude_logs import load_sessions_in_timerange
from .timeline_ui import TimelineUI


class TimelineMonitor:
    """Monitor for displaying Claude session timelines."""

    def __init__(self, hours: int = 24):
        """Initialize the timeline monitor.

        Args:
            hours: Number of hours to look back (default: 24)
        """
        self.hours = hours
        self.console = Console()
        self.ui = TimelineUI()

    def run(self) -> None:
        """Display the timeline visualization."""
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=self.hours)
        
        try:
            # Load sessions in the time range
            self.console.print(f"[dim]Loading Claude sessions from the last {self.hours} hours...[/dim]")
            timelines = load_sessions_in_timerange(start_time, end_time)
            
            # Clear and display the timeline
            self.console.clear()
            
            # Create and display the layout
            layout = self.ui.create_layout(timelines, start_time, end_time)
            self.console.print(layout)
            
            # Display summary statistics
            self._display_summary(timelines, start_time, end_time)
            
        except Exception as e:
            self.console.print(f"[red]Error loading sessions: {e}[/red]")

    def _display_summary(self, timelines, start_time: datetime, end_time: datetime) -> None:
        """Display summary statistics below the timeline.

        Args:
            timelines: List of session timelines
            start_time: Start of the time range
            end_time: End of the time range
        """
        if not timelines:
            return
        
        # Calculate statistics
        total_events = sum(len(t.events) for t in timelines)
        total_sessions = len(timelines)
        
        # Find most active session
        most_active = max(timelines, key=lambda t: len(t.events))
        
        # Calculate average session duration
        durations = [(t.end_time - t.start_time).total_seconds() / 60 for t in timelines]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Create summary text
        self.console.print("\n[bold cyan]Summary Statistics:[/bold cyan]")
        self.console.print(f"  • Total Sessions: [yellow]{total_sessions}[/yellow]")
        self.console.print(f"  • Total Events: [yellow]{total_events}[/yellow]")
        self.console.print(f"  • Average Session Duration: [yellow]{avg_duration:.1f} minutes[/yellow]")
        self.console.print(f"  • Most Active Session: [yellow]{most_active.directory_name}[/yellow] ({len(most_active.events)} events)")
        
        # Add time range info
        self.console.print(f"\n[dim]Time Range: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}[/dim]")