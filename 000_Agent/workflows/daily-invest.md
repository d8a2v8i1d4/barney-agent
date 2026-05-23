# 每日投資決策日報工作流

> 每天台北時間早上 8:00 由 scheduled trigger 自動觸發，或手動輸入「跑今日決策日報」執行。
> 完整版：含環境評分、部位追蹤、Gmail 草稿、git 歷史存檔。

---

## 部位設定

- 總資金：USD $25,000
- 時程：3-6 個月
- 部位追蹤：`000_Agent/memory/invest-portfolio.json`
- 歷史記錄：`000_Agent/memory/invest-history/YYYY-MM-DD.json`

### 三層配置目標

| 層 | 標的 | 目標金額 | 單筆建議 |
|---|---|---|---|
| 核心 | VWRA.L、CNDX.L、IWMO.L | $13,750 | 月 DCA $2,300 或單筆 $1,500-2,000 |
| 衛星 | SMH、SOXX、AVGS.L | $7,500 | 訊號單筆 $500-1,500 |
| 進攻 | LQQ.PA | $3,750 | 雙訊號單筆 $1,000-1,500 |

---

## Step 0：載入部位與日期

1. `date` 確認台北時間 TODAY
2. `date +%u` 取得星期幾
3. 讀 `000_Agent/memory/invest-history/` 最近 7 天 → 建立 `previous_signals`
4. 讀 `000_Agent/memory/invest-portfolio.json` → 載入部位
   - 若不存在 → 建立初始檔
5. 計算 `deployment_progress = deployed / 25000`
6. 計算 `days_elapsed = TODAY - start_date`

---

## Step 1：巨集環境評分（基礎 50 分）

搜尋：VIX、美債 10Y、美債 2Y、DXY、USD/TWD

| 指標條件 | 加減分 |
|---|---|
| VIX < 13 | -10 |
| VIX 13-18 | +5 |
| VIX 18-25 | +10 |
| VIX 25-35 | +20 |
| VIX > 35 | +30 |
| 10Y 下降 > 0.1% | +5 |
| 10Y 上升 > 0.1% | -5 |
| 2Y/10Y 倒掛 | -5 |
| DXY 走強 > 0.5% | -3 |

---

## Step 2：個股 + ETF 訊號評分（每檔從 50 分起跳）

觀察清單：NVDA、TSM、MSFT、META、AMZN、2454 / SMH、SOXX、AVGS.L / VWRA.L、CNDX.L、IWMO.L / LQQ.PA / 00631L

| 條件 | 加減分 |
|---|---|
| 距 52W 高 < 5% | -5 |
| 距 52W 高 5-15% | 0 |
| 距 52W 高 15-25% | +10 |
| 距 52W 高 > 25% | +20 |
| RSI < 30 | +15 |
| RSI 30-50 | +5 |
| RSI 50-70 | 0 |
| RSI > 70 | -10 |

**資料抓取規則（禁止顯示 N/A）**：
- 美股：WebSearch `[TICKER] stock price today`
- LSE ETF（.L）：WebSearch ETF 全名 + `price today LSE`
- Euronext（.PA）：WebSearch `LQQ.PA price today`
- 台股：WebSearch `[代號] 股價 今日`
- 每個標的至少嘗試 3 種方式；全部失敗才標「數據暫不可用」

---

## Step 3：財報與大事件

WebSearch：`earnings calendar this week`、`FOMC CPI NFP schedule`

規則：觀察清單個股本週有財報 → 該股衛星加碼暫停

---

## Step 4：與前日比較

對比 `previous_signals`：
- 總分差 < 5 且各指標 < 2% → 精簡版報告
- 連續 3 天無變動 → 開頭加「📌 連續 N 天市場無明顯訊號變化」

---

## Step 5：決策輸出

| 環境分數 | 判斷 | 核心層 | 衛星層 | 進攻層 |
|---|---|---|---|---|
| 80-100 | 🟢 歷史機會 | DCA + 重倉 $3,000-5,000 | 分數>60 積極加 $1,000-1,500 | 可動 $1,000-1,500 |
| 65-79 | 🟢 訊號偏多 | DCA $2,300 + 加 $1,000 | 分數>60 加 $500-1,000 | 暫不動 |
| 50-64 | 🟡 中性偏多 | 維持月 DCA $2,300 | 只挑分數>70 加 $500 | 暫不動 |
| 35-49 | 🟡 中性 | 維持月 DCA $2,300 | 暫停 | 暫不動 |
| 20-34 | 🟠 偏空 | DCA 減半 $1,150 | 暫停 | 暫不動 |
| 0-19 | 🔴 風險高 | 暫停 | 暫停 | 暫不動 |

**部位進度自校正**：
- `deployment_progress > days_elapsed / 180`：超前 → 金額減半
- `deployment_progress < (days_elapsed / 180) * 0.5`：落後 → 金額 +20%

---

## Step 6：歷史百分位定位

對 VIX、10Y、CNDX.L、SMH 報出當前值 + 過去 1 年百分位

---

## Step 7：產出 HTML 報告

包含：
- 部位進度區塊（進度條）
- 今日建議區塊（具體 USD 金額）
- 巨集環境表格
- 標的快檢表（依分數排序）
- 本週關鍵事件
- 與前日比較

---

## Step 8：存檔 & 寄信（⚠️ 無論如何都必須執行）

1. `mkdir -p 000_Agent/memory/invest-history`
2. Write `000_Agent/memory/invest-history/YYYY-MM-DD.json`（含當日分數、價格、建議）
3. **不修改** `invest-portfolio.json`（只有 Barney 實際下單後才更新）
4. Git commit & push：`git add ... && git commit -m "invest: YYYY-MM-DD 決策日報" && git push origin HEAD`
5. Write heartbeat 到 `lastrun.txt`
6. Gmail `create_draft` 寄到 `d8a2v8i1d4@gmail.com`
   - Subject：`📊 YYYY-MM-DD 投資決策日報 — 環境分數 X/100｜建議部署 $Y｜進度 Z%`
   - 若 Gmail 不可用 → Write HTML 到 `YYYY-MM-DD-report.html`

---

## 紀律規則

1. 每日結論必須給具體 USD 金額
2. 禁止顯示 N/A
3. 不追高：分數 < 50 不主動建議衛星加碼
4. 不給賣出建議
5. DCA 紀律：核心月 DCA 不受短期分數干擾（除非分數 < 20）
6. LQQ.PA 只在分數 ≥ 80 + VIX > 25 才動
7. 個股本週有財報 → 該股暫停加碼
8. 部位檔案不自動修改

---

## 部位更新方式

下次對話開頭說：「我今天買了 VWRA.L $1,500、AVGS.L $800」
Claude 會更新 `invest-portfolio.json` 並 commit。
