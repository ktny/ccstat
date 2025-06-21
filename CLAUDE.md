# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

ccmonitorは、Claude Codeのプロセス監視とリアルタイム可視化を行うPython製のCLIツールです。

### 主な機能
- Claude Codeプロセスのリアルタイム監視（CPU使用率、メモリ使用量）
- DuckDBによるデータ永続化と統計情報の管理
- Richライブラリを使用した美しいターミナルUI
- ~/.claude.jsonからのタスク情報読み取り

## 開発環境のセットアップ

```bash
# uvのインストール（初回のみ）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係のインストール
uv sync

# 開発用インストール（エディタブルモード）
uv pip install -e .
```

## コマンド一覧

### 実行コマンド
```bash
# 基本的な実行（リアルタイム監視）
ccmonitor

# サマリー表示のみ
ccmonitor --summary

# ヘルプ表示
ccmonitor --help
```

### 開発コマンド
```bash
# コードフォーマットとリント
uv run ruff check .       # リントチェック
uv run ruff check . --fix # 自動修正
uv run ruff format .      # コードフォーマット

# 型チェック
uv run pyright

# テスト実行
uv run pytest
uv run pytest -v  # 詳細表示
uv run pytest --cov=ccmonitor  # カバレッジ付き

# 単一のテストを実行
uv run pytest tests/test_monitor.py::test_specific_function

# 開発環境でのccmonitor実行
uv run ccmonitor
uv run ccmonitor --summary
```

## アーキテクチャ

### コア構造
```
ccmonitor/
├── __main__.py      # エントリーポイント
├── monitor.py       # メイン監視ロジック
├── db.py           # DuckDBデータベース管理
├── ui.py           # Rich UIコンポーネント
├── process.py      # プロセス情報取得
└── utils.py        # ユーティリティ関数
```

### 主要コンポーネント

#### Monitor クラス (monitor.py)
- Claude Codeプロセスの監視を管理する中心的なクラス
- `psutil`を使用してプロセス情報を取得
- 1秒間隔でデータを収集し、UIを更新

#### Database クラス (db.py)
- DuckDBを使用したデータ永続化
- プロセス情報の保存と統計クエリの実行
- データファイルは `~/.ccmonitor/data.db` に保存

#### UI クラス (ui.py)
- Richライブラリを使用したターミナルUI
- リアルタイムグラフ、統計情報、プロセステーブルの表示
- キーボード操作のハンドリング

### データフロー
1. `process.py` がpsutilを使用してClaude Codeプロセスを検出
2. `monitor.py` が定期的にプロセス情報を収集
3. `db.py` がDuckDBにデータを保存
4. `ui.py` がRichを使用してデータを可視化
5. `~/.claude.json` からタスク情報を読み取り表示

### 重要な依存関係
- **psutil**: プロセス情報の取得
- **DuckDB**: 高速なデータ永続化と集計
- **Rich**: 美しいターミナルUI
- **Click**: コマンドライン引数の処理

### 設定ファイル
- データベース: `~/.ccmonitor/data.db`
- Claudeタスク情報: `~/.claude.json`（読み取り専用）
