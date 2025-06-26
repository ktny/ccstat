# ccmonitor (Rust版)

Rust と ratatui で構築された Claude Code のリアルタイムプロセスモニター

## 特徴

- 🚀 Claude Code プロセスのリアルタイム監視
- 📊 CPU とメモリ使用量の追跡
- 📈 チャートによる履歴データの可視化
- 💾 DuckDB によるデータ永続化
- 🎨 ratatui を使用した美しいターミナル UI
- 📋 Claude のタスクシステムとの統合

## インストール

### 前提条件

- Rust 1.75 以降
- Claude Code がインストールされ、実行されていること

### ソースからビルド

```bash
# リポジトリをクローン
git clone https://github.com/ktny/ccmonitor
cd ccmonitor

# ビルドしてインストール
cargo build --release
cargo install --path .
```

## 使用方法

### リアルタイム監視

```bash
ccmonitor
```

### サマリー表示

```bash
ccmonitor --summary
```

### キーボードショートカット

- `Tab` / `Shift+Tab` - タブ間の切り替え
- `q` / `Esc` - アプリケーションの終了

## アーキテクチャ

### 主要コンポーネント

- **process.rs** - sysinfo を使用したプロセス監視
- **db.rs** - データ永続化のための DuckDB 統合
- **ui.rs** - ratatui を使用したターミナル UI
- **monitor.rs** - メイン監視ロジック
- **utils.rs** - ユーティリティ関数

### データストレージ

- データベース場所: `~/.ccmonitor/data.db`
- 7日より古いデータの自動クリーンアップ

## 開発

### 前提条件

```bash
# Rust をインストール
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### ビルドと実行

```bash
# 開発ビルド
cargo build

# 開発環境で実行
cargo run

# サマリーフラグ付きで実行
cargo run -- --summary
```

### テスト

```bash
# テストの実行
cargo test

# 出力付きでテストを実行
cargo test -- --nocapture
```

### コード品質

```bash
# コードフォーマット
cargo fmt

# リンターの実行
cargo clippy

# セキュリティ脆弱性のチェック
cargo audit
```

## 貢献

1. リポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feat/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feat/amazing-feature`)
5. プルリクエストを作成

## ライセンス

このプロジェクトは MIT ライセンスの下でライセンスされています - 詳細は LICENSE ファイルを参照してください。

## 謝辞

- ターミナル UI のための [ratatui](https://github.com/ratatui-org/ratatui) で構築
- プロセス監視のための [sysinfo](https://github.com/GuillaumeGomez/sysinfo) を使用
- [DuckDB](https://duckdb.org/) によるデータ永続化

## Python版との比較

この Rust 実装は、元の Python 版に対していくつかの利点を提供します：

- **パフォーマンス**: 大幅に高速な起動とより低いリソース使用量
- **ネイティブバイナリ**: ランタイム依存関係が不要
- **型安全性**: コンパイル時の保証とより良いエラーハンドリング
- **並行性**: Tokio によるより良い async/await サポート

## トラブルシューティング

### プロセスが検出されない

Claude Code が実行されていることを確認してください。モニターは名前またはコマンドラインに "claude" を含むプロセスを探します。

### データベースエラー

データベースエラーが発生した場合は、データベースファイルを削除してみてください：

```bash
rm ~/.ccmonitor/data.db
```

### UI レンダリングの問題

ターミナルが Unicode をサポートし、必要なシンボルを含むフォントがあることを確認してください。