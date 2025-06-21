"""Real-time monitoring functionality."""

import contextlib
import time
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .database import ProcessDatabase
from .process import (
    ProcessInfo,
    find_claude_processes,
    format_cpu_time,
    format_elapsed_time,
)


class RealTimeMonitor:
    """Real-time process monitor with live updating display."""

    def __init__(self, db: Optional[ProcessDatabase] = None):
        """Initialize the real-time monitor.

        Args:
            db: Database instance for persistence
        """
        self.db = db
        self.update_interval = 1.0
        self.console = Console()
        self.running = False
        self.last_update = datetime.now()
        self.update_count = 0

    def create_layout(self, processes: list[ProcessInfo]) -> Layout:
        """Create the layout for real-time display.

        Args:
            processes: Current process list

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

        # Header with title and stats
        header_text = Text.assemble(
            ("📊 Claude Code Monitor", "bold cyan"),
            " - ",
            ("Real-time Process Monitoring", "bold"),
        )

        # Add current time and update count
        now = datetime.now()
        time_text = Text.assemble(
            "\n",
            ("Last Update: ", "dim"),
            (now.strftime("%H:%M:%S"), "yellow"),
            ("  Updates: ", "dim"),
            (str(self.update_count), "green"),
        )

        layout["header"].update(Panel(header_text + time_text, border_style="blue"))

        # Main content with process table
        if processes:
            main_table = self._create_process_table(processes)
            layout["main"].update(main_table)
        else:
            no_processes_text = Text(
                "🔍 No Claude Code processes found", style="yellow", justify="center"
            )
            layout["main"].update(Panel(no_processes_text, border_style="yellow"))

        # Footer with controls and stats
        footer_text = Text.assemble(
            ("Controls: ", "bold"),
            ("Ctrl+C", "red"),
            (" to exit  ", ""),
            ("q", "red"),
            (" to quit  ", ""),
            ("Space", "cyan"),
            (" to force update", ""),
        )

        # Add database stats if available
        if self.db:
            try:
                stats = self.db.get_summary_stats()
                footer_text.append("\n")
                footer_text.append(
                    Text.assemble(
                        ("Database: ", "dim"),
                        (f"{stats['total_records']} records", "magenta"),
                        ("  Size: ", "dim"),
                        (
                            self._format_file_size(self.db.get_database_size()),
                            "magenta",
                        ),
                    )
                )
            except Exception:
                pass  # Ignore database errors in real-time display

        layout["footer"].update(Panel(footer_text, border_style="green"))

        return layout

    def _create_process_table(self, processes: list[ProcessInfo]) -> Table:
        """Create a table for displaying processes.

        Args:
            processes: List of ProcessInfo objects

        Returns:
            Rich Table object
        """
        table = Table(title=f"Claude Code Processes ({len(processes)} found)")
        table.add_column("PID", justify="right", style="cyan", no_wrap=True)
        table.add_column("CPU Time", justify="right", style="green")
        table.add_column("Elapsed", justify="right", style="yellow")

        for proc in processes:
            table.add_row(
                str(proc.pid),
                format_cpu_time(proc.cpu_time),
                format_elapsed_time(proc.elapsed_time),
            )

        return table

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def run(self) -> None:
        """Start the real-time monitoring loop."""
        self.running = True

        def generate():
            """Generator function for Live display updates."""
            while self.running:
                try:
                    # Find current processes
                    processes = find_claude_processes()

                    # Save to database if enabled
                    if self.db and processes:
                        with contextlib.suppress(Exception):
                            self.db.save_processes(processes)

                    # Update counters
                    self.last_update = datetime.now()
                    self.update_count += 1

                    # Yield the layout
                    yield self.create_layout(processes)

                    # Wait for next update
                    time.sleep(self.update_interval)

                except KeyboardInterrupt:
                    self.running = False
                    break
                except Exception:
                    # Continue on errors to maintain monitoring
                    time.sleep(self.update_interval)
                    continue

        # Start the live display
        try:
            with Live(refresh_per_second=2, screen=True) as live:
                # Show initial instruction
                self.console.print("Press Ctrl+C or 'q' to quit", style="dim")

                # Keep the live display running
                try:
                    for layout in generate():
                        live.update(layout)
                        if not self.running:
                            break
                except KeyboardInterrupt:
                    self.running = False

        except KeyboardInterrupt:
            self.running = False

        # Clean exit message
        self.console.print("\n👋 [bold green]Monitoring stopped.[/bold green]")

