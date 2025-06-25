"""Timeline UI components for Claude session visualization."""

from datetime import datetime, timedelta

from rich.console import Console
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
        table.add_column("Project", style="blue", no_wrap=True, width=30)
        table.add_column("Timeline", no_wrap=True)  # Remove style to let individual chars control color
        table.add_column("Events", style="cyan", justify="right", width=6)
        table.add_column("Duration", style="yellow", justify="center", width=8)

        # Calculate timeline width (console width - other columns - margins)
        # 30(dir) + 6(events) + 8(duration) + 2(padding per column) * 4 + 8(extra margin for safety)
        timeline_width = max(20, self.console.width - 60)

        # Add time axis row at the top
        time_axis_str = self._create_time_axis(start_time, end_time, timeline_width)
        table.add_row(
            "",  # Project column
            time_axis_str,  # Timeline column with time markers
            "",  # Events column
            "",  # Duration column
        )

        # Keep the sorting order from claude_logs.py (already sorted by event count with proper grouping)
        sorted_timelines = timelines

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

    def _determine_time_unit_and_interval(self, start_time: datetime, end_time: datetime, width: int) -> tuple[str, int, str]:
        """Determine the appropriate time unit and interval based on the time range.

        Args:
            start_time: Start time
            end_time: End time
            width: Available character width for timeline

        Returns:
            Tuple of (unit, interval_value, format_string)
            - unit: 'hour', 'day', 'week', 'month'
            - interval_value: numeric interval (e.g., 6 for 6-hour intervals)
            - format_string: strftime format for display
        """
        duration = end_time - start_time
        total_hours = duration.total_seconds() / 3600
        total_days = duration.days

        # Estimate label width (roughly 2-4 characters + spacing)
        min_spacing = 4
        max_markers = width // min_spacing

        if total_days <= 2:  # 1-2 days
            # Use 6-hour intervals: 00, 06, 12, 18
            intervals_needed = int(total_hours / 6) + 1
            if intervals_needed <= max_markers:
                return ('hour', 6, '%H')
            else:
                # Fall back to 12-hour intervals
                return ('hour', 12, '%H')

        elif total_days <= 14:  # 3-14 days
            # Use daily intervals
            if total_days <= max_markers:
                return ('day', 1, '%m/%d')
            else:
                # Use 2-day intervals
                return ('day', 2, '%m/%d')

        elif total_days <= 60:  # 15-60 days
            # Use weekly intervals
            weeks_needed = int(total_days / 7) + 1
            if weeks_needed <= max_markers:
                return ('week', 7, '%m/%d')
            else:
                # Use 2-week intervals
                return ('week', 14, '%m/%d')

        else:  # 60+ days
            # Use monthly intervals
            months_needed = int(total_days / 30) + 1
            if months_needed <= max_markers:
                return ('month', 30, '%b')
            else:
                # Use 2-month intervals
                return ('month', 60, '%b')

    def _create_time_axis(self, start_time: datetime, end_time: datetime, width: int) -> str:
        """Create a time axis string for reference with appropriate time units.

        Args:
            start_time: Start time
            end_time: End time
            width: Width in characters

        Returns:
            Time axis string with appropriate time markers
        """
        # Determine appropriate time unit and interval
        unit, interval_value, format_string = self._determine_time_unit_and_interval(start_time, end_time, width)

        # Create time markers
        axis_chars = [" "] * width
        total_duration = (end_time - start_time).total_seconds()

        if unit == 'hour':
            # Hour-based markers
            current_time = start_time.replace(minute=0, second=0, microsecond=0)
            # Align to interval boundaries (e.g., 00:00, 06:00, 12:00, 18:00)
            hour_offset = (current_time.hour // interval_value) * interval_value
            current_time = current_time.replace(hour=hour_offset)

            while current_time <= end_time:
                if current_time >= start_time:
                    time_offset = (current_time - start_time).total_seconds()
                    position = int((time_offset / total_duration) * (width - 1))

                    if 0 <= position < width - 2:  # Leave space for label
                        label = current_time.strftime(format_string)
                        for i, char in enumerate(label):
                            if position + i < width:
                                axis_chars[position + i] = char

                current_time += timedelta(hours=interval_value)

        elif unit == 'day':
            # Day-based markers
            current_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)

            while current_time <= end_time:
                if current_time >= start_time:
                    time_offset = (current_time - start_time).total_seconds()
                    position = int((time_offset / total_duration) * (width - 1))

                    if 0 <= position < width - 4:  # Leave space for MM/DD format
                        label = current_time.strftime(format_string)
                        for i, char in enumerate(label):
                            if position + i < width:
                                axis_chars[position + i] = char

                current_time += timedelta(days=interval_value)

        elif unit == 'week':
            # Week-based markers (show at start of each week)
            current_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            # Move to start of week (Monday)
            days_since_monday = current_time.weekday()
            current_time -= timedelta(days=days_since_monday)

            while current_time <= end_time:
                if current_time >= start_time:
                    time_offset = (current_time - start_time).total_seconds()
                    position = int((time_offset / total_duration) * (width - 1))

                    if 0 <= position < width - 4:  # Leave space for MM/DD format
                        label = current_time.strftime(format_string)
                        for i, char in enumerate(label):
                            if position + i < width:
                                axis_chars[position + i] = char

                current_time += timedelta(days=interval_value)

        elif unit == 'month':
            # Month-based markers
            current_time = start_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            while current_time <= end_time:
                if current_time >= start_time:
                    time_offset = (current_time - start_time).total_seconds()
                    position = int((time_offset / total_duration) * (width - 1))

                    if 0 <= position < width - 3:  # Leave space for month format
                        label = current_time.strftime(format_string)
                        for i, char in enumerate(label):
                            if position + i < width:
                                axis_chars[position + i] = char

                # Move to next month (handle year rollover)
                if current_time.month == 12:
                    current_time = current_time.replace(year=current_time.year + 1, month=1)
                else:
                    current_time = current_time.replace(month=current_time.month + 1)

                # Handle 2-month intervals
                if interval_value >= 60:  # 2+ month intervals
                    if current_time.month == 12:
                        current_time = current_time.replace(year=current_time.year + 1, month=1)
                    else:
                        current_time = current_time.replace(month=current_time.month + 1)

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
        summary_text.append("  • Total Projects: ", style="")
        summary_text.append(f"{total_projects}\n", style="yellow")
        summary_text.append("  • Total Events: ", style="")
        summary_text.append(f"{total_events}\n", style="yellow")
        summary_text.append("  • Average Project Duration: ", style="")
        summary_text.append(f"{avg_duration:.1f} minutes\n", style="yellow")
        summary_text.append("  • Most Active Project: ", style="")
        summary_text.append(f"{most_active.project_name}", style="yellow")
        summary_text.append(f" ({len(most_active.events)} events)", style="")

        return summary_text
