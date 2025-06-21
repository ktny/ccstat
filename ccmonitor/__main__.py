"""Entry point for ccmonitor."""

import click

from .display import display_processes_table, display_summary
from .process import find_claude_processes


@click.command()
@click.option(
    "--summary",
    is_flag=True,
    help="サマリー表示のみ(リアルタイム監視をスキップ)",
)
def main(summary: bool) -> None:
    """Claude Code Monitor - Claude Codeのプロセス監視とリアルタイム可視化ツール."""
    try:
        # Find Claude processes
        processes = find_claude_processes()

        if summary:
            display_summary(processes)
        else:
            display_processes_table(processes)

    except KeyboardInterrupt:
        click.echo("\n👋 Monitoring stopped.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


if __name__ == "__main__":
    main()
