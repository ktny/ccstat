"""Entry point for ccmonitor."""

import click


@click.command()
@click.option(
    "--summary",
    is_flag=True,
    help="サマリー表示のみ(リアルタイム監視をスキップ)",
)
def main(summary: bool) -> None:
    """Claude Code Monitor - Claude Codeのプロセス監視とリアルタイム可視化ツール."""
    if summary:
        click.echo("Summary mode: Not implemented yet")
    else:
        click.echo("Real-time monitoring: Not implemented yet")


if __name__ == "__main__":
    main()
