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
    "--hours",
    "-t",
    help="Number of hours to look back (1-24, overrides --days)",
    type=click.IntRange(1, 24),
)
@click.option(
    "--project",
    "-p",
    help="Filter by specific project",
    type=str,
)
@click.option(
    "--worktree",
    "-w",
    is_flag=True,
    help="Show projects as worktree (separate similar repos)",
)
@click.version_option(__version__, "-v", "--version", prog_name="ccmonitor")
@click.help_option("-h", "--help")
def main(days: int, hours: int | None, project: str | None, worktree: bool) -> None:
    """Claude Session Timeline - Claudeセッションの時系列可視化ツール."""
    try:
        monitor = TimelineMonitor(days=days, hours=hours, project=project, threads=worktree)
        monitor.run()

    except KeyboardInterrupt:
        click.echo("\n👋 Exiting.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


if __name__ == "__main__":
    main()
