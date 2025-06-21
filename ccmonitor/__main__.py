"""Entry point for ccmonitor."""

import click

from .database import ProcessDatabase
from .monitor import RealTimeMonitor


@click.command()
def main() -> None:
    """Claude Code Monitor - Claude Codeのプロセス監視とリアルタイム可視化ツール."""
    try:
        db = ProcessDatabase()
        monitor = RealTimeMonitor(db=db)
        monitor.run()

    except KeyboardInterrupt:
        click.echo("\n👋 Monitoring stopped.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


if __name__ == "__main__":
    main()
