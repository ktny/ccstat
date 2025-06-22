"""Real-time monitoring functionality."""

import contextlib
import time
from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .claude_config import format_conversation_preview
from .process import ProcessInfo, find_claude_processes
from .store import ProcessStore
from .util import format_time_duration


class RealTimeMonitor:
    """Real-time process monitor with live updating display."""

    def __init__(self, db: ProcessStore | None = None):
        """Initialize the real-time monitor.

        Args:
            db: Store instance for persistence
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

        # Main content with process table
        if processes:
            main_table = self._create_process_table(processes)
            layout["main"].update(main_table)
        else:
            no_processes_text = Text("🔍 No Claude Code processes found", style="yellow", justify="center")
            layout["main"].update(Panel(no_processes_text, border_style="yellow"))

        header_panel = self._create_header()
        layout["header"].update(header_panel)

        footer_panel = self._create_footer()
        layout["footer"].update(footer_panel)

        return layout

    def _create_header(self) -> Panel:
        # Header with title and stats
        now = datetime.now()
        header_text = Text.assemble(
            ("📊 Claude Code Monitor", "bold cyan"),
            " - ",
            ("Real-time Process Monitoring", "bold"),
            " - ",
            ("Last Update: ", "dim"),
            (now.strftime("%H:%M:%S"), "yellow"),
        )
        return Panel(header_text, border_style="blue")

    def _create_footer(self) -> Panel:
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
        return Panel(footer_text, border_style="green")

    def _create_process_table(self, processes: list[ProcessInfo]) -> Table:
        """Create a table for displaying processes.

        Args:
            processes: List of ProcessInfo objects

        Returns:
            Rich Table object
        """
        table = Table(title=f"Claude Code Processes ({len(processes)} found)")
        table.add_column("PID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Directory", justify="left", style="blue", min_width=20)
        table.add_column("CPU Time", justify="right", style="green")
        table.add_column("Elapsed", justify="right", style="yellow")
        table.add_column("Operating Rate", justify="right", style="magenta")
        table.add_column("Last Conversation", justify="left", style="bright_cyan", min_width=25)

        for proc in processes:
            # Format directory name (show only the deepest directory name)
            if proc.cwd == "unknown":
                directory = "unknown"
            else:
                directory = proc.cwd.rstrip("/").split("/")[-1] or "/"

            # Format conversation info
            conversation_text = format_conversation_preview(proc.last_conversation)

            table.add_row(
                str(proc.pid),
                directory,
                format_time_duration(proc.cpu_time),
                format_time_duration(proc.elapsed_time.total_seconds()),
                f"{proc.cpu_usage_percent:.1f}%",
                conversation_text,
            )

        return table

    def run(self) -> None:
        """Start the real-time monitoring loop."""
        self.running = True

        def generate():
            """Generator function for Live display updates."""
            while self.running:
                try:
                    # Find current processes
                    processes = find_claude_processes()

                    # Save to store if enabled
                    if self.db and processes:
                        with contextlib.suppress(Exception):
                            self.db.save_processes(processes)

                    # Update counters
                    self.last_update = datetime.now()
                    self.update_count += 1

                    # Yield the layout
                    yield self.create_layout(processes)

                except Exception:
                    # Continue monitoring even if process detection or UI creation fails
                    # Return empty layout to maintain display
                    yield self.create_layout([])

                # Wait for next update
                time.sleep(self.update_interval)

        # Start the live display with single KeyboardInterrupt handler
        try:
            with Live(refresh_per_second=2, screen=True) as live:
                # Keep the live display running
                for layout in generate():
                    live.update(layout)
                    if not self.running:
                        break

        except KeyboardInterrupt:
            self.running = False

        # Clean exit message
        self.console.print("\n👋 [bold green]Monitoring stopped.[/bold green]")
