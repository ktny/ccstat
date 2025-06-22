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

from .claude_config import ClaudeSession, format_conversation_preview, get_conversations_by_directory
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
        # Store previous CPU times for working status detection
        self.previous_cpu_times: dict[int, float] = {}

    def create_layout(self, processes: list[ProcessInfo], sessions: dict[str, ClaudeSession] | None = None) -> Layout:
        """Create the layout for real-time display.

        Args:
            processes: Current process list
            sessions: Dictionary mapping directory paths to ClaudeSession objects

        Returns:
            Rich Layout object
        """
        if sessions is None:
            sessions = {}
        layout = Layout()

        # Split into header, main content, and footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        # Main content with process table
        if processes:
            main_table = self._create_process_table(processes, sessions)
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

    def _create_process_table(self, processes: list[ProcessInfo], sessions: dict[str, ClaudeSession]) -> Table:
        """Create a table for displaying processes.

        Args:
            processes: List of ProcessInfo objects
            sessions: Dictionary mapping directory paths to ClaudeSession objects

        Returns:
            Rich Table object
        """
        console_width = self.console.width
        table = Table(title=f"Claude Code Processes ({len(processes)} found)", box=None)
        table.add_column("PID", justify="right", style="cyan", no_wrap=True, min_width=6)
        table.add_column("Directory", style="blue", no_wrap=True, min_width=12, max_width=20)
        table.add_column("Status", justify="center", style="bright_yellow", width=10)
        table.add_column("CPU Time", justify="right", style="green", no_wrap=True, width=10)
        table.add_column("Last Conversation", style="bright_cyan", no_wrap=True, max_width=console_width - 44)

        for proc in processes:
            # Format directory name (show only the deepest directory name)
            if proc.cwd == "unknown":
                directory = "unknown"
            else:
                directory = proc.cwd.rstrip("/").split("/")[-1] or "/"

            # Format conversation info from sessions
            last_conversation = None
            if proc.cwd in sessions:
                last_conversation = sessions[proc.cwd].last_conversation

            conversation_text = format_conversation_preview(last_conversation)

            # Format working status with icon
            if proc.is_working:
                status_text = "🟢Working"
            else:
                status_text = "⭕Idle"

            table.add_row(
                str(proc.pid),
                directory,
                status_text,
                format_time_duration(proc.cpu_time),
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

                    # Update is_working status based on CPU time changes
                    for process in processes:
                        previous_cpu_time = self.previous_cpu_times.get(process.pid, None)
                        if previous_cpu_time is not None:
                            # Process existed before, check if CPU time changed
                            process.is_working = (
                                process.cpu_time > previous_cpu_time + 0.2
                            )  # Threshold to avoid flickering
                        else:
                            # First time seeing this process, default to False
                            process.is_working = False

                        # Update previous CPU time for next iteration
                        self.previous_cpu_times[process.pid] = process.cpu_time

                    # Clean up old PIDs that are no longer active
                    current_pids = {proc.pid for proc in processes}
                    self.previous_cpu_times = {
                        pid: cpu_time for pid, cpu_time in self.previous_cpu_times.items() if pid in current_pids
                    }

                    # Get conversations by directory (once per update)
                    sessions = get_conversations_by_directory()

                    # Save to store if enabled
                    if self.db and processes:
                        with contextlib.suppress(Exception):
                            self.db.save_processes(processes)

                    # Yield the layout
                    yield self.create_layout(processes, sessions)

                except Exception:
                    # Continue monitoring even if process detection or UI creation fails
                    # Return empty layout to maintain display
                    yield self.create_layout([], {})

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
