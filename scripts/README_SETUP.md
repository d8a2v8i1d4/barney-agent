# 每日投資決策日報 — 設定步驟

純 Python 腳本，每天台北早上自動跑、**直接寄信到收件匣**（用 gmail.compose 範圍的 send）。
**不靠 LLM，零成本、不會 N/A**。

> ⚠️ **務必把 OAuth 同意畫面設成「正式（Production / 已發布）」**，否則 testing 狀態的
> refresh token 約 7 天就過期，日報會默默寄不出去。詳見下方「常見問題」。
> 寄信失敗時 job 會以非 0 結束（GitHub 變紅燈並寄失敗通知到收件匣），不會再假裝成功。

---

## 一次性設定（約 15 分鐘）

### Step 1：建立 Google Cloud OAuth Client

1. 開啟 https://console.cloud.google.com/
2. 建立新專案（或用既有的），名稱例如 `barney-agent`
3. 左側選單 → 「API 和服務」→「程式庫」→ 搜尋 `Gmail API` → 啟用
4. 左側選單 → 「API 和服務」→「OAuth 同意畫面」
   - User Type：**外部**（External）
   - App name：`barney-agent`
   - 使用者支援電子郵件、開發者電子郵件都填你的 Gmail
   - **作用範圍（Scopes）**：跳過不用加
   - **測試使用者**：加上你的 Gmail（`d8a2v8i1d4@gmail.com`）
5. 左側選單 → 「API 和服務」→「憑證」→「建立憑證」→「OAuth 用戶端 ID」
   - 應用程式類型：**桌面應用程式**（Desktop app）
   - 名稱：`barney-agent-cli`
   - 點「建立」→ 下載 JSON
6. 把下載的 JSON 重新命名為 `client_secret.json`，放到 `scripts/` 目錄

### Step 2：本機跑一次 OAuth 拿 refresh token

```bash
cd ~/barney-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python3 scripts/setup_gmail_oauth.py
```

瀏覽器會跳出 Google 授權頁，登入並按「允許」。終端會印出三個值：

```
GMAIL_CLIENT_ID     = xxxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET = GOCSPX-xxxx
GMAIL_REFRESH_TOKEN = 1//0xxxxxxxxxxxxxxx
```

### Step 3：把三個值放進 GitHub Secrets

到 https://github.com/d8a2v8i1d4/barney-agent/settings/secrets/actions
點「New repository secret」三次，分別建立：

| Name | Value |
|---|---|
| `GMAIL_CLIENT_ID` | 上面的 client_id |
| `GMAIL_CLIENT_SECRET` | 上面的 client_secret |
| `GMAIL_REFRESH_TOKEN` | 上面的 refresh_token |

### Step 4：保護 client_secret.json

```bash
# 確保不會被 commit 進 repo
echo "scripts/client_secret.json" >> .gitignore
```

（這檔案已被預設 .gitignore 規則排除，但保險起見再加一行）

---

## 驗證

### 本機跑一次

```bash
source .venv/bin/activate
export GMAIL_CLIENT_ID=...
export GMAIL_CLIENT_SECRET=...
export GMAIL_REFRESH_TOKEN=...
python3 scripts/daily_invest_report.py
```

成功的話：
- `000_Agent/memory/invest-history/YYYY-MM-DD.json` 被建立
- `000_Agent/memory/invest-history/YYYY-MM-DD-report.html` 被建立
- 你的 Gmail **收件匣**會多一封日報（不是草稿匣）

### 在 GitHub Actions 手動觸發

到 https://github.com/d8a2v8i1d4/barney-agent/actions
左側選「每日投資決策日報」→ 右上「Run workflow」→ 跑一次看結果。

---

## 排程

預設 `cron: '0 0 * * *'`（UTC 0:00 = 台北 8:00），每天跑。

要改時間：編輯 `.github/workflows/daily-invest-report.yml` 的 cron 行。
（GitHub cron 有時會延後 5-30 分鐘觸發，這是 GitHub 的政策不是 bug。）

---

## 常見問題

**Q：跑出來顯示資料抓取失敗 N 個？**
A：yfinance 偶爾會被 Yahoo 限流。短期失敗很正常，連續 3 天才需要擔心。失敗清單會列在報告底部。

**Q：Gmail 沒寄出？**
A：檢查 Actions log 的 `[gmail fail]` 訊息。最常見是 refresh token 過期（Google 對 testing 狀態的 app 7 天過期）→ 把 OAuth 同意畫面從「測試」改成「發布」就不會過期。

**Q：怎麼把 OAuth 從「測試」改成「正式」？（治本，做一次就好）**
A：
1. 開 https://console.cloud.google.com/ → 選到 `My AI Assistant` 專案
2. 「API 和服務」→「OAuth 同意畫面」
3. 找到「Publishing status / 發布狀態」目前是 **Testing** → 按「**PUBLISH APP / 發布應用程式**」→ 確認
   （External + 只用 Gmail 範圍，通常不需 Google 驗證審核，發布後即生效）
4. 發布後**重跑一次** `python3 scripts/setup_gmail_oauth.py` 產生新的 `GMAIL_REFRESH_TOKEN`
5. 到 GitHub Secrets 更新 `GMAIL_REFRESH_TOKEN`（其他兩個沒變可不動）
6. 到 Actions 手動「Run workflow」驗證收件匣有收到信

改成正式後，refresh token 不再 7 天過期（除非閒置 6 個月或手動撤銷）。

**Q：報告寫到歷史檔，但分支不對？**
A：workflow 設計成寫到 `main` 分支（檢查 yml 的 git push 部分）。
