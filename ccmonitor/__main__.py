"""Entry point for ccmonitor."""

import click

from ccmonitor import __version__
from ccmonitor.timeline_monitor import TimelineMonitor


@click.command()
@click.option(
    "--days",
    "-d",
    default=1,
    help="Number of days to look back (default: 1)",
    type=int,
)
@click.option(
    "--project",
    "-p",
    help="Filter by specific project",
    type=str,
)
@click.option(
    "--threads",
    "-t",
    is_flag=True,
    help="Show projects as threads (separate similar repos)",
)
@click.version_option(__version__, "-v", "--version", prog_name="ccmonitor")
@click.help_option("-h", "--help")
def main(days: int, project: str | None, threads: bool) -> None:
    """Claude Session Timeline - Claudeセッションの時系列可視化ツール."""
    try:
        monitor = TimelineMonitor(days=days, project=project, threads=threads)
        monitor.run()

    except KeyboardInterrupt:
        click.echo("\n👋 Exiting.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


if __name__ == "__main__":
    main()
