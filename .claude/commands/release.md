# Release Process

このドキュメントは ccstat プロジェクトのリリースプロセスを説明します。

## 前提条件

- GitHub CLI (`gh`) がセットアップされていること
- npmjs.com への公開権限があること
- プロジェクトのメンテナーであること

## リリース手順

### 1. バージョン更新

```bash
# package.json の version フィールドを手動で更新
# 例: "version": "2.0.3"
```

### 2. 品質チェック

```bash
# リント、型チェック、テストを実行
npm run check

# ビルドを実行
npm run build

# 動作確認
node dist/index.js
```

### 3. 変更のコミット

```bash
# 変更をステージング
git add package.json

# コミット（バージョン番号を含む）
git commit -m "chore: bump version to v2.0.3"
```

### 4. Gitタグの作成とプッシュ

```bash
# タグを作成（semantic-release用のフォーマット）
git tag v2.0.3

# タグをリモートにプッシュ（自動リリースをトリガー）
git push origin v2.0.3

# 変更もプッシュ
git push origin main
```

## 自動化されるプロセス

以下は GitHub Actions で自動実行されます：

1. **リリースワークフロー** (`.github/workflows/release.yml`)
   - タグプッシュで自動トリガー
   - ビルド実行
   - npmjs.com への公開
   - GitHub Release の作成
   - CHANGELOG.md の更新

2. **Conventional Commits**
   - コミットメッセージから自動的にバージョニング
   - `feat:` → minor バージョンアップ
   - `fix:` → patch バージョンアップ
   - `BREAKING CHANGE:` → major バージョンアップ

## トラブルシューティング

### リリースが失敗した場合

1. GitHub Actions のログを確認
2. NPM_TOKEN が正しく設定されているか確認
3. package.json の設定を確認

### 手動でのnpm公開（緊急時）

```bash
# ビルド
npm run build

# 公開
npm publish
```

## 注意事項

- **必ず main ブランチから リリースする**
- **リリース前に必ず品質チェックを実行する**
- **タグは semantic versioning に従う（v1.2.3 形式）**
- **package.json のバージョンとタグバージョンを一致させる**

## リリース後の確認

1. npmjs.com でパッケージが公開されているか確認
   - https://www.npmjs.com/package/ccstat

2. GitHub Release が作成されているか確認
   - https://github.com/ktny/ccstat/releases

3. 実際にインストールして動作確認
   ```bash
   npm install -g ccstat@2.0.3
   ccstat --version
   ```
