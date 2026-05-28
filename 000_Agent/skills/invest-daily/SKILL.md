---
name: invest-daily
description: 每日投資決策日報。觸發時機：「發今天日報」「跑日報」「投資日報」「今天市場怎樣」「每日日報」「investment daily report」。執行完整的每日決策日報：抓取巨集數據 + 個股/ETF 價格 → 量化評分 → 產出 HTML → 建立 Gmail 草稿 → 寫入歷史 JSON → git commit。
---

# Invest Daily — 每日投資決策日報

Barney 的每日投資決策儀表板。核心問題：**今天該不該加碼？哪一層？加多少 USD？**

全程繁體中文輸出。

---

## Step 0：初始化

```bash
date   # 確認台北時間（UTC+8）
date +%u  # 取得星期幾
ls 000_Agent/memory/invest-history/*.json 2>/dev/null | sort -r | head -7
```

- Read `000_Agent/memory/invest-portfolio.json` → 載入部位
  - 若不存在 → 建立初始檔（deployed 全 0，start_date=TODAY）
- 計算 `deployment_progress = deployed / 25000`
- 計算 `days_elapsed = TODAY - start_date`
- 讀最近 7 天歷史 → 建立 `previous_signals`

---

## Step 1：抓取巨集數據

每個指標至少嘗試 2 種 WebSearch 查詢，有 URL 就 WebFetch 確認：

| 指標 | 搜尋關鍵字 |
|------|-----------|
| VIX | `VIX index today` |
| 美債 10Y | `US 10 year treasury yield today` |
| 美債 2Y | `US 2 year treasury yield today` |
| DXY | `DXY dollar index today` |
| USD/TWD | `USD TWD exchange rate today` |

---

## Step 2：抓取標的價格

**⚠️ 黃金原則：禁止顯示 N/A，每個標的至少嘗試 3 種方式。全部失敗才標「數據暫不可用」。**

### 觀察清單
- **個股**：NVDA、TSM、MSFT、META、AMZN、2454
- **半導體 ETF**：SMH、SOXX、AVGS.L
- **廣基 ETF**：VWRA.L、CNDX.L、IWMO.L
- **槓桿 ETF**：00631L、LQQ.PA

### 美股標準流程（NVDA、TSM、MSFT、META、AMZN、SMH、SOXX）
1. WebSearch：`[TICKER] stock price today`
2. WebSearch：`[TICKER] site:finance.yahoo.com`
3. WebFetch 任何找到的 Yahoo Finance URL

### LSE ETF 專用流程（AVGS.L、VWRA.L、CNDX.L、IWMO.L）
`.L` 結尾 = 倫敦交易所
1. WebSearch：`[TICKER] price today LSE`
2. WebSearch ETF 全名：
   - AVGS.L → `Avantis Global Small Cap Value UCITS ETF price today`
   - VWRA.L → `Vanguard FTSE All-World UCITS ETF price today`
   - CNDX.L → `iShares NASDAQ 100 UCITS ETF price today`
   - IWMO.L → `iShares Edge MSCI World Momentum Factor UCITS ETF price today`
3. WebSearch：`site:uk.finance.yahoo.com [TICKER]`
4. 若有 URL → WebFetch

### Euronext ETF 專用流程（LQQ.PA）
1. WebSearch：`LQQ.PA price today`
2. WebSearch：`Lyxor Nasdaq-100 Daily 2x Leveraged UCITS ETF price today`
3. WebSearch：`LQQ.PA site:fr.finance.yahoo.com`

### 台股（2454、00631L）
1. WebSearch：`[代號] 股價 今日`
2. WebSearch：`[代號] site:tw.finance.yahoo.com`

---

## Step 3：本週財報與大事件

```
WebSearch: "earnings calendar this week"
WebSearch: "FOMC CPI NFP schedule [YEAR]"
```

**規則**：觀察清單個股本週有財報 → 該股衛星加碼**暫停**

---

## Step 4：計算環境分數（基礎 50 分）

### 巨集評分
| 指標 | 條件 | 加減分 |
|------|------|--------|
| VIX | < 13 過度自滿 | -10 |
| VIX | 13-18 正常 | +5 |
| VIX | 18-25 警戒 | +10 |
| VIX | 25-35 恐慌買點 | +20 |
| VIX | > 35 極端恐慌 | +30 |
| 10Y | 較昨日上升 > 0.1% | -5 |
| 10Y | 較昨日下降 > 0.1% | +5 |
| 2Y/10Y | 倒掛（2Y > 10Y） | -5 |
| DXY | 較昨日走強 > 0.5% | -3 |

### 個股/ETF 評分（每個標的單獨算）
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

## Step 5：與昨日比較（去重複）

對比 `previous_signals`（最近一天的歷史 JSON）：
- 總分差距 < 5 且各指標變動 < 2% → 精簡版報告
- 跨越關鍵閾值 → 全量 + 標 `[訊號變化]`
- 連續 3 天無變動 → 開頭加 `📌 連續 N 天市場無明顯訊號變化，維持原計畫`

---

## Step 6：決策建議

### 決策對照表
| 環境分數 | 環境判斷 | 核心層 | 衛星層 | 進攻層 |
|---------|---------|--------|--------|--------|
| 80-100 | 🟢 歷史機會 | DCA + 重倉 $3,000-5,000 | 積極加分數>60 標的 $1,000-1,500 | 可動 $1,000-1,500 |
| 65-79 | 🟢 訊號偏多 | DCA $2,300 + 加 $1,000 | 加分數>60 標的 $500-1,000 | 暫不動 |
| 50-64 | 🟡 中性偏多 | 維持月 DCA $2,300 | 觀望，只挑分數>70 加 $500 | 暫不動 |
| 35-49 | 🟡 中性 | 維持月 DCA $2,300 | 暫停 | 暫不動 |
| 20-34 | 🟠 偏空 | DCA 減半 $1,150 | 暫停 | 暫不動 |
| 0-19 | 🔴 風險高 | 暫停 | 暫停 | 暫不動 |

### 部位進度調節
```
deployment_progress = deployed / 25000
theoretical_progress = days_elapsed / 180

超前 (actual > theoretical): 建議金額減半
落後 (actual < theoretical * 0.5): 建議金額追加 20%
超過 90%: 改為「最後 10% 留作機會性彈藥」
```

**進攻層門檻**：LQQ.PA 只在分數 ≥ 80 **且** VIX > 25 才建議動。

### 每日報告必須回答
1. 今天該不該動？動哪一層？
2. 具體加碼多少 USD（絕對金額）
3. 加碼哪一檔？為什麼？
4. 部署進度：已部署 X / $25,000 (Y%)
5. 下一個觀察重點

---

## Step 7：產出 HTML 報告

```html
<h2>📊 [TODAY] 投資決策日報</h2>

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

<div style="background:#fff3cd;padding:12px;border-left:4px solid #ffc107;margin-top:10px;">
  <h3>💡 今日建議</h3>
  <p><strong>環境分數</strong>：[X] / 100（[環境判斷]）</p>
  <p><strong>核心層</strong>：[具體 USD 動作]</p>
  <p><strong>衛星層</strong>：[具體 USD 動作 + 標的]</p>
  <p><strong>進攻層</strong>：[具體 USD 動作]</p>
  <p><strong>今日總建議部署</strong>：USD $[X]</p>
  <p><strong>下一個觀察點</strong>：[事件]</p>
</div>

<h3>🌐 巨集環境</h3>
<table border="1" cellpadding="6" style="border-collapse:collapse;">
  <tr><th>指標</th><th>當前</th><th>較昨日</th><th>1Y 百分位</th><th>訊號</th></tr>
  <!-- VIX、10Y、2Y、DXY、USD/TWD 各一行 -->
</table>

<h3>📈 標的快檢（依分數排序）</h3>
<table border="1" cellpadding="6" style="border-collapse:collapse;">
  <tr><th>標的</th><th>價格</th><th>今日%</th><th>距52W高</th><th>RSI</th><th>分數</th><th>備註</th></tr>
  <!-- 數據暫不可用者標明原因，不顯示 N/A -->
</table>

<h3>📅 本週關鍵事件</h3>
<ul>...</ul>

<h3>🔄 與昨日比較</h3>
<p>昨日分數 [X]，今日 [Y]，變化 [±Z]。[說明主要變因]</p>

<hr>
<p style="color:#888;font-size:12px;">
  以上為資訊整理與量化框架輸出，非投資建議。最終決策請自行判斷。<br>
  📝 實際下單後請告知 Claude 更新 000_Agent/memory/invest-portfolio.json。
</p>
```

---

## Step 8：寫入歷史 & 寄信（⚠️ 無論任何情況都必須執行）

### 8-1 建立目錄
```bash
mkdir -p 000_Agent/memory/invest-history
```

### 8-2 Write 歷史 JSON
路徑：`000_Agent/memory/invest-history/[TODAY].json`
```json
{
  "date": "YYYY-MM-DD",
  "total_score": 65,
  "vix": 18.5,
  "yield_10y": 4.2,
  "yield_2y": 4.0,
  "dxy": 104.5,
  "twd": 32.1,
  "stock_scores": {
    "NVDA": 55, "TSM": 70, "MSFT": 50, "META": 50, "AMZN": 50,
    "SMH": 45, "SOXX": 45, "AVGS.L": 60, "VWRA.L": 55,
    "CNDX.L": 50, "IWMO.L": 50, "LQQ.PA": 35,
    "2454": 60, "00631L": 35
  },
  "recommendation": "核心 VWRA.L $1,500 + 衛星 AVGS.L $800",
  "portfolio_progress": 0.0948,
  "data_fetch_failures": []
}
```

### 8-3 不修改 invest-portfolio.json
只有 Barney 實際下單後才更新部位檔案。

### 8-4 Git commit
```bash
git add 000_Agent/memory/invest-history/[TODAY].json
git commit -m "invest: [TODAY] 決策日報"
git push -u origin HEAD
```

### 8-5 Write heartbeat
路徑：`000_Agent/memory/invest-history/lastrun.txt`
```
[TODAY] 執行完成，環境分數=[X]/100，建議部署=$[Y]，進度=[Z]%
```

### 8-6 Gmail 草稿
使用 `mcp__Gmail__create_draft`：
- **to**：`d8a2v8i1d4@gmail.com`
- **subject**：`📊 [TODAY] 投資決策日報 — 環境分數 [X]/100｜建議部署 $[Y]｜進度 [Z]%`
- **htmlBody**：Step 7 的完整 HTML

若 Gmail 工具不可用 → Write 到 `000_Agent/memory/invest-history/[TODAY]-report.html`

---

## 紀律規則

1. **每日結論必須具體**：給 USD 金額，不能只說「考慮加碼」
2. **禁止顯示 N/A**：全部失敗才標「數據暫不可用」並記入 `data_fetch_failures`
3. **不追高**：分數 < 50 時不建議衛星加碼
4. **不給賣出建議**：只給進場 / 加碼決策
5. **DCA 紀律**：核心月度 DCA 不受短期分數干擾（除非分數 < 20）
6. **進攻層門檻**：LQQ.PA 只在分數 ≥ 80 + VIX > 25 才建議
7. **去重複**：市場無變化時報告精簡
8. **避開財報前加碼**：個股本週有財報 → 該股暫停
9. **進度自校正**：超前減半、落後追加 20%
10. **部位檔案不自動修改**：routine 不更新 portfolio.json
