"""Timeline UI components for Claude session visualization."""

from datetime import datetime, timedelta

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .claude_logs import SessionTimeline


class TimelineUI:
    """UI component for displaying session timelines."""

    def __init__(self):
        """Initialize the timeline UI."""
        self.console = Console()

    def create_layout(self, timelines: list[SessionTimeline], start_time: datetime, end_time: datetime) -> Layout:
        """Create the main layout for timeline display.

        Args:
            timelines: List of session timelines to display
            start_time: Start of the time range
            end_time: End of the time range

        Returns:
            Rich Layout object
        """
        layout = Layout()

        # Split into header, main content, and footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        # Header
        header_panel = self._create_header(start_time, end_time, len(timelines))
        layout["header"].update(header_panel)

        # Main content with timeline visualization
        if timelines:
            timeline_panel = self._create_timeline_panel(timelines, start_time, end_time)
            layout["main"].update(timeline_panel)
        else:
            no_sessions_text = Text("🔍 No Claude sessions found in the specified time range", style="yellow", justify="center")
            layout["main"].update(Panel(no_sessions_text, border_style="yellow"))

        # Footer
        footer_panel = self._create_footer()
        layout["footer"].update(footer_panel)

        return layout

    def _create_header(self, start_time: datetime, end_time: datetime, session_count: int) -> Panel:
        """Create header panel with title and time range info."""
        duration = end_time - start_time
        hours = int(duration.total_seconds() / 3600)
        
        header_text = Text.assemble(
            ("📊 Claude Session Timeline", "bold cyan"),
            " - ",
            (f"{hours} hours", "bold"),
            " - ",
            (f"{session_count} sessions", "yellow"),
        )
        return Panel(header_text, border_style="blue")

    def _create_footer(self) -> Panel:
        """Create footer panel with controls."""
        footer_text = Text.assemble(
            ("Time Range: ", "bold"),
            ("24 hours", "green"),
            ("  |  ", "dim"),
            ("Sessions shown with activity markers", "dim"),
        )
        return Panel(footer_text, border_style="green")

    def _create_timeline_panel(self, timelines: list[SessionTimeline], start_time: datetime, end_time: datetime) -> Panel:
        """Create the main timeline visualization panel.

        Args:
            timelines: List of session timelines
            start_time: Start of visualization range
            end_time: End of visualization range

        Returns:
            Panel containing the timeline visualization
        """
        # Create a table for the timeline
        table = Table(show_header=True, box=None, padding=(0, 1))
        
        # Add columns
        table.add_column("Directory", style="blue", no_wrap=True, width=20)
        table.add_column("Timeline", style="white", no_wrap=True)
        table.add_column("Events", style="cyan", justify="right", width=6)
        
        # Calculate timeline width (console width - other columns)
        timeline_width = self.console.width - 35  # 20 (dir) + 6 (events) + padding
        
        # Add rows for each session
        for timeline in timelines:
            # Create visual timeline string
            timeline_str = self._create_timeline_string(
                timeline, start_time, end_time, timeline_width
            )
            
            table.add_row(
                timeline.directory_name,
                timeline_str,
                str(len(timeline.events)),
            )
        
        return Panel(table, title="Session Activity", border_style="cyan")

    def _create_timeline_string(self, timeline: SessionTimeline, start_time: datetime, end_time: datetime, width: int) -> str:
        """Create a visual timeline string for a session.

        Args:
            timeline: Session timeline data
            start_time: Start of the time range
            end_time: End of the time range
            width: Width of the timeline in characters

        Returns:
            String representation of the timeline
        """
        # Initialize timeline with dots
        timeline_chars = ["·"] * width
        
        # Calculate total duration
        total_duration = (end_time - start_time).total_seconds()
        
        # Mark active periods
        for i, event in enumerate(timeline.events):
            # Calculate position
            event_offset = (event.timestamp - start_time).total_seconds()
            position = int((event_offset / total_duration) * (width - 1))
            
            if 0 <= position < width:
                # Use different markers based on message type
                if event.message_type == "user":
                    timeline_chars[position] = "█"  # User message
                elif event.message_type == "assistant":
                    timeline_chars[position] = "▓"  # Assistant message
                else:
                    timeline_chars[position] = "░"  # Other
                
                # Connect events that are close together (within 5 minutes)
                if i > 0:
                    prev_event = timeline.events[i - 1]
                    time_diff = (event.timestamp - prev_event.timestamp).total_seconds()
                    
                    if time_diff < 300:  # 5 minutes
                        prev_offset = (prev_event.timestamp - start_time).total_seconds()
                        prev_position = int((prev_offset / total_duration) * (width - 1))
                        
                        # Fill the gap with line characters
                        for j in range(min(prev_position, position) + 1, max(prev_position, position)):
                            if 0 <= j < width and timeline_chars[j] == "·":
                                timeline_chars[j] = "─"
        
        # Add time markers
        timeline_str = "".join(timeline_chars)
        
        # Add start and end markers
        timeline_str = f"|{timeline_str}|"
        
        return timeline_str

    def create_time_axis(self, start_time: datetime, end_time: datetime, width: int) -> str:
        """Create a time axis string for reference.

        Args:
            start_time: Start time
            end_time: End time
            width: Width in characters

        Returns:
            Time axis string
        """
        # Create hour markers
        axis_chars = [" "] * width
        
        total_duration = (end_time - start_time).total_seconds()
        hours_count = int(total_duration / 3600)
        
        # Place hour markers
        for hour in range(0, hours_count + 1, 3):  # Every 3 hours
            position = int((hour * 3600 / total_duration) * (width - 1))
            if 0 <= position < width:
                # Format hour
                current_time = start_time + timedelta(hours=hour)
                hour_str = current_time.strftime("%H")
                
                # Place the hour marker
                for i, char in enumerate(hour_str):
                    if position + i < width:
                        axis_chars[position + i] = char
        
        return " " + "".join(axis_chars) + " "