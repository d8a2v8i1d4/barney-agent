# 投資決策日報 Skill

執行 Barney 每日投資決策日報，完整流程如下。

## 部位狀態

- 總資金：USD $25,000
- 部位檔案：`000_Agent/memory/invest-portfolio.json`
- 歷史檔目錄：`000_Agent/memory/invest-history/`

### 三層配置目標
| 層 | 標的 | 目標金額 | 單筆加碼建議 |
|---|------|---------|------------|
| 核心 | VWRA.L、CNDX.L、IWMO.L | $13,750 | 月 DCA $2,300 或單筆 $1,500-2,000 |
| 衛星 | SMH、SOXX、AVGS.L | $7,500 | 訊號單筆 $500-1,500 |
| 進攻 | LQQ.PA | $3,750 | 雙訊號單筆 $1,000-1,500 |

### 觀察清單
- 個股：NVDA、TSM、MSFT、META、AMZN、2454
- 半導體 ETF：SMH、SOXX、AVGS.L
- 廣基 ETF：VWRA.L、CNDX.L、IWMO.L
- 槓桿 ETF：00631L、LQQ.PA
- 巨集：VIX、美債10Y、美債2Y、DXY、USD/TWD

---

## 資料抓取策略（禁止顯示 N/A，每標的至少試 3 種）

### 美股（NVDA、TSM、MSFT、META、AMZN、SMH、SOXX）
1. WebSearch：`[TICKER] stock price today`
2. WebSearch：`[TICKER] site:finance.yahoo.com`
3. 若有 URL → WebFetch

### LSE ETF（AVGS.L、VWRA.L、CNDX.L、IWMO.L）
1. WebSearch：`[TICKER] price today LSE`
2. WebSearch 用全名（AVGS.L → `Avantis Global Small Cap Value UCITS ETF price today`）
3. WebSearch：`site:uk.finance.yahoo.com [TICKER]`

### Euronext（LQQ.PA）
1. WebSearch：`LQQ.PA price today`
2. WebSearch：`Lyxor Nasdaq-100 Daily 2x Leveraged UCITS ETF price today`
3. WebSearch：`LQQ.PA site:fr.finance.yahoo.com`

### 台股（2454、00631L）
1. WebSearch：`[代號] 股價 今日`
2. WebSearch：`[代號] site:tw.finance.yahoo.com`

### 巨集
WebSearch：`VIX index today`、`US 10 year treasury yield today`、`DXY dollar index today`、`USD TWD exchange rate today`

---

## 執行步驟

### Step 0：載入
1. Bash: `date` 確認台北時間 TODAY
2. Read `000_Agent/memory/invest-portfolio.json`（不存在則建立初始檔）
3. `ls 000_Agent/memory/invest-history/*.json 2>/dev/null | sort -r | head -7` 讀近 7 天歷史
4. 計算 `deployment_progress = deployed / 25000`
5. 計算 `days_elapsed = TODAY - start_date`

### Step 1：巨集評分（基礎 50 分）

| 指標 | 條件 | 加減分 |
|------|------|--------|
| VIX < 13 | 過度自滿 | -10 |
| VIX 13-18 | 正常 | +5 |
| VIX 18-25 | 警戒 | +10 |
| VIX 25-35 | 恐慌（買點）| +20 |
| VIX > 35 | 極端恐慌 | +30 |
| 10Y 上升 > 0.1% | 壓抑估值 | -5 |
| 10Y 下降 > 0.1% | 利好估值 | +5 |
| 2Y/10Y 倒掛 | 衰退訊號 | -5 |
| DXY 走強 > 0.5% | 美元強壓力 | -3 |

### Step 2：個股 / ETF 評分

| 條件 | 加減分 |
|------|--------|
| 距 52W 高 < 5% | -5 |
| 距 52W 高 5-15% | 0 |
| 距 52W 高 15-25% | +10 |
| 距 52W 高 > 25% | +20 |
| RSI < 30 | +15 |
| RSI 30-50 | +5 |
| RSI 50-70 | 0 |
| RSI > 70 | -10 |

### Step 3：財報 / 大事件
WebSearch：`earnings calendar this week`、`FOMC CPI NFP schedule`
觀察清單個股本週有財報 → 該股加碼**暫停**

### Step 4：與昨日比較
讀歷史檔比較；連續 3 天無變動 → 開頭加「📌 連續 N 天無明顯訊號變化」

### Step 5：決策輸出

| 環境分數 | 判斷 | 核心層 | 衛星層 | 進攻層 |
|---------|------|--------|--------|--------|
| 80-100 | 🟢 歷史機會 | DCA + 重倉 $3,000-5,000 | 積極加 $1,000-1,500 | 可動 $1,000-1,500 |
| 65-79 | 🟢 訊號偏多 | DCA $2,300 + 加 $1,000 | 加 $500-1,000 | 暫不動 |
| 50-64 | 🟡 中性偏多 | 維持月 DCA $2,300 | 只挑分數>70 加 $500 | 暫不動 |
| 35-49 | 🟡 中性 | 維持月 DCA $2,300 | 暫停 | 暫不動 |
| 20-34 | 🟠 偏空 | DCA 減半 $1,150 | 暫停 | 暫不動 |
| 0-19 | 🔴 風險高 | 暫停 DCA | 暫停 | 暫不動 |

**部位進度調節**：
- `deployment_progress > days_elapsed/180`：超前 → 建議金額減半
- `deployment_progress < (days_elapsed/180)*0.5`：落後 → 追加 20%

**進攻層門檻**：LQQ.PA 只在分數 ≥ 80 + VIX > 25 才建議

### Step 6：歷史百分位
對 VIX、10Y、CNDX.L、SMH 報出當前值 + 過去 1 年百分位

### Step 7：產出 HTML 報告
產出完整 HTML，包含：
- 部位進度區塊（含進度條）
- 今日建議區塊（環境分數、三層行動、今日總金額、下一觀察點）
- 巨集環境表格
- 標的快檢表（依分數排序，禁止顯示 N/A）
- 本週關鍵事件
- 與昨日比較
- 免責聲明

### Step 8：寫入歷史 & 發送（無論任何情況必須執行）

**8-1** `mkdir -p 000_Agent/memory/invest-history`

**8-2** Write 今日 JSON 到 `000_Agent/memory/invest-history/TODAY.json`

**8-3** 不修改 `invest-portfolio.json`

**8-4** Git commit（CI 環境：只 commit，不 push）：
```bash
git add 000_Agent/memory/invest-history/
git commit -m "invest: TODAY 決策日報"
```

**8-5** Write heartbeat 到 `000_Agent/memory/invest-history/lastrun.txt`

**8-6** 寫 HTML 到 `000_Agent/memory/invest-history/TODAY-report.html`（CI 環境替代 Gmail draft）

---

## 紀律規則
1. 每日結論必須給 USD 金額
2. 禁止顯示 N/A（全部失敗才標「數據暫不可用」）
3. 分數 < 50 不主動建議衛星加碼
4. 不給賣出建議
5. 進攻層：分數 ≥ 80 + VIX > 25 才動
6. 避開財報前加碼
7. 部位檔案不自動修改
