"""Entry point for ccmonitor."""

import click

from .database import ProcessDatabase
from .display import display_history, display_processes_table, display_summary
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
    "--no-save",
    is_flag=True,
    help="データベースへの保存をスキップ",
)
@click.option(
    "--once",
    is_flag=True,
    help="一度だけ実行してリアルタイム監視をスキップ",
)
@click.option(
    "--interval",
    default=1.0,
    type=float,
    help="リアルタイム監視の更新間隔(秒)",
)
def main(
    summary: bool, history: bool, no_save: bool, once: bool, interval: float
) -> None:
    """Claude Code Monitor - Claude Codeのプロセス監視とリアルタイム可視化ツール."""
    try:
        db = None if no_save else ProcessDatabase()

        if history:
            # Display historical data
            if db is None:
                raise click.ClickException(
                    "--historyオプションは--no-saveと一緒に使用できません"
                )
            display_history(db)
            return

        if summary or once:
            # Find current Claude processes
            processes = find_claude_processes()

            # Save to database unless --no-save is specified
            if db and processes:
                db.save_processes(processes)

            if summary:
                display_summary(processes, db)
            else:
                display_processes_table(processes)
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
