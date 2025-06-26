# ccmonitor

Claude Session Timeline - Claudeセッションの時系列可視化ツール

## 概要

`ccmonitor`は、Claude Codeのセッション履歴を解析し、プロジェクト別の活動状況を時系列で可視化するCLIツールです。Claude Codeのログファイル（~/.claude/projects/）から情報を読み取り、プロジェクト毎の活動パターンやアクティブ時間を分析・表示します。

## 特徴

- 📊 **プロジェクト別活動表示**: 各プロジェクトの活動状況を時系列でビジュアル表示
- 🕒 **アクティブ時間計算**: メッセージ間隔に基づく実際の作業時間を自動計算
- 📈 **活動密度可視化**: 活動の密度に応じた色分け表示
- 🗂️ **プロジェクト統合**: Git repositoryによるプロジェクトの自動グルーピング
- 🧵 **スレッド表示**: 同一リポジトリ内の異なるディレクトリを階層表示
- 📅 **期間フィルタ**: 指定日数分の活動履歴を表示
- 🔍 **プロジェクトフィルタ**: 特定プロジェクトのみの表示

## インストール

### uvを使用した開発環境セットアップ（推奨）

```bash
# uvをインストール（初回のみ）
curl -LsSf https://astral.sh/uv/install.sh | sh

# リポジトリをクローン
git clone https://github.com/ktny/ccmonitor.git
cd ccmonitor

# 依存関係をインストール
uv sync

# 開発用インストール（エディタブルモード）
uv pip install -e .
```

### pipを使用した場合

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
# 過去1日の活動を表示（デフォルト）
ccmonitor

# 過去7日間の活動を表示
ccmonitor --days 7
ccmonitor -d 7

# 特定プロジェクトのみフィルタ表示
ccmonitor --project myproject
ccmonitor -p myproject

# スレッド表示（同一リポジトリの異なるディレクトリを分離表示）
ccmonitor --threads
ccmonitor -t

# 複数オプションの組み合わせ
ccmonitor --days 3 --project myproject --threads
ccmonitor -d 3 -p myproject -t

# ヘルプ表示
ccmonitor --help
ccmonitor -h
```

### 表示内容の説明

#### Project Activityテーブル
- **Project**: プロジェクト名（Git repository名またはディレクトリ名）
- **Timeline**: 時系列での活動状況（活動密度により色分け）
- **Events**: セッション内のメッセージ数
- **Duration**: アクティブな作業時間（分単位）

#### 活動密度の色分け
- ■ (明るい黒): 低活動
- ■ (緑系): 中程度の活動
- ■ (黄～オレンジ系): 高活動
- ■ (赤系): 非常に高い活動

#### 時間軸
- 1日表示: 時間単位（0, 6, 12, 18時）
- 複数日表示: 日付単位

### アクティブ時間の計算

メッセージ間の間隔が1分以内の場合のみアクティブ時間として計算されます。長時間の休憩は除外され、実際の作業時間のみが計測されます。

## 開発

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

# 開発環境でのccmonitor実行
uv run ccmonitor
uv run ccmonitor -d 7 -t
```

### アーキテクチャ

```
ccmonitor/
├── __main__.py          # エントリーポイント
├── timeline_monitor.py  # メイン監視・制御ロジック
├── claude_logs.py       # Claudeログファイル解析
├── timeline_ui.py       # リッチUI表示コンポーネント
├── git_utils.py         # Git repository情報取得
└── utils.py            # ユーティリティ関数
```

#### 主要コンポーネント
- **claude_logs.py**: `~/.claude/projects/`のJSONLファイルを解析し、セッション情報を抽出
- **timeline_ui.py**: Richライブラリを使用した美しいターミナル表示
- **git_utils.py**: ディレクトリのGit repository情報を取得してプロジェクトをグルーピング

### データソース

ccmonitorは以下のファイルからデータを読み取ります：
- `~/.claude/projects/*/**.jsonl`: Claude Codeのセッションログ
- 各JSONLファイルには、タイムスタンプ、セッションID、作業ディレクトリ、メッセージ内容などが記録

## 要件

- Python 3.12+
- Claude Code（ログファイル生成のため）
- Git（プロジェクト統合機能のため、推奨）

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。