"""Display functionality using Rich library."""

from rich.console import Console
from rich.table import Table

from .process import ProcessInfo, format_cpu_time, format_elapsed_time, format_memory


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


def display_summary(processes: list[ProcessInfo]) -> None:
    """Display summary statistics for Claude processes.

    Args:
        processes: List of ProcessInfo objects to summarize
    """
    console = Console()

    if not processes:
        console.print("🔍 [yellow]No Claude Code processes found[/yellow]")
        return

    # Calculate summary statistics
    total_memory = sum(proc.memory_mb for proc in processes)
    total_cpu_time = sum(proc.cpu_time for proc in processes)
    process_count = len(processes)

    # Find longest running process
    longest_running = max(processes, key=lambda p: p.elapsed_time.total_seconds())

    # Create summary table
    table = Table(title="📋 Claude Code Process Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Processes", str(process_count))
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
