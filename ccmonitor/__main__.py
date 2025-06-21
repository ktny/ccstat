"""Entry point for ccmonitor."""

import click

from .database import ProcessDatabase
from .display import display_history, display_summary
from .monitor import RealTimeMonitor
from .process import find_claude_processes


@click.command()
@click.option(
    "--summary",
    is_flag=True,
    help="サマリー表示のみ(リアルタイム監視をスキップ)",
)
@click.option(
    "--history",
    is_flag=True,
    help="過去のプロセス情報を表示",
)
@click.option(
    "--interval",
    default=1.0,
    type=float,
    help="リアルタイム監視の更新間隔(秒)",
)
def main(summary: bool, history: bool, interval: float) -> None:
    """Claude Code Monitor - Claude Codeのプロセス監視とリアルタイム可視化ツール."""
    try:
        db = ProcessDatabase()

        if history:
            display_history(db)
            return

        if summary:
            processes = find_claude_processes()
            if processes:
                db.save_processes(processes)
            display_summary(processes, db)
        else:
            # Start real-time monitoring
            monitor = RealTimeMonitor(db=db, update_interval=interval)
            monitor.run()

    except KeyboardInterrupt:
        click.echo("\n👋 Monitoring stopped.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


if __name__ == "__main__":
    main()
