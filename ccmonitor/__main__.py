"""Entry point for ccmonitor."""

import click

from .timeline_monitor import TimelineMonitor


@click.command()
@click.option(
    "--hours",
    default=24,
    help="Number of hours to look back (default: 24)",
    type=int,
)
@click.option(
    "--directory",
    help="Filter by specific directory",
    type=str,
)
def main(hours: int, directory: str | None) -> None:
    """Claude Session Timeline - Claudeセッションの時系列可視化ツール."""
    try:
        # Note: directory filtering will be implemented later
        if directory:
            click.echo("Directory filtering is not yet implemented")
            
        monitor = TimelineMonitor(hours=hours)
        monitor.run()

    except KeyboardInterrupt:
        click.echo("\n👋 Exiting.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


if __name__ == "__main__":
    main()
