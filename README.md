# ccmonitor

Claude Code Monitor - Claude Codeのプロセス監視とリアルタイム可視化ツール

## 概要

`ccmonitor`は、Claude Codeの稼働状況をリアルタイムで監視・可視化するCLIツールです。複数のClaudeプロセスのCPU使用時間、メモリ使用量、稼働状況を一目で把握できます。

## 特徴

- 🔍 **リアルタイム監視**: Claude Codeプロセスの状況を1秒間隔で更新
- 📊 **可視化**: CPU使用率、メモリ使用量をグラフで表示
- 📈 **統計情報**: 1日の稼働時間、プロセス数の推移を表示
- 💾 **データ永続化**: DuckDBによる高速なデータ保存・集計
- 📝 **タスク情報**: ~/.claude.jsonから実行中のタスク内容を表示
- 🎨 **美しいCLI**: Richライブラリによる見やすい表示

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/ktny/ccmonitor.git
cd ccmonitor

# 依存関係をインストール
pip install -r requirements.txt

# または開発用インストール
pip install -e .
```

## 使用方法

### 基本的な使用方法

```bash
# リアルタイム監視開始
ccmonitor

# サマリー表示（一回のみ）
ccmonitor --summary

# ヘルプ表示
ccmonitor --help
```
