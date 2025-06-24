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

    def display_timeline(self, timelines: list[SessionTimeline], start_time: datetime, end_time: datetime) -> None:
        """Display the timeline components directly to console.

        Args:
            timelines: List of session timelines to display
            start_time: Start of the time range
            end_time: End of the time range
        """
        # Header
        header_panel = self._create_header(start_time, end_time, len(timelines))
        self.console.print(header_panel)

        # Main content with timeline visualization
        if timelines:
            timeline_panel = self._create_timeline_panel(timelines, start_time, end_time)
            self.console.print(timeline_panel)
        else:
            no_sessions_text = Text(
                "🔍 No Claude sessions found in the specified time range", style="yellow", justify="center"
            )
            self.console.print(Panel(no_sessions_text, border_style="yellow"))

        # Footer
        footer_panel = self._create_footer()
        self.console.print(footer_panel)
        
        # Summary statistics (if there are timelines)
        if timelines:
            summary_text = self.create_summary_text(timelines)
            self.console.print(summary_text)

    def _create_header(self, start_time: datetime, end_time: datetime, session_count: int) -> Panel:
        """Create header panel with title and time range info."""
        duration = end_time - start_time
        hours = int(duration.total_seconds() / 3600)

        header_text = Text.assemble(
            ("📊 Claude Project Timeline", "bold cyan"),
            " - ",
            (f"{hours} hours", "bold"),
            " - ",
            (f"{session_count} projects", "yellow"),
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
            ("Activity Density: ", "bold"),
            ("■", "bright_black"),
            (" None  ", ""),
            ("■", "color(22)"),
            (" Low  ", ""),
            ("■", "color(28)"),
            (" Med  ", ""),
            ("■", "color(34)"),
            (" High  ", ""),
            ("■", "color(40)"),
            (" Max", ""),
        )
        return Panel(footer_text, border_style="green")

    def _create_timeline_panel(
        self, timelines: list[SessionTimeline], start_time: datetime, end_time: datetime
    ) -> Panel:
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
        table.add_column("Project", style="blue", no_wrap=True, width=20)
        table.add_column("Timeline", no_wrap=True)  # Remove style to let individual chars control color
        table.add_column("Events", style="cyan", justify="right", width=6)
        table.add_column("Duration", style="yellow", justify="center", width=8)

        # Calculate timeline width (console width - other columns - margins)
        # 20(dir) + 6(events) + 8(duration) + 2(padding per column) * 4 + 8(extra margin for safety)
        timeline_width = max(20, self.console.width - 50)

        # Add time axis row at the top
        time_axis_str = self._create_time_axis(start_time, end_time, timeline_width)
        table.add_row(
            "",  # Project column
            time_axis_str,  # Timeline column with time markers
            "",  # Events column
            "",  # Duration column
        )

        # Sort timelines - for thread display, keep parent-child order
        if any(t.parent_project for t in timelines):
            # Thread mode: sort by parent project first, then by start time
            sorted_timelines = sorted(timelines, key=lambda t: (
                t.parent_project or t.project_name,  # Parent project name for grouping
                t.parent_project is not None,         # Children after parent
                t.start_time                          # Then by start time
            ))
        else:
            # Normal mode: sort by number of events (descending)
            sorted_timelines = sorted(timelines, key=lambda t: len(t.events), reverse=True)

        # Add rows for each session
        for timeline in sorted_timelines:
            # Create visual timeline string
            timeline_str = self._create_timeline_string(timeline, start_time, end_time, timeline_width)

            # Calculate session duration
            duration = timeline.end_time - timeline.start_time
            duration_str = f"{int(duration.total_seconds() / 60)}m"

            # Add indent for child threads
            project_display = timeline.project_name
            if timeline.parent_project:
                project_display = f"  └─ {timeline.project_name}"

            table.add_row(
                project_display,
                timeline_str,
                str(len(timeline.events)),
                duration_str,
            )


        return Panel(table, title="Project Activity", border_style="cyan")

    def _create_timeline_string(
        self, timeline: SessionTimeline, start_time: datetime, end_time: datetime, width: int
    ) -> str:
        """Create a visual timeline string for a session with density-based display.

        Args:
            timeline: Session timeline data
            start_time: Start of the time range
            end_time: End of the time range
            width: Width of the timeline in characters

        Returns:
            String representation of the timeline with density-based markers
        """
        # Initialize timeline with square points (idle periods) - using very light gray
        timeline_chars = ["[bright_black]■[/bright_black]"] * width
        activity_counts = [0] * width  # Count messages per position

        # Calculate total duration
        total_duration = (end_time - start_time).total_seconds()

        # Count events per time position
        for event in timeline.events:
            event_offset = (event.timestamp - start_time).total_seconds()
            position = int((event_offset / total_duration) * (width - 1))

            if 0 <= position < width:
                activity_counts[position] += 1

        # Find max activity for normalization
        max_activity = max(activity_counts) if any(activity_counts) else 1

        # Create density-based markers
        for i, count in enumerate(activity_counts):
            if count > 0:
                # Calculate density level (0-4 scale)
                density_level = min(4, int((count / max_activity) * 4) + 1)

                # Use square markers with different green intensities (same hue, different saturation)
                if density_level == 1:
                    timeline_chars[i] = "[color(22)]■[/color(22)]"  # Light green (low saturation)
                elif density_level == 2:
                    timeline_chars[i] = "[color(28)]■[/color(28)]"  # Medium-light green
                elif density_level == 3:
                    timeline_chars[i] = "[color(34)]■[/color(34)]"  # Medium-heavy green
                else:  # density_level == 4
                    timeline_chars[i] = "[color(40)]■[/color(40)]"  # Heavy green (high saturation)

        # Create timeline string without borders (GitHub style)
        timeline_str = "".join(timeline_chars)

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

        # Place markers on even hours only for cleaner display
        for hour_offset in range(0, hours_count + 1):
            current_time = start_time + timedelta(hours=hour_offset)

            # Only show even hours (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22)
            if current_time.hour % 2 == 0:
                position = int((hour_offset * 3600 / total_duration) * (width - 1))
                if 0 <= position < width - 2:  # Leave space for hour string
                    # Format hour (just HH format for cleaner look)
                    hour_str = current_time.strftime("%H")

                    # Place the hour marker (2 characters)
                    for i, char in enumerate(hour_str):
                        if position + i < width:
                            axis_chars[position + i] = char

        # Return time axis without borders (GitHub style)
        return "".join(axis_chars)

    def create_summary_text(self, timelines: list[SessionTimeline]) -> Text:
        """Create summary statistics text.

        Args:
            timelines: List of session timelines

        Returns:
            Text containing summary statistics
        """
        if not timelines:
            return Text("")

        # Calculate statistics
        total_events = sum(len(t.events) for t in timelines)
        total_projects = len(timelines)

        # Find most active project
        most_active = max(timelines, key=lambda t: len(t.events))

        # Calculate average project duration
        durations = [(t.end_time - t.start_time).total_seconds() / 60 for t in timelines]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Create summary text
        summary_text = Text()
        summary_text.append("\nSummary Statistics:\n", style="bold cyan")
        summary_text.append(f"  • Total Projects: ", style="")
        summary_text.append(f"{total_projects}\n", style="yellow")
        summary_text.append(f"  • Total Events: ", style="")
        summary_text.append(f"{total_events}\n", style="yellow")
        summary_text.append(f"  • Average Project Duration: ", style="")
        summary_text.append(f"{avg_duration:.1f} minutes\n", style="yellow")
        summary_text.append(f"  • Most Active Project: ", style="")
        summary_text.append(f"{most_active.project_name}", style="yellow")
        summary_text.append(f" ({len(most_active.events)} events)", style="")

        return summary_text
