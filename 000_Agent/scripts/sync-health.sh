#!/usr/bin/env bash
# sync-health.sh
# 驗證 Claude Code 跨裝置同步架構是否健康
# 由 pro-kit 07 生成 · by 雷蒙

set -e

echo "🩺 sync-health.sh 開始體檢..."
echo ""

FAIL=0

# 檢查 1：~/.claude/ 底下的 symlink 指向是否都存在
echo "[1/3] 檢查 ~/.claude/ symlink..."
for item in settings.json CLAUDE.md commands skills; do
  link="$HOME/.claude/$item"
  if [ -L "$link" ]; then
    target=$(readlink "$link")
    if [ -e "$target" ]; then
      echo "  ✅ $item → $target"
    else
      echo "  ❌ $item → $target（target 不存在）"
      FAIL=$((FAIL+1))
    fi
  elif [ -e "$link" ]; then
    echo "  ⚠️  $item 是一般檔案（可能是 iCloud 把 symlink 吃掉了）"
    FAIL=$((FAIL+1))
  fi
done

# 檢查 2：關鍵 skill 讀得到
echo ""
echo "[2/3] 檢查關鍵 skill 可讀取..."
TEST_SKILL="$HOME/.claude/skills/skill-creator/SKILL.md"
BA_SKILL="$HOME/.claude/skills/ba-analysis/SKILL.md"
if [ -f "$TEST_SKILL" ]; then
  echo "  ✅ skill-creator/SKILL.md 可讀取"
else
  echo "  ⚠️  skill-creator 讀不到（可能是 symlink 斷了）"
fi
if [ -f "$BA_SKILL" ]; then
  echo "  ✅ ba-analysis/SKILL.md 可讀取"
else
  echo "  ⚠️  ba-analysis 讀不到"
fi

# 檢查 3：MEMORY.md 可讀取
echo ""
echo "[3/3] 檢查記憶系統..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEMORY="$SCRIPT_DIR/../memory/MEMORY.md"
if [ -f "$MEMORY" ]; then
  echo "  ✅ MEMORY.md 可讀取（$(wc -l < "$MEMORY" | tr -d ' ') 行）"
else
  echo "  ❌ MEMORY.md 讀不到：$MEMORY"
  FAIL=$((FAIL+1))
fi

echo ""
if [ "$FAIL" = "0" ]; then
  echo "🎉 全部正常！你的 AI 分身活著。"
else
  echo "⚠️  發現 $FAIL 個問題，建議從 ~/claude-backup-* 檢查或重跑 pro-kit 07。"
  exit 1
fi
