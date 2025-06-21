"""Display functionality using Rich library."""

from datetime import timedelta
from typing import TYPE_CHECKING, Optional

from rich.console import Console
from rich.table import Table

from .process import ProcessInfo, format_cpu_time, format_elapsed_time, format_memory

if TYPE_CHECKING:
    from .database import ProcessDatabase


def display_processes_table(processes: list[ProcessInfo]) -> None:
    """Display Claude processes in a formatted table.

    Args:
        processes: List of ProcessInfo objects to display
    """
    console = Console()

    if not processes:
        console.print("🔍 [yellow]No Claude Code processes found[/yellow]")
        return

    # Create table
    table = Table(title="📊 Claude Code Processes")
    table.add_column("PID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("CPU Time", justify="right", style="green")
    table.add_column("Memory", justify="right", style="blue")
    table.add_column("Elapsed", justify="right", style="yellow")
    table.add_column("Command", style="dim", max_width=50)

    # Add rows
    for proc in processes:
        # Truncate command line for display
        cmd_display = " ".join(proc.cmdline)
        if len(cmd_display) > 50:
            cmd_display = cmd_display[:47] + "..."

        table.add_row(
            str(proc.pid),
            proc.name,
            format_cpu_time(proc.cpu_time),
            format_memory(proc.memory_mb),
            format_elapsed_time(proc.elapsed_time),
            cmd_display,
        )

    console.print(table)
    console.print(f"\n📈 [bold]Total processes found: {len(processes)}[/bold]")


def display_summary(
    processes: list[ProcessInfo], db: Optional["ProcessDatabase"] = None
) -> None:
    """Display summary statistics for Claude processes.

    Args:
        processes: List of ProcessInfo objects to summarize
        db: Optional database instance for historical stats
    """
    console = Console()

    if not processes:
        console.print("🔍 [yellow]No Claude Code processes found[/yellow]")
    else:
        # Calculate current process statistics
        total_memory = sum(proc.memory_mb for proc in processes)
        total_cpu_time = sum(proc.cpu_time for proc in processes)
        process_count = len(processes)

        # Find longest running process
        longest_running = max(processes, key=lambda p: p.elapsed_time.total_seconds())

        # Create current processes table
        table = Table(title="📋 Current Claude Code Processes")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Running Processes", str(process_count))
        table.add_row("Total Memory Usage", format_memory(total_memory))
        table.add_row("Total CPU Time", format_cpu_time(total_cpu_time))
        table.add_row(
            "Longest Running",
            f"PID {longest_running.pid} ({format_elapsed_time(longest_running.elapsed_time)})",
        )

        if process_count > 0:
            avg_memory = total_memory / process_count
            table.add_row("Average Memory", format_memory(avg_memory))

        console.print(table)

    # Display database statistics if available
    if db:
        try:
            stats = db.get_summary_stats()

            console.print("\n")
            db_table = Table(title="📊 Historical Database Statistics")
            db_table.add_column("Metric", style="cyan")
            db_table.add_column("Value", style="magenta")

            db_table.add_row("Total Records", str(stats["total_records"]))
            db_table.add_row("Unique Processes", str(stats["unique_processes"]))
            db_table.add_row("Database Size", _format_file_size(db.get_database_size()))

            if stats["oldest_record"] and stats["newest_record"]:
                db_table.add_row(
                    "Data Range",
                    f"{stats['oldest_record'].strftime('%Y-%m-%d')} to {stats['newest_record'].strftime('%Y-%m-%d')}",
                )

            console.print(db_table)
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not load database statistics: {e}[/yellow]"
            )


def display_history(db: "ProcessDatabase", limit: int = 20) -> None:
    """Display historical process information from database.

    Args:
        db: Database instance
        limit: Maximum number of records to display
    """
    console = Console()

    try:
        records = db.get_recent_processes(limit)

        if not records:
            console.print("🔍 [yellow]No historical process data found[/yellow]")
            return

        # Create history table
        table = Table(title=f"📜 Recent Process History (Last {len(records)} records)")
        table.add_column("PID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("CPU Time", justify="right", style="green")
        table.add_column("Memory", justify="right", style="blue")
        table.add_column("Elapsed", justify="right", style="yellow")
        table.add_column("Recorded", justify="right", style="dim")
        table.add_column("Status", style="red")

        for record in records:
            # Format elapsed time from seconds
            elapsed = timedelta(seconds=record["elapsed_seconds"])

            # Format recorded time
            recorded_time = record["recorded_at"].strftime("%m-%d %H:%M")

            # Format status with emoji
            status_display = (
                "🟢 Running" if record["status"] == "running" else "🔴 Terminated"
            )

            table.add_row(
                str(record["pid"]),
                record["name"],
                format_cpu_time(record["cpu_time"]),
                format_memory(record["memory_mb"]),
                format_elapsed_time(elapsed),
                recorded_time,
                status_display,
            )

        console.print(table)

        # Display summary stats
        stats = db.get_summary_stats()
        console.print(
            f"\n📈 [bold]Total records in database: {stats['total_records']}[/bold]"
        )
        console.print(
            f"💾 [bold]Database size: {_format_file_size(db.get_database_size())}[/bold]"
        )

    except Exception as e:
        console.print(f"❌ [red]Error loading historical data: {e}[/red]")


def _format_file_size(size_bytes: int) -> str:
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
