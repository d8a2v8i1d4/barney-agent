# deal-hunter-daily：每日薅羊毛情報整理

> 每天固定執行，或手動輸入 `/deal-hunter-daily` 觸發。
> 歷史記錄持久化於 `000_Agent/memory/deal-hunter-history/`

---

## 📌 Barney 的個人狀態（篩選基準，請務必比對）

### 飯店會員等級

| 品牌 | 現有等級 | 最高等級 | 還能升？ |
|------|---------|---------|---------|
| Hilton Honors | Diamond | Diamond | ❌ 已頂，不報同品牌 match |
| IHG One Rewards | Gold Elite | Diamond Elite（最高）| ✅ Platinum Elite / Spire Elite / Diamond Elite 升等機會要報 |
| Best Western Rewards | Diamond | Diamond | ❌ 已頂，不報同品牌 match |
| Choice Privileges | Platinum | Platinum | ❌ 已頂，不報同品牌 match |
| Marriott Bonvoy | Gold Elite | Ambassador Elite（最高）| ✅ Platinum Elite / Titanium Elite / Ambassador 升等機會要報 |
| GHA Discovery | Titanium | Titanium | ❌ 已頂，不報同品牌 match |
| Ascott Star Rewards | Platinum | Platinum | ❌ 已頂，不報同品牌 match |
| Wyndham Rewards | Diamond | Diamond | ❌ 已頂，不報同品牌 match |

**過濾規則**：
- 「已頂」品牌 → 不報 status match / challenge（除非是用該品牌等級去 match **其他品牌**）
- IHG Gold、Marriott Gold → 若有升等到更高一級的活動，照報
- **反向有價值**：用 Barney 的飯店等級 match 其他品牌高卡，永遠報

### 郵輪會員
- MSC Voyagers Club **Diamond**（已最高），可用來 match 其他郵輪：NCL Latitudes、Royal Caribbean Crown & Anchor、Carnival VIFP、Celebrity Captain's Club、Princess Captain's Circle、Holland America Mariner、Virgin Voyages 等

### 航空會員（⭐ 重點關注，目前空白）

Barney 想拿任一三大聯盟高卡，只要有 match 機會就推：

- **Star Alliance Gold**：United Premier Gold、ANA Platinum、Avianca Gold、Turkish Elite、Aegean Gold、Singapore KrisFlyer Elite Gold、EVA Infinity Gold 等
- **Oneworld Sapphire**：AA AAdvantage Platinum、BA Executive Club Silver、Qatar Gold、Cathay Diamond Silver、JAL Sapphire、Finnair Silver、Iberia Plata 等
- **SkyTeam Elite Plus**：Delta Platinum Medallion、AF/KLM Flying Blue Gold、China Airlines Dynasty Emerald、Korean SKYPASS Morning Calm Premium、Virgin Atlantic Gold 等

可用籌碼（Barney 飯店等級常被接受）：Hilton Diamond、Wyndham Diamond、Marriott Gold、GHA Titanium

### 美國信用卡狀態
- 已有：Amex Hilton Honors（台灣轉卡，免年費，有美卡 SSN/ITIN 信用記錄）
- 已申請 **ITIN**
- 下一張目標：**Amex Green** 或 **Hilton Aspire**（用 ITIN 申請）
- 第三張以後才會開其他發卡行（Chase、Capital One、Citi、Bilt 等暫不考慮）
- ⚠️ 短期內只看 **Amex 家**的活動，其他家除非是歷史前 10% SUB 才報

### 點數庫存
- 目前空，台灣 Amex MR 累積中（等 Amex Green 過件後轉到美卡 MR）
- 主力：**Amex MR**，MR transfer bonus 是重點

### 長期關注（1 年以上，慢慢收情報）
- **NRA 開美國公司**：個人 NRA 開 LLC 最低成本、最容易合規方式
- **Fintech 商業銀行**：Mercury、SoFi、Relay、Bluevine、Novo，特別注意對 NRA 友善的
- **未來商業信用卡**：Amex Business、Capital One Spark、Chase Ink 等的歷史高峰 SUB
- **Rakuten / 返利**：高額 cashback 加碼、Amex Offers 大額活動

---

## 🔍 執行步驟

### 第一步：確認日期 & 載入歷史

```bash
date                    # 確認台北時間 TODAY
date +%u               # 取得星期幾（1=週一，7=週日）
ls 000_Agent/memory/deal-hunter-history/*.json 2>/dev/null | sort -r | head -7
```

Read 工具讀取最近 7 天的 JSON 檔，建立 `history_set`（活動指紋集合）。
若無歷史檔，以空集合開始。

---

### 第二步：搜尋（Search 先行策略）

> ⚠️ **執行原則**：先用 WebSearch 取得 URL，再對有價值的結果用 WebFetch 抓全文。
> 不要事先硬寫 WebFetch 目標 URL——許多網站對直接抓取回傳 403。
> 若 WebFetch 回傳 403 / 無內容，記錄失敗並繼續，不要重試。

**動態年份**：今年 `[YEAR]` + 明年 `[YEAR+1]`，例如 2026 年就搜 `2026 2027`。

---

**類別 A：航空 Status Match（⭐ 最高優先）**

搜尋：
- `airline status match challenge [YEAR] [YEAR+1]`
- `star alliance gold status match [YEAR]`
- `oneworld sapphire status match [YEAR]`
- `skyteam elite plus status match [YEAR]`
- `hotel elite status to airline miles match [YEAR]`
- `hilton diamond airline status match [YEAR]`
- `site:reddit.com/r/awardtravel status match [YEAR]`
- `site:reddit.com/r/churning status match airline [YEAR]`

對搜尋結果中出現的有價值 URL → WebFetch 抓全文。

---

**類別 B：飯店 Status Match（套用升等邏輯）**

搜尋：
- `hotel status match challenge [YEAR] [YEAR+1]`
- `IHG Spire Elite status match [YEAR]`（IHG 還能升）
- `Marriott Platinum Titanium status match challenge [YEAR]`（Marriott 還能升）
- `Hyatt Globalist status match [YEAR]`（新品牌，值得拿）
- `Accor Diamond status match [YEAR]`（新品牌）
- `site:reddit.com/r/marriott OR site:reddit.com/r/hilton status match upgrade [YEAR]`
- `site:flyertalk.com hotel status match [YEAR]`

過濾邏輯（見個人狀態表）：
- 「已頂」品牌的 match → 跳過
- IHG / Marriott 升等機會 → 照報
- 任何用 Barney 現有等級 match 新品牌的機會 → 照報

---

**類別 C：Amex 家活動（⭐ 主力）**

搜尋：
- `amex membership rewards transfer bonus [YEAR]`
- `amex green card elevated welcome offer [YEAR]`
- `amex hilton aspire increased SUB [YEAR]`
- `amex personal cards best welcome offer [YEAR]`
- `amex offers high value [YEAR]`
- `site:reddit.com/r/amex OR site:reddit.com/r/creditcards amex transfer bonus [YEAR]`
- `site:doctorofcredit.com amex [YEAR]`

---

**類別 D：商務艙特賣 / 好兌換**

搜尋：
- `business class sale award sweet spot [YEAR]`
- `mistake fare business class [YEAR]`
- `TPE taipei business class deal [YEAR]`
- `site:reddit.com/r/awardtravel business class redemption [YEAR]`
- `site:flyertalk.com mistake fare business class [YEAR]`

優先：TPE 出發、亞洲區域內、可台北轉機抵達。

---

**類別 E：中文站精選（Points Talent）**

搜尋：
- `site:pointstalent.com [YEAR] 信用卡 OR 里程 OR 飯店`

取得 URL → WebFetch 抓最新 2-3 篇全文（pointstalent.com 通常可正常抓取）。

---

**類別 F：長期目標情報**

平日：搜尋快速掃過，發現明顯重大消息才報。
週日（`date +%u` = 7）：深度搜尋。

搜尋：
- `NRA non-resident open US LLC [YEAR]`
- `Mercury SoFi business bank account foreign owner NRA [YEAR]`
- `amex business platinum historical high SUB [YEAR]`
- `rakuten cashback large bonus [YEAR]`
- `site:reddit.com/r/smallbusiness OR site:reddit.com/r/entrepreneur NRA LLC bank [YEAR]`

---

### 第三步：去重複過濾 ⚠️

對每個活動建立指紋：`fingerprint = 活動標題前 30 字 + "|" + 來源網域`

1. fingerprint 在 `history_set` → **跳過**
2. 與歷史高度相似（同一張卡 / 同一 match 方案 / 同一 transfer bonus 體系）→ **跳過**
3. **允許重報，標 [更新]**（條件需在內容說明「上次 vs 本次」差異）：
   - SUB 金額提高 ≥ 20%
   - 截止日延長 ≥ 1 個月
   - 門檻降低（最低消費下降、挑戰天數縮短）
   - 從「需邀請」變「公開申請」
4. **不算更新**（不重報）：
   - 換網址但內容一樣
   - 不同部落客寫同一活動
   - 單純截止日倒數提醒

---

### 第四步：個人化篩選

- 飯店 match → 套用第一步個人狀態表過濾
- 美卡 SUB → 短期只報 Amex 家；其他家需歷史前 10%（Chase Sapphire 100k+、Capital One Venture X 100k+）
- 航空 match → 任何能拿星盟金 / Oneworld 藍寶石 / 天合超精的機會都推
- 商務艙特賣 → 優先 TPE 出發 / 亞洲區域

---

### 第五步：CP 值量化評分

**✅ 強推**（符合 ≥ 2 項）：
- SUB 等值 ≥ $1000 USD，或里程 ≥ 75k
- 最低消費 ≤ $5000 / 3 個月（或無最低消費）
- 無年費或首年免年費
- Status match 直接給等級（不需 challenge）
- Transfer bonus ≥ 25%
- 命中 Barney 航空空白區（任何聯盟高卡 match）→ **自動 ✅ 強推**

**⚠️ 參考**：有價值但有明顯門檻（高最低消費、需挑戰入住數等）

**不報**：小加碼 5-10%、需要超常支出（30 天內刷 $20k）、連 ⚠️ 都不到的

---

### 第六步：判斷今日狀態 & 產出

#### 情況 A：今日有新活動 → 寄 Gmail 草稿

按截止急迫性排序：🚨 3 天內 → ⏰ 7 天內 → 📅 一般有效期 → ♾️ 不限期

HTML 格式：

```html
<h2>🗓️ [TODAY] 薅羊毛日報</h2>
<p style="color:#666;font-size:13px;">
  📊 今日新增 N 筆，已過濾 M 筆（重複）
</p>
<hr>

<h3>✈️ 航空 Status Match（重點區）</h3>
<p>
  🚨 <strong>[活動名稱]</strong><br>
  📋 <b>內容</b>：[一句話，標註聯盟、能拿什麼等級]<br>
  💎 <b>聯盟價值</b>：[命中 Barney 哪個空白]<br>
  ⏰ <b>截止</b>：[日期]<br>
  💰 <b>預估成本</b>：[年費/最低消費/挑戰要求]<br>
  ⏱️ <b>預估時間</b>：[申請 X 分鐘 + 達標 X 個月]<br>
  🎯 <b>評分</b>：✅ 強推<br>
  🔗 <a href="[URL]">查看詳情</a>
</p>

<h3>🏨 飯店 / 郵輪 Status Match</h3>
<!-- 同上格式，[更新] 標記如有 -->

<h3>💳 Amex 家活動</h3>

<h3>💺 商務艙特賣 / 好兌換</h3>

<h3>🇹🇼 中文站精選（Points Talent）</h3>

<h3>🏢 長期目標情報（NRA / 美國公司 / 商業卡 / Rakuten）</h3>
<!-- 只在平日掃到重大消息或週日深挖時出現 -->

<hr>
<p style="color:#888;font-size:12px;">
  🔧 本次執行：搜尋 X 類別，WebFetch 成功 Y 個 / 失敗（403）Z 個<br>
  以上為情報整理，非消費建議，請自行評估。<br>
  資料來源：Reddit (r/churning, r/awardtravel, r/amex)、FlyerTalk、Doctor of Credit、The Points Guy、One Mile at a Time、Points Talent、AwardWallet
</p>
```

用 Gmail `create_draft` 工具：
- to: `d8a2v8i1d4@gmail.com`
- subject: `🔥 [TODAY] 薅羊毛日報 — 今日 N 個新活動`（若有航空 match 或史詩級 SUB 加 hot tag）
- htmlBody: 上方 HTML

若 Gmail 工具不可用 → Write 到 `000_Agent/memory/deal-hunter-history/[TODAY]-report.html`

#### 情況 B：今日無新活動 → 不寄信

只在 terminal 輸出：`[TODAY] 無新活動，全部 X 筆皆為重複，跳過寄信。`

#### 週日加碼（`date +%u` = 7）

讀過去 7 天所有 history JSON，挑 ✅ 強推 做「本週 Top 5」，放在當日報告最上方：

```html
<h2 style="background:#fff3cd;padding:10px;">📅 本週 TOP 5 回顧</h2>
<ol>
  <li><strong>[活動名稱]</strong> — [一句話] — <a href="[URL]">連結</a></li>
  ...
</ol>
<hr>
```

若當日為情況 B 但是週日 → 只寄週報，主旨改為 `📅 [TODAY] 薅羊毛週報 — 本週精選回顧`

---

### 第七步：寫入今日歷史（⚠️ 無論情況 A/B 都必須執行）

情況 A：把所有通過篩選的活動寫入：

```bash
# 確保目錄存在
mkdir -p 000_Agent/memory/deal-hunter-history
```

Write 工具寫入 `000_Agent/memory/deal-hunter-history/[TODAY].json`：

```json
[
  {
    "fingerprint": "標題前30字|網域",
    "date": "YYYY-MM-DD",
    "title": "完整標題",
    "url": "...",
    "category": "airline_match | hotel_match | amex | biz_class | points_talent | long_term",
    "rating": "強推 | 參考"
  }
]
```

情況 B：寫入空陣列 `[]` 到 `000_Agent/memory/deal-hunter-history/[TODAY].json`（確保去重機制有日期記錄）

然後執行 git commit 讓歷史持久化：

```bash
cd /path/to/barney-agent  # 使用實際 repo 路徑
git add 000_Agent/memory/deal-hunter-history/[TODAY].json
git commit -m "deal-hunter: [TODAY] 歷史記錄"
git push origin claude/adjust-code-routines-1jVTZ
```

---

### 第八步：寫 heartbeat（⚠️ 無論情況 A/B 都必須執行）

```bash
echo "[TODAY] 執行完成，情況=[A 或 B]，新增 N 筆，過濾 M 筆" > 000_Agent/memory/deal-hunter-history/lastrun.txt
```

Write 工具同步更新 `000_Agent/memory/deal-hunter-history/lastrun.txt`（確保 git 能追蹤）。

---

## 🚫 執行紀律

1. **去重複最高優先** — 寧可不寄也不寄重複內容
2. **Search 先行** — 不硬寫 WebFetch 目標；從搜尋結果取 URL 再 fetch；403 就記錄跳過
3. **個人化過濾嚴格** — 已頂品牌 match、非 Amex 家非史詩級 SUB，直接丟
4. **第七、八步無條件執行** — 不被情況 A/B 的邏輯打斷，是每次 run 的收尾動作
5. 類別找不到內容就跳過，不要硬填
6. 中文撰寫，英文術語保留（Status Match、SUB、transfer bonus、mistake fare、NRA、LLC、ITIN 等）
7. 每個活動最多 7-8 行，掃讀友善
