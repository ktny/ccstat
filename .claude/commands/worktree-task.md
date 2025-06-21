---
description: ".worktree配下にgit worktreeで新しいブランチを作成し、タスク完了後にPRまで作成"
allowed-tools: Bash(git worktree:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(gh pr:*)
---

# Worktree Task コマンド

指定されたタスクに基づいて以下を実行します：

1. `.worktree`ディレクトリ配下に新しいgit worktreeブランチを作成
2. タスクを実装
3. コミット、プッシュ、PR作成まで完了

## 現在のgit状態

!`git status`

## 実行ステップ

### 1. ブランチ名の生成
タスク説明から自動的にブランチ名を生成します（例: `feat/add-feature-1221-1430`）

### 2. Worktreeの作成
```bash
mkdir -p .worktree
git worktree add -b <branch-name> .worktree/<branch-name>
```

### 3. タスク実装の指示受け
具体的な実装指示を受けて、新しいworktreeディレクトリで作業を実行します。

### 4. PR作成
実装完了後、以下を実行：
- `git add .`
- `git commit -m "適切なコミットメッセージ"`
- `git push -u origin <branch-name>`
- `gh pr create --title "PRタイトル" --body "PR説明"`

## 注意事項

- GitHub CLIがセットアップされている必要があります
- リモートリポジトリへのプッシュ権限が必要です
- 実装完了後は自動的にPRが作成されます

## タスクの説明をお教えください

どのようなタスクを実装しますか？具体的な内容を教えてください。