# AI 大腦遷移手冊

> 這份文件由 pro-kit 07 生成，記錄 Barney 的 AI 分身架構。
> 未來換新電腦、換新 AI 時，照這份走就能一鍵接管。

## 當前架構

- **專案資料夾**：`~/Downloads/Barney_agent/`（計畫未來移到更永久的位置）
- **.claude/ 同步設定**：
  - `settings.json` → iCloud：`~/Library/Mobile Documents/com~apple~CloudDocs/Barney-Agent/.claude/settings.json`
  - `CLAUDE.md` → iCloud：`~/Library/Mobile Documents/com~apple~CloudDocs/Barney-Agent/.claude/CLAUDE.md`
  - `commands/` → iCloud：`~/Library/Mobile Documents/com~apple~CloudDocs/Barney-Agent/.claude/commands/`
  - `skills` → symlink 指向 `~/Downloads/Barney_agent/000_Agent/skills/`
- **GitHub repo**：https://github.com/d8a2v8i1d4/barney-agent.git（私有）
- **體檢腳本**：`000_Agent/scripts/sync-health.sh`
- **檢查頻率**：每週五複盤日手動跑

---

## 情境 1：換一台新 Mac

1. 在新 Mac 登入同一個 Apple ID，等 iCloud 同步完成
2. 從 GitHub clone 專案（如果你已設好 GitHub）：
   ```bash
   git clone git@github.com:[你的帳號]/barney-agent.git ~/Downloads/Barney_agent
   ```
   或手動複製資料夾
3. 建立 symlinks：
   ```bash
   ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Barney-Agent"
   for item in settings.json CLAUDE.md commands; do
     ln -sf "$ICLOUD/.claude/$item" "$HOME/.claude/$item"
   done
   ln -sf "$HOME/Downloads/Barney_agent/000_Agent/skills" "$HOME/.claude/skills"
   ```
4. 跑 `000_Agent/scripts/sync-health.sh` 驗證

---

## 情境 2：從 Windows 電腦存取

由於 iCloud 在 Windows 體驗不佳，**建議用 GitHub 做 Windows 同步**：

1. 在 Windows 安裝 Git，clone 專案：
   ```bash
   git clone git@github.com:[你的帳號]/barney-agent.git C:\Users\[你的帳號]\Barney-Agent
   ```
2. 手動複製或設定 `settings.json`、`CLAUDE.md`、`commands/` 到 Windows 的 `%USERPROFILE%\.claude\`
3. 每次 Mac 有更新時，在 Mac 執行 `git push`，Windows 執行 `git pull`

---

## 情境 3：換新 AI 大腦（Codex / Gemini CLI / 未來新產品）

你的 `000_Agent/` + `CLAUDE.md` 是 AI 無關的規則文件。要給新 AI 讀：

1. 確認新 AI 的規則檔命名慣例（Codex 讀 `AGENTS.md`、Cursor 讀 `.cursorrules`）
2. 多加一條 symlink：
   ```bash
   ln -s "~/Downloads/Barney_agent/CLAUDE.md" "~/Downloads/Barney_agent/AGENTS.md"
   ```
3. Skills / memory 的邏輯需要新 AI 支援同等機制才能復用

---

## 情境 4：備份還原

如果 07 跑出事，從備份還原：

```bash
rm -rf ~/.claude
mv ~/claude-backup-YYYYMMDD-HHMMSS ~/.claude
```

備份位置：`~/claude-backup-20260503-215909`

---

## 設定 GitHub（待辦）

```bash
cd ~/Downloads/Barney_agent
git remote add origin git@github.com:[你的帳號]/barney-agent.git
git push -u origin main
```

> ✅ 已完成，2026-05-04 推送。
