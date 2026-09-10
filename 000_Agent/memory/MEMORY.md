<!-- AI 分身起始助手紀錄:START -->
<!-- AI 分身起始助手 by 雷小蒙 v1.0 · 2026-05-03 · by 雷蒙（Raymond Hou）· https://github.com/Raymondhou0917/claude-code-resources · CC BY-NC-SA 4.0 -->

# Barney 的 AI 分身記憶

> 這裡存我跟 AI 之間跨 session 的偏好、經驗、踩坑紀錄。
> AI 每次 session 開始會自動讀這個檔案。

---

## 用戶偏好

### 券商：IBKR 直接下單（2026-09-10）

不是複委託。手續費很低（15 筆交易總計約 US$27，佔成本 0.22%），
所以算損益落差時不要往手續費猜，先看匯率。

---

## Feedback（AI 學到的原則）

### 資料搜集要嚴謹，寧可少講也不要講錯（2026-09-10）

- **錯誤做法**：把搜尋引擎的摘要當事實引用。deal-hunter 曾據此寄出「IHG × Accor 互相 status match」，
  實際上唯一來源是內容農場 `travelarbitrage.net`，完全虛構。
- **正確做法**：任何要寫進產出的事實，先確認來源等級（官方 / 專業媒體 / 社群實測），
  單一來源不夠就標「未證實」或直接不寫。
- **原因**：Barney 的原話 —「提供虛假甚至錯誤的資訊 只是在浪費我的 token」。
  他要的是可以直接行動的情報，錯的情報比沒有情報更貴。

### 診斷要先查資料再下判斷（2026-09-10）

- **錯誤做法**：看到「損益偏高」就先猜手續費沒算，沒先問券商是哪一家。
- **正確做法**：先確認前提（券商、幣別、計價方式），再算。
- **原因**：猜錯會讓他跟著錯誤方向走一輪。

---

## 踩坑筆記

### 改了持倉但日報還是舊數字（2026-08-01）

投資日報跑在 GitHub Actions 上，**讀的是遠端 repo 的 `000_Agent/memory/invest-portfolio.json`**，不是本機那份。
2026-07-30 新增的四筆持倉（IWMO/VWRA/CNDX/SOXX）只 commit 在本機沒 push，遠端停在 6/27 版，
所以 7/31、8/1 的日報都用舊部位算（進度顯示 18.9%，正確應是 34.0%）。

**規則：改完 `invest-portfolio.json` 一定要 `git push origin main`，光 commit 沒用。**

合併時注意：Actions 每天自動 commit 日報歷史檔，本機容易「落後幾十筆」。
`git merge origin/main` 若在 `invest-history/` 撞衝突，一律採用遠端（Actions）版本，
本機手動跑出來的歷史檔丟掉，才能跟後續日期接得起來。持倉檔本身不會衝突。

---

### 日報損益的美元帳 vs 台幣帳（2026-09-10）

日報原本只算美元報酬，NT$ 損益是「美元損益 × 今日匯率」，
完全忽略成本是在不同匯率下換進去的 → 2026-09-09 那封信虛報近一倍（NT$+11,620，實際 +6,232）。

已改：每筆 trade 新增 `fx_rate`（成交日 USD/TWD）與 `fee` 欄位，
台幣成本用各筆成交日匯率累加，信裡美元帳與台幣帳分開列。
**新增交易時這兩個欄位要一起填**，缺 fx_rate 台幣帳會直接留白不計算。

另：非美元計價標的（進攻層 LQQ.PA 是歐元）現在會先換算成美元再算市值。

---

### 排程任務在遠端環境跑時，WebFetch 幾乎全被擋（2026-09-10）

flight-hunter（機票情報員）首次在 Claude Code 遠端容器執行，WebFetch 對 loyaltylobby、onemileatatime、
awardwallet、delta.com、aa.com、alaskaair.com 等 33 次請求全部回 EGRESS_BLOCKED，只有 WebSearch 能用。

**規則：遠端排程任務的事實核對，改用「多組 WebSearch 交叉比對 ≥ 2 個專業媒體」；
單一來源或推估數字一律在信裡標 [未證實] / [估]，不要假裝驗證過。**
歷史檔放 `000_Agent/memory/flight-hunter-history/YYYY-MM-DD.json`，指紋去重複邏輯同 invest-history。

---

## 環境速查表

| 項目             | 值                        |
| :--------------- | :------------------------ |
| AI 分身母資料夾  | `/Users/rollatothemoon/Downloads/Barney_agent/` |
| 建立日期         | `2026-05-03`            |
| Skills symlink   | ✅ `~/.claude/skills` → `000_Agent/skills/` |
| 記憶系統啟用     | ✅                        |

<!-- AI 分身起始助手紀錄:END -->
