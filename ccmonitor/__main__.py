"""Entry point for ccmonitor."""

import click

from .timeline_monitor import TimelineMonitor


@click.command()
@click.option(
    "--days",
    default=1,
    help="Number of days to look back (default: 1)",
    type=int,
)
@click.option(
    "--directory",
    help="Filter by specific directory",
    type=str,
)
def main(days: int, directory: str | None) -> None:
    """Claude Session Timeline - Claudeセッションの時系列可視化ツール."""
    try:
        # Note: directory filtering will be implemented later
        if directory:
            click.echo("Directory filtering is not yet implemented")
            
        monitor = TimelineMonitor(days=days)
        monitor.run()

    except KeyboardInterrupt:
        click.echo("\n👋 Exiting.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


if __name__ == "__main__":
    main()
