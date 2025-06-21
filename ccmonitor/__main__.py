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
        click.echo("🔍 Summary mode: Claude Code process monitoring summary")
        click.echo("This is a dummy output for summary mode.")
    else:
        click.echo("📊 Real-time monitoring: Claude Code process monitor")
        click.echo("This is a dummy output for real-time monitoring mode.")
        click.echo("Press Ctrl+C to exit.")


if __name__ == "__main__":
    main()
