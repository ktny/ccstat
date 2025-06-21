"""Entry point for ccmonitor."""

import click

from .database import ProcessDatabase
from .display import display_history, display_processes_table, display_summary
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
def main(summary: bool, history: bool, no_save: bool) -> None:
    """Claude Code Monitor - Claude Codeのプロセス監視とリアルタイム可視化ツール."""
    try:
        db = ProcessDatabase()

        if history:
            # Display historical data
            display_history(db)
            return

        # Find current Claude processes
        processes = find_claude_processes()

        # Save to database unless --no-save is specified
        if not no_save:
            db.save_processes(processes)

        if summary:
            display_summary(processes, db)
        else:
            display_processes_table(processes)

    except KeyboardInterrupt:
        click.echo("\n👋 Monitoring stopped.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


if __name__ == "__main__":
    main()
