# 每日投資早報工作流

> 每天早上 8:00 自動觸發，或手動輸入 `/daily-invest` 執行。
> 資料來源：`000_Agent/knowledge/watchlist.md`、`000_Agent/knowledge/portfolio.md`

---

## Step 0：讀取觀察清單與持倉

1. 讀取 `000_Agent/knowledge/watchlist.md`，取得今日要分析的個股、ETF 清單與巨集指標。
2. 讀取 `000_Agent/knowledge/portfolio.md`，載入各代號的持倉股數與平均成本。

---

## Step 1：巨集環境掃描（2 分鐘）

用 WebSearch 搜尋今日：
- `VIX index today`
- `US 10 year treasury yield today`
- `DXY dollar index today`
- `USD TWD exchange rate today`

輸出格式：
```
【巨集溫度計】
VIX：XX（[正常 / 警戒 / 恐慌]）
美債 10Y：X.XX%
DXY：XXX
USD/TWD：XX.X
整體氛圍：[樂觀 / 中性 / 謹慎] — 一句話說明原因
```

---

## Step 2：今日重要財報 & 事件

用 WebSearch 搜尋：`earnings calendar today [日期]` 和 `market events today [日期]`

列出：
- 今天公布財報的重要公司（若有觀察清單內的公司，標記 ⚡）
- 重要總經事件（Fed 會議、CPI、非農就業等）

---

## Step 3：個股快訊（每檔 30 秒）

對觀察清單中每一支個股，搜尋：`[代號] news today` 或 `[代號] stock news`

只回報有實質新聞的個股，沒有重要動態的標「無異動」。

格式：
```
【個股快訊】
● NVDA：[一句話說明今日重要動態，附來源]
● TSM：無異動
● MSFT：[...]
...
```

---

## Step 4：ETF 表現掃描

搜尋各 ETF 昨日收盤或今日最新價格：
- 標出漲跌幅最大的 1-2 檔
- 若槓桿 ETF（00631L、LQQ.PA）單日跌幅 > 3%，加 ⚠️ 警示

格式：
```
【ETF 表現】
● 00631L：[漲跌%]
● VWRA.L：[漲跌%]
● LQQ.PA：[漲跌%] ⚠️（若跌幅大）
...
最強：[代號]  最弱：[代號]
```

---

## Step 4.5：我的持倉損益（有持倉才執行）

從 `portfolio.md` 取出有持倉的代號，搭配 Step 4 抓到的最新價格計算：

- **浮動損益（每股）** = 最新價 - 平均成本
- **浮動損益（總）** = （最新價 - 平均成本）× 股數
- **報酬率** = 浮動損益（總）/ 總成本 × 100%

格式：
```
【我的持倉】
● IWMO.L：持 7 股｜成本 $110.00｜現價 $XXX｜損益 +$XX.XX（+X.X%）
● VWRA.L：持 6 股｜成本 $183.84｜現價 $XXX｜損益 +$XX.XX（+X.X%）
● CNDX.L：持 0.3 股｜成本 $1,654.80｜現價 $XXX｜損益 +$XX.XX（+X.X%）
整體持倉：總成本 $X,XXX｜市值 $X,XXX｜浮動損益 +$XX.XX（+X.X%）
```

注意：若當日找不到最新價，標註「價格待確認」，不要猜測數字。

---

## Step 5：今日產業脈動（選讀）

搜尋：`AI semiconductor news today`、`tech sector news today`

挑出 1-3 條對觀察清單最相關的產業新聞，每條一句話摘要。

---

## Step 6：輸出今日早報

整合以上，輸出完整早報。結尾固定加：

```
---
以上為資訊整理，非投資建議，請自行判斷風險。
今日早報產生時間：[時間戳記 Asia/Taipei]
```

---

## 儲存規則

完成後把今日早報存到：
`300_Journal/invest-reports/YYYY-MM-DD-daily-invest.md`

（若目錄不存在，先建立）
