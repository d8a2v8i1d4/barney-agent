---
created: 2026-05-03
status: in-progress
source: pro-kit 03「外部工具整合包 by 雷小蒙」
---

# 外部工具整合計畫（2026-05-03）

> 這份計畫列出你所有打算接到 Claude Code 的工具。
> **執行方式**：有空的時候打開這份文件跟 AI 說：「幫我挑一個來裝」，AI 會用網路搜尋查當下最新的整合方式，一步一步帶你裝，完成後把對應的 checklist 打勾。

## 決策原則速查

1. 🥇 **CLI**（`gh`、`gws-cli`、官方 CLI）— 不吃 context、最穩定
2. 🥈 **REST API + `.env`**（curl / Python requests）— 彈性最高、可精準控制
3. 🥉 **MCP**（`~/.claude.json` 的 `mcpServers`）— 只有 CLI + API 都不行時才用
4. 🔒 **瀏覽器控制** — 真的沒 API 才走這條

---

## 工具清單

### 🟢 Google Calendar — 已整合（MCP）

- **用途**：查今日行程、昨日回顧，搭配 `/morning` 早晨日報使用
- **路線**：MCP（claude.ai Google Calendar）
- **狀態**：✅ 已完成，每天 `/morning` 指令使用中
- **備註**：MCP 連接穩定。未來如果需要「建立行程」可評估是否改用 `gws-cli calendar create`（CLI 路線更可控）

---

### 🟢 Notion — 已整合（MCP）

- **用途**：查詢個人行事曆 database（`collection://b54f20a6-3b82-4974-8d44-0af725ed4daf`）、搭配 `/morning` 使用
- **路線**：MCP（claude.ai Notion）
- **狀態**：✅ 已完成
- **備註**：MCP 只支援語義搜尋（不支援按 date 欄位 filter）。目前 `/morning` 用日期字串搜尋 + 年份過濾作為 workaround。如果未來需要精確 filter，改用 REST API（`curl api.notion.com`）

---

### 🟢 Firecrawl — 已整合（MCP），偶爾使用

- **用途**：抓取網頁內容，導入 `/ba-analysis` 做分析，或整理競品資料
- **路線**：MCP（claude.ai Firecrawl）
- **狀態**：✅ 已完成
- **備註**：偶爾使用，免費方案有月度 quota 限制。使用 `/ba-analysis` 分析某個網頁時直接呼叫即可

---

### 🟡 Google Drive / Sheets — 尚未整合

- **用途**：讀取 / 更新 Sheets 數據後導入分析、取得雲端文件內容
- **建議路線**：🥈 REST API（Google Drive API + Google Sheets API）或 🥇 CLI（`gws-cli`）
- **執行時要查的事情**：
  - [ ] `gws-cli` 是否支援 Google Drive + Sheets 操作？（查 GitHub README）
  - [ ] Google Sheets REST API 有沒有比 MCP 更穩的讀寫方式？
  - [ ] OAuth 或 Service Account 哪個更適合個人用途？
- **安裝 checklist**：
  - [ ] 取得必要憑證（Service Account JSON 或 OAuth token），存到 `.env`
  - [ ] 依 AI 查到的最新步驟安裝 CLI 或設定 REST API
  - [ ] 跑一個實際驗證指令（例如「幫我讀 [某個 Sheet] 的 A1:C10」）
  - [ ] 回來打勾 + 在備註欄記下踩坑
- **備註**：（執行完畢後填這裡）

---

## 進度總覽

- 🟡 尚未整合：1 個（Google Drive / Sheets）
- 🟢 已整合：3 個（Google Calendar、Notion、Firecrawl）
- 🔴 放棄：0 個

**下次執行建議**：開一個新 Claude Code 對話，說「幫我從 `100_Todo/integrations/2026-05-03-tool-integration-plan.md` 挑 Google Drive 來裝。請先用網路搜尋查最新整合方式再動手。」

---

## 給未來 AI 執行時的指引（不要刪這段）

當用戶打開這份文件跟你說「幫我挑 [某個工具] 來裝」時，請按以下步驟：

### 1. 確認範圍
用 `AskUserQuestion` 確認：要整合哪個工具，以及主要用途（從計畫文件的「用途」欄讀出來讓他確認）

### 2. 用網路搜尋查最新整合方式
**絕對不要跳過，也不要用訓練資料裡的舊資訊。** 執行：
1. 用 WebSearch / WebFetch 查：`"[工具名]" Claude Code integration 2026`、官方 CLI、REST API auth
2. 優先看官方文件、GitHub README、官方 blog
3. 把查到的結果整理後告訴用戶，讓他拍板

### 3. 執行安裝
- **CLI 路線**：安裝 CLI 工具，引導完成 auth，跑驗證指令
- **API 路線**：引導取得 key → 存到 `.env` → 在 `000_Agent/skills/` 建 skill（例如 `google-sheets-api/SKILL.md`）
- **MCP 路線**：編輯 `~/.claude.json` 加 entry → 完成 auth → 重載

### 4. 驗證 + 更新計畫文件
跑實際驗證指令 → 把該工具區塊從 🟡 改成 🟢 → checklist 打勾 → 填備註
