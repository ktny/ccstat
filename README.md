# ccmonitor

Claude Session Timeline - Claudeセッションの時系列可視化ツール

## 概要

`ccmonitor`は、Claude Codeのセッション情報を時系列で可視化するCLIツールです。`~/.claude/projects/*.jsonl`ファイルから情報を読み取り、プロジェクト別のアクティビティを美しいターミナルUIで表示します。

## 特徴

- 📊 **時系列可視化**: プロジェクト別のアクティビティを密度ベースで表示
- 🎯 **高速**: Go製で高速なJSONLファイル処理
- 🎨 **美しいTUI**: Bubbletea + LipglossによるモダンなターミナルUI
- 📈 **統計情報**: プロジェクト数、イベント数、平均時間の表示
- 🔍 **フィルタリング**: プロジェクト名でのフィルタリング機能
- 🌳 **Git統合**: Git リポジトリとWorktree構造に対応
- ⚡ **単一バイナリ**: 依存関係なしで配布可能

## インストール

### バイナリリリース（推奨）
```bash
# GitHub Releasesから最新版をダウンロード
# TODO: リリース後にURLを更新
```

### ソースからビルド
```bash
# リポジトリをクローン
git clone https://github.com/ktny/ccmonitor.git
cd ccmonitor

# Go 1.23+ が必要
go build -o ccmonitor .
```

## 使用方法

### 基本的な使用方法

```bash
# 過去1日のセッションを表示
ccmonitor

# 過去7日のセッションを表示
ccmonitor --days 7

# 特定プロジェクトのみ表示
ccmonitor --project myproject

# スレッド表示（同一リポジトリの複数ディレクトリを分離）
ccmonitor --threads

# ヘルプ表示
ccmonitor --help
```

## アーキテクチャ

### Go版構造
```
ccmonitor/
├── cmd/
│   └── root.go          # Cobra CLI setup
├── internal/
│   ├── models/          # データ構造体
│   │   └── session.go   # SessionEvent, SessionTimeline
│   ├── reader/          # JSONLファイル読み取り
│   │   └── claude_logs.go
│   ├── git/             # Git統合
│   │   └── utils.go
│   ├── ui/              # Bubbletea UI
│   │   ├── app.go       # アプリケーション
│   │   ├── model.go     # メインモデル
│   │   ├── timeline.go  # タイムライン表示
│   │   └── styles.go    # Lipgloss スタイル
│   └── app/
│       └── monitor.go   # アプリケーションロジック
├── go.mod
├── go.sum
├── main.go             # エントリーポイント
└── README.md
```

### 技術スタック

- **Go 1.23+**: 高速で安全な並行処理
- **Bubbletea**: モダンなTUIフレームワーク
- **Lipgloss**: スタイリングライブラリ
- **Cobra**: CLIフレームワーク
- **標準ライブラリ**: JSON処理、ファイル操作、時間処理

### データフロー

1. `claude_logs.go` が`~/.claude/projects/*.jsonl`ファイルを解析
2. `git/utils.go` がGitリポジトリ情報を取得
3. `app/monitor.go` がデータをフィルタリング・グループ化
4. `ui/` パッケージがBubbletea + Lipglossで可視化

## 開発

### 開発環境のセットアップ

```bash
# Go 1.23+ をインストール
# https://golang.org/dl/

# 依存関係を取得
go mod tidy

# ビルド
go build -o ccmonitor .

# テスト実行
go test ./...

# リンター実行
golangci-lint run
```

### コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを開く

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。