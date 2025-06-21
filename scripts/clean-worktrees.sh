#!/bin/bash

# Worktreeクリーンアップスクリプト
# .worktree配下のworktreeをすべて削除する

set -e

echo "🧹 Worktreeクリーンアップを開始します..."

# .worktree配下のworktree一覧を取得
WORKTREES=$(git worktree list | awk '$1 ~ /\.worktree\// {print $1}')

if [ -z "$WORKTREES" ]; then
    echo "✅ クリーンアップするworktreeはありません"
    exit 0
fi

echo "📋 以下のworktreeをクリーンアップします:"
echo "$WORKTREES"
echo ""

# 確認プロンプト
read -p "続行しますか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ キャンセルしました"
    exit 1
fi

# 各worktreeを削除
echo "$WORKTREES" | while IFS= read -r worktree_path; do
    if [ -z "$worktree_path" ]; then
        continue
    fi
    
    echo "🗑️  削除中: $worktree_path"
    git worktree remove "$worktree_path" --force || {
        echo "  ⚠️  強制削除を試行中..."
        rm -rf "$worktree_path" 2>/dev/null || true
        git worktree prune
    }
    echo "  ✅ 完了"
done

# .worktreeディレクトリが空の場合は削除
if [ -d ".worktree" ] && [ -z "$(ls -A .worktree 2>/dev/null)" ]; then
    echo "📁 空の.worktreeディレクトリを削除しています..."
    rmdir .worktree
fi

# 最終確認
echo "🎉 クリーンアップが完了しました！"
echo ""
echo "現在のworktree一覧:"
git worktree list