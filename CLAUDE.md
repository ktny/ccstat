# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

ccmonitorは、Claude Codeのセッション履歴を解析し、プロジェクト別の活動状況を時系列で可視化するCLIツールです。

### 主な機能
- Claude Codeのログファイル（~/.claude/projects/）から セッション情報を解析
- プロジェクト別の活動パターンを時系列で視覚化
- Input/Output tokenの使用量をプロジェクト別に集計・表示
- メッセージ間隔に基づくアクティブ時間の自動計算（1分間隔閾値）
- Git repositoryによるプロジェクトの自動統合・グルーピング

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
# 基本的な実行（過去1日）
ccmonitor

# 過去N日間の活動を表示
ccmonitor --days 7

# 特定プロジェクトのみフィルタ表示
ccmonitor --project myproject

# スレッド表示（同一リポジトリの異なるディレクトリを分離表示）
ccmonitor --threads

# 複数オプションの組み合わせ
ccmonitor --days 3 --project myproject --threads

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
uv run pytest                    # 全テスト実行
uv run pytest -v               # 詳細表示
uv run pytest --cov=ccmonitor  # カバレッジ付き

# 単一のテストファイルを実行
uv run pytest tests/test_claude_logs.py
uv run pytest tests/test_claude_logs.py::TestCalculateActiveDuration

# 開発環境でのccmonitor実行
uv run ccmonitor
uv run ccmonitor --days 7 --threads
```

## アーキテクチャ

### コア構造
```
ccmonitor/
├── __main__.py          # エントリーポイント
├── timeline_monitor.py  # メイン監視・制御ロジック
├── claude_logs.py       # Claudeログファイル解析
├── timeline_ui.py       # リッチUI表示コンポーネント
├── git_utils.py         # Git repository情報取得
└── utils.py            # ユーティリティ関数（削除済み）
```

### 主要コンポーネント

#### claude_logs.py - ログ解析エンジン
- Claude Codeのセッションログ（~/.claude/projects/**.jsonl）をパース
- `SessionEvent`: 個々のメッセージイベント（timestamp, tokens, content等）
- `SessionTimeline`: プロジェクト毎のセッション集約（total tokens, active duration等）
- `calculate_active_duration()`: 1分間隔閾値によるアクティブ時間計算
- `calculate_token_totals()`: input/output tokenの集計

#### timeline_ui.py - UI表示レイヤー
- Richライブラリを使用した美しいターミナル表示
- Project Activityテーブル: プロジェクト名、時系列視覚化、Events数、Input/Output tokens、Duration
- 活動密度による色分け表示（低活動→高活動で色の濃さが変化）
- 時間軸表示（1日表示時は時間単位、複数日時は日付単位）

#### timeline_monitor.py - 制御レイヤー
- CLIオプションの処理（--days, --project, --threads）
- ログ読み込み処理の制御とUI表示の管理
- プロジェクトフィルタリング機能

#### git_utils.py - プロジェクト統合
- ディレクトリのGit repository情報を取得
- 同一リポジトリ内の異なるディレクトリを統合してプロジェクトとしてグルーピング

### データフロー
1. `timeline_monitor.py` がCLIオプションを解析
2. `claude_logs.py` が~/.claude/projects/下のJSONLファイルを読み込み
3. セッションイベントをパースし、token情報と時刻情報を抽出
4. `git_utils.py` でプロジェクト統合・グルーピング処理
5. アクティブ時間とtoken集計を実行
6. `timeline_ui.py` でRichを使った視覚化と表示

### 重要な依存関係
- **Rich**: 美しいターミナルUI（テーブル、色分け、パネル）
- **Click**: コマンドライン引数の処理
- **pathlib/json**: ログファイルの読み込みと解析

### 設定とデータソース
- **入力データ**: `~/.claude/projects/*/*.jsonl` （Claude Codeセッションログ）
- **データ形式**: 各行がJSON形式のイベント（timestamp, sessionId, cwd, message, usage等）
- **token情報**: assistantメッセージの`usage`フィールドから`input_tokens`と`output_tokens`を抽出

### アクティブ時間計算ロジック
- メッセージ間の間隔が1分以内の場合のみアクティブ時間としてカウント
- 長時間の休憩（>1分）は除外し、実際の作業時間のみを計測
- 単一イベントの場合は最低5分として扱う

## 開発のポイント

### TDD (Test-Driven Development)
- 原則としてテスト駆動開発で進める
- 新機能追加時は、まずテストを作成してから実装
- 既存機能修正時も、関連テストを先に更新

### Token情報の取扱い
- cache_creation_input_tokensとcache_read_input_tokensは input_tokensに含めない
- assistantメッセージのみtoken情報を持つ（userメッセージは0）
- token表示は3桁区切り（1,000形式）、0の場合は「-」表示

### プロジェクト統合ロジック
- Git repositoryの検出により同一プロジェクトをグルーピング
- --threadsオプション時は同一リポジトリでもディレクトリ別に分離表示
- 親子関係の表示（└─で子プロジェクトを示す）

## カスタムコマンド

### `/project:worktree-task`
`.worktree`配下にgit worktreeで新しいブランチを作成し、タスク完了後にPRまで作成するカスタムスラッシュコマンドです。

#### 使用方法
1. `/project:worktree-task` を実行
2. タスクの説明を入力
3. 自動的に新しいworktreeブランチが作成される
4. 実装指示を与える
5. 完了後、自動的にコミット・プッシュ・PR作成まで実行される

#### 前提条件
- GitHub CLIがセットアップされていること
- リモートリポジトリへのプッシュ権限があること

#### ディレクトリ構造
```
.worktree/
├── feat-task-name-1221-1430/  # 各タスクのworktreeディレクトリ
└── .gitignore                 # .worktree/は.gitignoreに追加済み
```