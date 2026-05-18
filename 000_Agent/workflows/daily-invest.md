# 每日投資決策日報

> 每天固定執行，或手動輸入 `/daily-invest` 觸發。
> 部位主檔持久化於 `000_Agent/memory/invest-portfolio.json`
> 歷史記錄持久化於 `000_Agent/memory/invest-history/`

---

## 🎯 任務本質

不是新聞剪報，是「**今天該不該加碼？哪一層加？加多少 USD？**」的決策儀表板。
資訊只是手段，**每日結論必須給出具體行動建議**。

---

## 💰 Barney 的部位狀態

### 待部署資金
- **總額**：USD $25,000（已換匯完成，可直接使用）
- **時程**：3-6 個月為基準，遇歷史機會可一次重倉
- **風險承受**：長期導向，短期 -10% 內可接受

### 三層配置目標
| 層 | 標的 | 目標占比 | 目標金額 | 單筆加碼建議 |
|---|------|---------|---------|------------|
| **核心** | VWRA.L、CNDX.L、IWMO.L | 55% | $13,750 | 月 DCA $2,300 或單筆 $1,500-2,000 |
| **衛星** | SMH、SOXX、AVGS.L | 30% | $7,500 | 訊號單筆 $500-1,500 |
| **進攻** | LQQ.PA | 15% | $3,750 | 雙訊號單筆 $1,000-1,500 |

### 部位追蹤檔案
- 主檔：`000_Agent/memory/invest-portfolio.json`
- 若檔案不存在 → 第一次執行時建立初始檔（deployed 全部 0）
- Barney 實際下單後，可手動編輯此檔，或在下次對話告知 Claude 更新

```json
{
  "total_capital": 25000,
  "deployed": 0,
  "remaining": 25000,
  "layers": {
    "core": {"target": 13750, "deployed": 0, "remaining": 13750, "trades": []},
    "satellite": {"target": 7500, "deployed": 0, "remaining": 7500, "trades": []},
    "aggressive": {"target": 3750, "deployed": 0, "remaining": 3750, "trades": []}
  },
  "start_date": "YYYY-MM-DD",
  "last_updated": "YYYY-MM-DD"
}
```

### 觀察清單
- **個股**：NVDA、TSM、MSFT、META、AMZN、2454
- **半導體 ETF**：SMH、SOXX、AVGS.L
- **廣基 ETF**：VWRA.L、CNDX.L、IWMO.L
- **槓桿 ETF**：00631L、LQQ.PA
- **巨集指標**：VIX、美債10Y、美債2Y、DXY、USD/TWD

---

## 📡 資料抓取策略（重要：禁止顯示 N/A）

> ⚠️ **黃金原則**：每個標的至少嘗試 3 種方式，全部失敗才可省略該行並標註「數據暫不可用」。**絕對不能顯示 N/A。**

### 美股標準流程（NVDA、TSM、MSFT、META、AMZN、SMH、SOXX）
1. WebSearch：`[TICKER] stock price today`
2. 若無結果 → WebSearch：`[TICKER] site:finance.yahoo.com`
3. 若有 Yahoo Finance URL → WebFetch 抓取

### LSE ETF 專用流程（AVGS.L、VWRA.L、CNDX.L、IWMO.L）
`.L` 結尾 = 倫敦交易所，Yahoo Finance 有但 WebFetch 常被擋，改用以下順序：

1. WebSearch：`[TICKER] price today LSE`（例：`AVGS.L price today LSE`）
2. WebSearch：`[ETF 全名] ETF price today`
   - AVGS.L → `Amundi S&P Global Semiconductors UCITS ETF price today`
   - VWRA.L → `Vanguard FTSE All-World UCITS ETF price today`
   - CNDX.L → `iShares NASDAQ 100 UCITS ETF price today`
   - IWMO.L → `iShares Edge MSCI World Momentum Factor UCITS ETF price today`
3. WebSearch：`[TICKER] Interactive Brokers`（IBKR 數據常出現在搜尋結果）
4. 若搜尋結果有 Yahoo Finance / Justetf / Bloomberg URL → WebFetch 抓取
5. 最後嘗試 WebSearch：`site:uk.finance.yahoo.com [TICKER]`

### Euronext ETF 專用流程（LQQ.PA）
`.PA` 結尾 = Euronext Paris：

1. WebSearch：`LQQ.PA price today`
2. WebSearch：`Lyxor Nasdaq-100 Daily 2x Leveraged UCITS ETF price today`
3. WebSearch：`LQQ.PA site:fr.finance.yahoo.com`
4. 若有 URL → WebFetch

### 台股流程（2454、00631L）
1. WebSearch：`[代號] 股價 今日`
2. WebSearch：`[代號] site:tw.finance.yahoo.com`

### 巨集指標流程
1. WebSearch：`VIX index today`、`US 10 year treasury yield today`、`DXY dollar index today`、`USD TWD exchange rate today`
2. 對搜尋結果中的財經網站 URL → WebFetch

---

## 🔄 執行步驟

### Step 0：載入歷史 + 部位 + 日期

```bash
date        # 確認台北時間 TODAY
date +%u    # 星期幾（1=週一，7=週日）
ls 000_Agent/memory/invest-history/*.json 2>/dev/null | sort -r | head -7
```

1. Read `000_Agent/memory/invest-history/` 最近 7 天 JSON → 建立 `previous_signals`
2. Read `000_Agent/memory/invest-portfolio.json` → 載入部位
   - 若不存在，建立初始檔並 Write 到該路徑（total_capital=25000，deployed=0，start_date=TODAY）
3. 計算 `deployment_progress = deployed / 25000`
4. 計算 `days_elapsed = TODAY - start_date`

---

### Step 1：巨集環境量化評分

依「資料抓取策略」取得：VIX、10Y、2Y、DXY、USD/TWD + 各自過去 1 年百分位。

**量化評分（基礎 50 分，上下調整）**：

| 指標 | 條件 | 加減分 |
|------|------|--------|
| VIX < 13 | 過度自滿 | -10 |
| VIX 13-18 | 正常 | +5 |
| VIX 18-25 | 警戒 | +10 |
| VIX 25-35 | 恐慌（買點區）| +20 |
| VIX > 35 | 極端恐慌（歷史機會）| +30 |
| 10Y 上升 > 0.1% | 壓抑估值 | -5 |
| 10Y 下降 > 0.1% | 利好估值 | +5 |
| 2Y/10Y 倒掛 | 衰退訊號 | -5 |
| DXY 走強 > 0.5% | 美元強壓力 | -3 |

---

### Step 2：個股 + ETF 訊號評分

對每個觀察標的，依「資料抓取策略」取得：當前價、今日漲跌、距 52W 高、RSI、本益比（個股）。

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

---

### Step 3：本週財報與大事件

WebSearch：`earnings calendar this week`、`FOMC CPI NFP schedule [YEAR]`

**規則**：觀察清單個股本週有財報 → 該股衛星加碼**暫停**

---

### Step 4：與昨日比較（去重複）

對比 `previous_signals`：
- 總分差距 < 5 且各指標變動 < 2% → 精簡版報告
- 跨越關鍵閾值 → 全量 + 標 `[訊號變化]`
- 連續 3 天無變動 → 開頭加 `📌 連續 N 天市場無明顯訊號變化，維持原計畫`

---

### Step 5：決策輸出（核心）

| 環境分數 | 環境判斷 | 核心層 | 衛星層 | 進攻層 |
|---------|---------|--------|--------|--------|
| 80-100 | 🟢 歷史機會 | DCA + 重倉 $3,000-5,000 | 積極加分數>60 標的 $1,000-1,500 | 可動 $1,000-1,500 |
| 65-79 | 🟢 訊號偏多 | DCA $2,300 + 加 $1,000 | 加分數>60 標的 $500-1,000 | 暫不動 |
| 50-64 | 🟡 中性偏多 | 維持月 DCA $2,300 | 觀望，只挑分數>70 加 $500 | 暫不動 |
| 35-49 | 🟡 中性 | 維持月 DCA $2,300 | 暫停加碼 | 暫不動 |
| 20-34 | 🟠 偏空 | DCA 減半 $1,150 | 暫停 | 暫不動 |
| 0-19 | 🔴 風險高 | 暫停 DCA | 暫停 | 暫不動 |

**部位進度調節**：
- `deployment_progress > days_elapsed / 180`：進度超前，建議金額**減半**
- `deployment_progress < (days_elapsed / 180) * 0.5`：進度落後，建議金額**追加 20%**
- `deployment_progress > 90%`：改為「最後 10% 留作機會性彈藥」

**每日報告必須回答**：
1. 今天該不該動？動哪一層？
2. 具體加碼多少 USD（絕對金額，不是 %）
3. 加碼哪一檔？為什麼？
4. 部署進度：已部署 X / $25,000 (Y%)，預計 Z 個月投完
5. 下一個觀察重點

---

### Step 6：歷史百分位定位

對 VIX、10Y、CNDX.L、SMH 報出：當前值 + 過去 1 年百分位
例：「VIX 18，過去 1 年第 35 百分位（偏低，市場偏樂觀）」

---

### Step 7：產出 HTML 報告

```html
<h2>📊 [TODAY] 投資決策日報</h2>

<!-- 1. 部位進度條 -->
<div style="background:#f0f7ff;padding:12px;border-left:4px solid #2196f3;">
  <h3>💼 部位進度</h3>
  <p><strong>已部署</strong>：USD $[deployed] / $25,000 ([progress]%)</p>
  <p><strong>剩餘彈藥</strong>：USD $[remaining]</p>
  <p><strong>三層分布</strong>：核心 $[core]/$13,750 | 衛星 $[sat]/$7,500 | 進攻 $[agg]/$3,750</p>
  <p><strong>時程</strong>：已過 [days] 天，理論進度 [theoretical]%，目前[超前/落後/同步]</p>
  <div style="background:#ddd;height:20px;border-radius:10px;">
    <div style="background:#2196f3;width:[progress]%;height:100%;border-radius:10px;"></div>
  </div>
</div>

<!-- 2. 今日建議（最重要）-->
<div style="background:#fff3cd;padding:12px;border-left:4px solid #ffc107;margin-top:10px;">
  <h3>💡 今日建議</h3>
  <p><strong>環境分數</strong>：[X] / 100（[環境判斷]）</p>
  <p><strong>核心層</strong>：[具體 USD 動作，例如「加碼 VWRA.L $1,500」]</p>
  <p><strong>衛星層</strong>：[具體 USD 動作 + 標的]</p>
  <p><strong>進攻層</strong>：[具體 USD 動作]</p>
  <p><strong>今日總建議部署</strong>：USD $[X]</p>
  <p><strong>下一個觀察點</strong>：[事件]</p>
</div>

<!-- 3. 巨集 -->
<h3>🌐 巨集環境</h3>
<table border="1" cellpadding="6" style="border-collapse:collapse;">
  <tr><th>指標</th><th>當前</th><th>變動</th><th>1Y 百分位</th><th>訊號</th></tr>
  <!-- 每列一個指標 -->
</table>

<!-- 4. 標的快檢（依分數排序）-->
<h3>📈 標的快檢</h3>
<table border="1" cellpadding="6" style="border-collapse:collapse;">
  <tr><th>標的</th><th>價格</th><th>今日</th><th>距52W高</th><th>RSI</th><th>分數</th><th>備註</th></tr>
  <!-- 所有標的，數據暫不可用者標明原因，不顯示 N/A -->
</table>

<!-- 5. 本週事件 -->
<h3>📅 本週關鍵事件</h3>
<ul>...</ul>

<!-- 6. 與昨日比較 -->
<h3>🔄 與昨日比較</h3>
<p>...</p>

<hr>
<p style="color:#888;font-size:12px;">
  以上為資訊整理與量化框架輸出，非投資建議。最終決策請自行判斷。<br>
  📝 實際下單後請手動更新 000_Agent/memory/invest-portfolio.json，或在下次對話告知 Claude 更新部位。
</p>
```

---

### Step 8：寫入歷史 & 更新主檔 & 寄信（⚠️ 無論任何情況都必須執行）

**8-1：確保目錄存在**

```bash
mkdir -p 000_Agent/memory/invest-history
```

**8-2：Write 今日歷史** 到 `000_Agent/memory/invest-history/[TODAY].json`：

```json
{
  "date": "YYYY-MM-DD",
  "total_score": 65,
  "vix": 18.5,
  "yield_10y": 4.2,
  "dxy": 104.5,
  "twd": 32.1,
  "stock_scores": {"NVDA": 55, "TSM": 70, "AVGS.L": 60, "VWRA.L": 55},
  "recommendation": "核心 VWRA.L $1,500 + 衛星 AVGS.L $800",
  "portfolio_progress": 0.12,
  "data_fetch_failures": ["CNDX.L RSI 無法取得"]
}
```

**8-3：不修改** `invest-portfolio.json`（只有 Barney 實際下單後才更新，避免自動累加錯誤）

**8-4：git commit 讓歷史持久化**

```bash
git add 000_Agent/memory/invest-history/[TODAY].json
git add 000_Agent/memory/invest-portfolio.json  # 若今天是初始建立
git commit -m "invest: [TODAY] 決策日報歷史記錄"
git push origin HEAD
```

**8-5：Write heartbeat** 到 `000_Agent/memory/invest-history/lastrun.txt`：

```
[TODAY] 執行完成，環境分數=[X]/100，建議部署=$[Y]，進度=[Z]%
```

**8-6：Gmail `create_draft`**：
- to: `d8a2v8i1d4@gmail.com`
- subject: `📊 [TODAY] 投資決策日報 — 環境分數 [X]/100｜建議部署 $[Y]｜進度 [Z]%`
- htmlBody: Step 7 的 HTML

若 Gmail 工具不可用 → Write 到 `000_Agent/memory/invest-history/[TODAY]-report.html`

---

## 🚫 紀律規則

1. **每日結論必須具體**：給 USD 金額，不能只說「考慮加碼」
2. **禁止顯示 N/A**：每個標的至少試 3 種抓取方式；全部失敗才標「數據暫不可用」並記入 `data_fetch_failures`
3. **不追高**：分數 < 50 時不主動建議衛星加碼
4. **不給賣出建議**：只給進場 / 加碼決策
5. **DCA 紀律**：核心月度 DCA 不受短期分數干擾（除非分數 < 20）
6. **進攻層門檻高**：LQQ.PA 只在分數 ≥ 80 + VIX > 25 才建議動
7. **去重複**：市場無變化時報告精簡
8. **避開財報前加碼**：個股本週有財報 → 該股暫停
9. **進度自校正**：超前減半、落後追加 20%
10. **部位檔案不自動修改**：routine 不會自動更新 portfolio.json

---

## 📝 部位更新機制

Barney 實際下單後，有兩種方式更新：

**方式 A：直接編輯**
```bash
# 範例：今天買了 VWRA.L $1,500
# 編輯 000_Agent/memory/invest-portfolio.json
# 把 core.deployed +1500，total.deployed +1500，last_updated 改今日
# 然後 git add + commit + push
```

**方式 B：跟 Claude 說**
在下次對話開頭說：「我今天買了 VWRA.L $1,500、AVGS.L $800」，Claude 會更新 portfolio.json 並 commit。
