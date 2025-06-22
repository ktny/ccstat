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
            Layout(name="header", size=4),
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
            ("📊 Claude Directory Timeline", "bold cyan"),
            " - ",
            (f"{hours} hours", "bold"),
            " - ",
            (f"{session_count} directories", "yellow"),
            "\n",
            ("Time Range: ", "dim"),
            (start_time.strftime("%m/%d %H:%M"), "cyan"),
            (" - ", "dim"),
            (end_time.strftime("%m/%d %H:%M"), "cyan"),
        )
        return Panel(header_text, border_style="blue")


    def _create_footer(self) -> Panel:
        """Create footer panel with controls."""
        footer_text = Text.assemble(
            ("Legend: ", "bold"),
            ("█", "white"),
            (" User  ", ""),
            ("▓", "white"),
            (" Assistant  ", ""),
            ("─", "white"),
            (" Activity  ", ""),
            ("·", "dim"),
            (" Idle", ""),
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
        table.add_column("Directory", style="blue", no_wrap=True, width=15)
        table.add_column("Start", style="yellow", justify="center", width=8)
        table.add_column("End", style="yellow", justify="center", width=8)
        table.add_column("Timeline", style="white", no_wrap=True)
        table.add_column("Events", style="cyan", justify="right", width=6)
        table.add_column("Duration", style="green", justify="center", width=8)
        
        # Calculate timeline width (console width - other columns)
        timeline_width = self.console.width - 58  # 15(dir) + 8(start) + 8(end) + 6(events) + 8(duration) + padding
        
        # Add rows for each session
        for timeline in timelines:
            # Create visual timeline string
            timeline_str = self._create_timeline_string(
                timeline, start_time, end_time, timeline_width
            )
            
            # Calculate session duration
            duration = timeline.end_time - timeline.start_time
            duration_str = f"{int(duration.total_seconds() / 60)}m"
            
            # Format start and end times
            start_str = timeline.start_time.strftime("%H:%M")
            end_str = timeline.end_time.strftime("%H:%M")
            
            table.add_row(
                timeline.directory_name,
                start_str,
                end_str,
                timeline_str,
                str(len(timeline.events)),
                duration_str,
            )
        
        # Add time axis row at the bottom
        time_axis_str = self._create_time_axis(start_time, end_time, timeline_width)
        table.add_row(
            "",  # Directory column
            "",  # Start column
            "",  # End column
            time_axis_str,  # Timeline column with time markers
            "",  # Events column
            "",  # Duration column
        )
        
        return Panel(table, title="Directory Activity", border_style="cyan")

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

    def _create_time_axis(self, start_time: datetime, end_time: datetime, width: int) -> str:
        """Create a time axis string for reference.

        Args:
            start_time: Start time
            end_time: End time
            width: Width in characters

        Returns:
            Time axis string with hour markers
        """
        # Create hour markers
        axis_chars = [" "] * width
        
        total_duration = (end_time - start_time).total_seconds()
        hours_count = int(total_duration / 3600)
        
        # Place markers only on even hours for cleaner display
        start_hour = start_time.hour
        for hour_offset in range(0, hours_count + 1, 2):  # Every 2 hours
            hour = hour_offset
            current_time = start_time + timedelta(hours=hour)
            
            # Only show even hours
            if current_time.hour % 2 == 0:
                position = int((hour * 3600 / total_duration) * (width - 1))
                if 0 <= position < width - 3:  # Leave space for hour string
                    # Format hour (just HH format for cleaner look)
                    hour_str = current_time.strftime("%H")
                    
                    # Clear the area first to avoid overlaps
                    for i in range(3):
                        if position + i < width:
                            axis_chars[position + i] = " "
                    
                    # Place the hour marker
                    for i, char in enumerate(hour_str):
                        if position + i < width:
                            axis_chars[position + i] = char
        
        # Add start and end markers
        result = "|" + "".join(axis_chars) + "|"
        return result