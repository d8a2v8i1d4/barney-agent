#!/usr/bin/env python3
"""每日投資決策日報

執行流程：
  1. 載入 portfolio.json 與最近歷史
  2. yfinance → Yahoo chart API → stooq/FRED 三段式抓巨集、ETF、個股資料
  3. 量化評分（巨集、標的、決策矩陣）+ 本週財報暫停規則
  4. 輸出 HTML、寫入歷史 JSON、lastrun.txt
  5. 建立 Gmail 草稿（環境變數有設才寄）

規格文件：000_Agent/workflows/daily-invest.md
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parent.parent
PORTFOLIO_FILE = REPO_ROOT / "000_Agent" / "memory" / "invest-portfolio.json"
HISTORY_DIR = REPO_ROOT / "000_Agent" / "memory" / "invest-history"

ETF_LIST = [
    ("VWRA.L", "核心"),
    ("CNDX.L", "核心"),
    ("IWMO.L", "核心"),
    ("SMH", "衛星"),
    ("SOXX", "衛星"),
    ("AVGS.L", "衛星"),
    ("LQQ.PA", "進攻"),
]

# 觀察清單（不屬於三層配置，只列分數供參考）
WATCH_LIST = [
    ("NVDA", "個股"),
    ("TSM", "個股"),
    ("MSFT", "個股"),
    ("META", "個股"),
    ("AMZN", "個股"),
    ("2454.TW", "個股"),
    ("00631L.TW", "槓桿觀察"),
]

# 本週有財報 → 該股暫停加碼（只查美股，台股財報季另計）
EARNINGS_CHECK = ["NVDA", "TSM", "MSFT", "META", "AMZN"]

TZ = ZoneInfo("Asia/Taipei")

UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


# ============= 資料抓取 =============

def clean(val):
    """NaN / inf / 非數字 → None。LSE/Euronext 最新一列常是 NaN，混進計算會把分數算錯。"""
    if val is None:
        return None
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    if np.isnan(f) or np.isinf(f):
        return None
    return f


def fetch_yf(ticker, period="1y"):
    try:
        hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        if hist.empty:
            return None, None
        close = hist["Close"].dropna()
        if close.empty:
            return None, None
        return float(close.iloc[-1]), close
    except Exception as e:
        print(f"[yf fail] {ticker}: {e}", file=sys.stderr)
        return None, None


def fetch_chart_api(ticker, range_="1y"):
    """Yahoo chart API 直連，回 (即時價, 前收, 收盤序列)。
    yfinance 的 history 對 LSE/Euronext 常延遲一天且帶 NaN，
    meta.regularMarketPrice 才是最新成交價。429 時退避重試一次。"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"range": range_, "interval": "1d"}
    for attempt in range(2):
        try:
            r = requests.get(url, params=params, headers=UA_HEADERS, timeout=15)
            if r.status_code == 429:
                time.sleep(5)
                continue
            if r.status_code != 200:
                return None, None, None
            res = r.json()["chart"]["result"][0]
            meta = res.get("meta", {})
            price = clean(meta.get("regularMarketPrice"))
            market_time = meta.get("regularMarketTime")  # unix ts，判斷即時價屬於哪一天
            series = None
            try:
                ts = res["timestamp"]
                closes = res["indicators"]["quote"][0]["close"]
                s = pd.Series(closes, index=pd.to_datetime(ts, unit="s")).dropna()
                if not s.empty:
                    series = s
            except (KeyError, IndexError, TypeError):
                pass
            return price, market_time, series
        except Exception as e:
            print(f"[chart api fail] {ticker}: {e}", file=sys.stderr)
            return None, None, None
    return None, None, None


def fetch_fred(series_id):
    """FRED 公開 CSV（免 API key），取最近一筆有效值。"""
    try:
        r = requests.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv",
            params={"id": series_id}, headers=UA_HEADERS, timeout=15,
        )
        if r.status_code != 200:
            return None
        for line in reversed(r.text.strip().split("\n")):
            parts = line.split(",")
            if len(parts) == 2:
                try:
                    return float(parts[1])
                except ValueError:
                    continue
        return None
    except Exception as e:
        print(f"[fred fail] {series_id}: {e}", file=sys.stderr)
        return None


def fetch_stooq(symbol):
    try:
        r = requests.get(
            f"https://stooq.com/q/d/l/?s={symbol}&i=d", timeout=15
        )
        if r.status_code != 200 or not r.text or "Brak danych" in r.text:
            return None
        lines = r.text.strip().split("\n")
        if len(lines) < 2:
            return None
        return float(lines[-1].split(",")[4])
    except Exception as e:
        print(f"[stooq fail] {symbol}: {e}", file=sys.stderr)
        return None


# ============= 技術指標 =============

def calc_rsi(series, period=14):
    if series is None or len(series) < period + 1:
        return None
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(alpha=1 / period, adjust=False).mean()
    ma_down = down.ewm(alpha=1 / period, adjust=False).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return None if pd.isna(val) else float(val)


def percentile_1y(current, series):
    if current is None or series is None:
        return None
    arr = series.dropna().values
    if len(arr) == 0:
        return None
    return float((arr <= current).sum() / len(arr) * 100)


def analyze_ticker(ticker, layer):
    """單一標的完整分析。抓取順序：yfinance history → Yahoo chart API。
    即時價以 chart API 的 regularMarketPrice 優先（LSE 收盤 yfinance 會延遲一天）。
    全部失敗回 None。"""
    price, series = fetch_yf(ticker)
    api_price, market_time, api_series = fetch_chart_api(ticker)
    if series is None:
        series = api_series
    if api_price is not None:
        price = api_price
    price = clean(price)
    if price is None and series is not None:
        price = clean(series.iloc[-1])
    if price is None:
        return None

    # 今日漲跌：判斷即時價屬於序列最後一天（前收 = 倒數第二筆）
    # 還是更新的一天（前收 = 最後一筆）
    change_pct = None
    if series is not None and len(series) >= 2:
        prev = float(series.iloc[-2])
        if market_time is not None:
            try:
                api_date = datetime.fromtimestamp(market_time, tz=ZoneInfo("UTC")).date()
                if api_date > series.index[-1].date():
                    prev = float(series.iloc[-1])
            except (TypeError, ValueError, OSError):
                pass
        if prev > 0:
            change_pct = (price / prev - 1) * 100

    dist_high_pct = None
    if series is not None and len(series) > 0:
        high_52w = clean(max(float(series.max()), price))
        if high_52w:
            dist_high_pct = (high_52w - price) / high_52w * 100

    rsi = clean(calc_rsi(series))
    pct_1y = percentile_1y(price, series)
    return {
        "ticker": ticker, "layer": layer, "price": price,
        "change_pct": clean(change_pct), "dist_high_pct": clean(dist_high_pct),
        "rsi": rsi, "pct_1y": pct_1y,
        "score": ticker_score(clean(dist_high_pct), rsi), "note": "",
    }


def upcoming_earnings(tickers, today, days_ahead=7):
    """查未來 N 天內有財報的標的，回 {ticker: date}。查不到就略過（不阻塞日報）。"""
    result = {}
    for t in tickers:
        try:
            cal = yf.Ticker(t).calendar
            dates = cal.get("Earnings Date") if isinstance(cal, dict) else None
            if not dates:
                continue
            for d in dates if isinstance(dates, (list, tuple)) else [dates]:
                d = d.date() if hasattr(d, "date") else d
                if today <= d <= today + timedelta(days=days_ahead):
                    result[t] = d
                    break
        except Exception as e:
            print(f"[earnings fail] {t}: {e}", file=sys.stderr)
    return result


# ============= 計分 =============

def macro_score(vix, y10_change_bps, inverted, dxy_change_pct):
    score = 50
    if vix is not None:
        if vix < 13:
            score -= 10
        elif vix < 18:
            score += 5
        elif vix < 25:
            score += 10
        elif vix < 35:
            score += 20
        else:
            score += 30
    if y10_change_bps is not None:
        if y10_change_bps > 10:
            score -= 5
        elif y10_change_bps < -10:
            score += 5
    if inverted:
        score -= 5
    if dxy_change_pct is not None and dxy_change_pct > 0.5:
        score -= 3
    return score


def ticker_score(dist_high_pct, rsi):
    score = 50
    if dist_high_pct is not None:
        if dist_high_pct < 5:
            score -= 5
        elif dist_high_pct < 15:
            score += 0
        elif dist_high_pct < 25:
            score += 10
        else:
            score += 20
    if rsi is not None:
        if rsi < 30:
            score += 15
        elif rsi < 50:
            score += 5
        elif rsi < 70:
            score += 0
        else:
            score -= 10
    return score


DECISION_MATRIX = [
    (80, 101, "🟢 歷史機會", "DCA + 重倉 $3,000-5,000", "積極加分數>60 標的 $1,000-1,500", "可動 $1,000-1,500"),
    (65, 80,  "🟢 訊號偏多", "DCA $2,300 + 加 $1,000",   "加分數>60 標的 $500-1,000",       "暫不動"),
    (50, 65,  "🟡 中性偏多", "維持月 DCA $2,300",        "觀望，只挑分數>70 加 $500",       "暫不動"),
    (35, 50,  "🟡 中性",     "維持月 DCA $2,300",        "暫停加碼",                       "暫不動"),
    (20, 35,  "🟠 偏空",     "DCA 減半 $1,150",          "暫停",                           "暫不動"),
    (0,  20,  "🔴 風險高",   "暫停 DCA",                 "暫停",                           "暫不動"),
]


def decide(env_score):
    s = max(0, min(env_score, 100))
    for lo, hi, label, core, sat, agg in DECISION_MATRIX:
        if lo <= s < hi:
            return label, core, sat, agg
    return DECISION_MATRIX[-1][2:]


# ============= HTML 模板 =============

def fmt(val, spec=".2f", fallback="—"):
    if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
        return fallback
    return format(val, spec)


def ticker_rows(results):
    rows = ""
    for r in results:
        rows += (
            f"<tr><td>{r['ticker']}</td><td>{r['layer']}</td>"
            f"<td>{fmt(r['price'])}</td>"
            f"<td>{fmt(r['change_pct'], '+.2f')}%</td>"
            f"<td>{fmt(r['dist_high_pct'], '.1f')}%</td>"
            f"<td>{fmt(r['rsi'], '.1f')}</td>"
            f"<td>{fmt(r['pct_1y'], '.0f')}</td>"
            f"<td><b>{r['score']}</b></td>"
            f"<td>{r['note']}</td></tr>"
        )
    return rows


def build_html(ctx):
    rows = ticker_rows(ctx["etf_results"])
    watch_rows = ticker_rows(ctx["watch_results"])

    if ctx["earnings_map"]:
        events_html = "".join(
            f"<li>📅 {d}：<b>{t}</b> 財報（本週暫停加碼）</li>"
            for t, d in sorted(ctx["earnings_map"].items(), key=lambda x: x[1])
        )
    else:
        events_html = "<li>觀察清單個股未來 7 天無財報</li>"
    events_html += "<li style='color:#888;'>FOMC / CPI 等宏觀數據日程請另行確認</li>"

    failures_html = (
        "".join(f"<li>{f}</li>" for f in ctx["failures"])
        if ctx["failures"]
        else "<li>無</li>"
    )

    return f"""<h2>📊 {ctx['today']} 投資決策日報</h2>

<div style="background:#f0f7ff;padding:12px;border-left:4px solid #2196f3;">
  <h3>💼 部位進度</h3>
  <p><strong>已部署</strong>：USD ${ctx['deployed']:,.2f} / ${ctx['total_capital']:,} ({ctx['actual_progress']*100:.1f}%)</p>
  <p><strong>剩餘彈藥</strong>：USD ${ctx['remaining']:,.2f}</p>
  <p><strong>三層分布</strong>：核心 ${ctx['core_deployed']:,.0f} / ${ctx['core_target']:,}｜衛星 ${ctx['sat_deployed']:,.0f} / ${ctx['sat_target']:,}｜進攻 ${ctx['agg_deployed']:,.0f} / ${ctx['agg_target']:,}</p>
  <p><strong>時程</strong>：已過 {ctx['days_elapsed']} 天，理論進度 {ctx['theoretical_progress']*100:.1f}%，{ctx['progress_note']}</p>
  <div style="background:#ddd;height:20px;border-radius:10px;overflow:hidden;">
    <div style="background:#2196f3;width:{ctx['actual_progress']*100:.1f}%;height:100%;"></div>
  </div>
</div>

<div style="background:#fff3cd;padding:12px;border-left:4px solid #ffc107;margin-top:10px;">
  <h3>💡 今日建議</h3>
  <p><strong>環境分數</strong>：{ctx['env_score']} / 100（{ctx['label']}）</p>
  <p><strong>核心層</strong>：{ctx['core_action']}</p>
  <p><strong>衛星層</strong>：{ctx['sat_action']}{ctx['sat_pick']}</p>
  <p><strong>進攻層</strong>：{ctx['agg_action']}</p>
</div>

<h3>🌐 巨集環境</h3>
<table border="1" cellpadding="6" style="border-collapse:collapse;">
  <tr style="background:#f5f5f5;"><th>指標</th><th>當前</th><th>1Y 百分位</th><th>備註</th></tr>
  <tr><td>VIX</td><td>{fmt(ctx['vix'])}</td><td>{fmt(ctx['vix_pct'], '.0f')}</td><td>{ctx['vix_note']}</td></tr>
  <tr><td>10Y 美債</td><td>{fmt(ctx['y10'])}%</td><td>{fmt(ctx['y10_pct'], '.0f')}</td><td>日變動 {fmt(ctx['y10_change_bps'], '+.1f')} bps</td></tr>
  <tr><td>2Y 美債</td><td>{fmt(ctx['y2'])}%</td><td>—</td><td>{'⚠️ 殖利率倒掛' if ctx['inverted'] else '未倒掛'}</td></tr>
  <tr><td>DXY</td><td>{fmt(ctx['dxy'])}</td><td>{fmt(ctx['dxy_pct'], '.0f')}</td><td>日變動 {fmt(ctx['dxy_change_pct'], '+.2f')}%</td></tr>
  <tr><td>USD/TWD</td><td>{fmt(ctx['twd'])}</td><td>—</td><td>—</td></tr>
</table>

<h3>📈 ETF 快檢（依分數排序）</h3>
<table border="1" cellpadding="6" style="border-collapse:collapse;">
  <tr style="background:#f5f5f5;">
    <th>標的</th><th>層</th><th>價格</th><th>今日</th><th>距 52W 高</th><th>RSI</th><th>1Y 百分位</th><th>分數</th><th>備註</th>
  </tr>
  {rows}
</table>

<h3>👀 個股觀察清單（依分數排序，不屬於三層配置）</h3>
<table border="1" cellpadding="6" style="border-collapse:collapse;">
  <tr style="background:#f5f5f5;">
    <th>標的</th><th>類別</th><th>價格</th><th>今日</th><th>距 52W 高</th><th>RSI</th><th>1Y 百分位</th><th>分數</th><th>備註</th>
  </tr>
  {watch_rows}
</table>

<h3>📅 本週關鍵事件</h3>
<ul>{events_html}</ul>

<h3>🔄 與昨日比較</h3>
<p>{ctx['signal_change'] or '無歷史資料可比較'}</p>

<h3>⚠️ 資料抓取失敗清單</h3>
<ul>{failures_html}</ul>

<hr>
<p style="color:#888;font-size:12px;">
  以上為資訊整理與量化框架輸出，非投資建議。最終決策請自行判斷。<br>
  📝 實際下單後請編輯 000_Agent/memory/invest-portfolio.json 並 commit。
</p>
"""


# ============= 主流程 =============

def main():
    today = datetime.now(TZ).date()
    today_str = today.strftime("%Y-%m-%d")
    print(f"[start] {today_str}")

    if not PORTFOLIO_FILE.exists():
        print(f"portfolio file missing: {PORTFOLIO_FILE}", file=sys.stderr)
        sys.exit(1)
    portfolio = json.loads(PORTFOLIO_FILE.read_text())

    start_date = datetime.strptime(portfolio["start_date"], "%Y-%m-%d").date()
    days_elapsed = (today - start_date).days
    theoretical_progress = min(days_elapsed / 180, 1.0) if days_elapsed > 0 else 0.0
    actual_progress = portfolio["deployed"] / portfolio["total_capital"]

    failures = []

    # ===== VIX =====
    vix, vix_series = fetch_yf("^VIX")
    if vix is None:
        failures.append("VIX")
    vix_pct = percentile_1y(vix, vix_series)
    if vix is None:
        vix_note = "資料抓取失敗"
    elif vix < 13:
        vix_note = "過度自滿"
    elif vix < 18:
        vix_note = "正常"
    elif vix < 25:
        vix_note = "⚠️ 警戒區（買點起點）"
    elif vix < 35:
        vix_note = "🔥 恐慌區（買點區）"
    else:
        vix_note = "🚨 極端恐慌（歷史機會）"

    # ===== 10Y 殖利率 =====
    y10, y10_series = fetch_yf("^TNX")
    if y10 is not None and y10 > 20:
        y10 = y10 / 10
        if y10_series is not None:
            y10_series = y10_series / 10
    y10_change_bps = None
    if y10_series is not None and len(y10_series) >= 2:
        y10_change_bps = float((y10_series.iloc[-1] - y10_series.iloc[-2]) * 100)
    y10_pct = percentile_1y(y10, y10_series)
    if y10 is None:
        failures.append("10Y yield")

    # ===== 2Y 殖利率（Yahoo 2YY=F 期貨 → stooq → FRED）=====
    y2, _, _ = fetch_chart_api("2YY=F", range_="5d")
    if y2 is None:
        y2 = fetch_stooq("2usy.b")
    if y2 is None:
        y2 = fetch_fred("DGS2")
    if y2 is None:
        failures.append("2Y yield")
    inverted = (y2 is not None and y10 is not None and y2 > y10)

    # ===== DXY =====
    dxy, dxy_series = fetch_yf("DX-Y.NYB")
    dxy_change_pct = None
    if dxy_series is not None and len(dxy_series) >= 2:
        dxy_change_pct = float((dxy_series.iloc[-1] / dxy_series.iloc[-2] - 1) * 100)
    dxy_pct = percentile_1y(dxy, dxy_series)
    if dxy is None:
        failures.append("DXY")

    # ===== USD/TWD =====
    twd, _ = fetch_yf("USDTWD=X", period="5d")
    if twd is None:
        twd = fetch_stooq("usdtwd")
    if twd is None:
        failures.append("USD/TWD")

    env_score = macro_score(vix, y10_change_bps, inverted, dxy_change_pct)

    # ===== ETF（三層配置標的）=====
    etf_results = []
    for ticker, layer in ETF_LIST:
        data = analyze_ticker(ticker, layer)
        if data is None:
            failures.append(f"{ticker} price")
            etf_results.append({
                "ticker": ticker, "layer": layer, "price": None,
                "change_pct": None, "dist_high_pct": None, "rsi": None,
                "pct_1y": None, "score": 0, "note": "數據暫不可用",
            })
        else:
            etf_results.append(data)
        time.sleep(0.5)

    # ===== 個股觀察清單 =====
    watch_results = []
    for ticker, layer in WATCH_LIST:
        data = analyze_ticker(ticker, layer)
        if data is None:
            failures.append(f"{ticker} price")
            watch_results.append({
                "ticker": ticker, "layer": layer, "price": None,
                "change_pct": None, "dist_high_pct": None, "rsi": None,
                "pct_1y": None, "score": 0, "note": "數據暫不可用",
            })
        else:
            watch_results.append(data)
        time.sleep(0.5)

    # ===== 本週財報 → 該股暫停加碼 =====
    earnings_map = upcoming_earnings(EARNINGS_CHECK, today)
    for r in watch_results:
        base = r["ticker"].split(".")[0]
        if base in earnings_map:
            r["note"] = (r["note"] + " " if r["note"] else "") + \
                f"⚠️ {earnings_map[base]} 財報，本週暫停加碼"

    # 排序：分數高的在前
    etf_results.sort(key=lambda r: -(r["score"] or 0))
    watch_results.sort(key=lambda r: -(r["score"] or 0))

    # ===== 決策 =====
    label, core_action, sat_action, agg_action = decide(env_score)

    # 部位進度調整
    if days_elapsed > 0 and actual_progress > theoretical_progress * 1.0 and theoretical_progress > 0:
        progress_note = "目前超前 → 建議金額減半"
    elif days_elapsed > 0 and theoretical_progress > 0 and actual_progress < theoretical_progress * 0.5:
        progress_note = "目前落後 → 建議金額追加 20%"
    else:
        progress_note = "目前同步"

    # 衛星具體標的
    sat_pick = ""
    sat_candidates = sorted(
        [r for r in etf_results if r["layer"] == "衛星"],
        key=lambda r: -(r["score"] or 0),
    )
    if "暫停" not in sat_action and sat_candidates:
        threshold = 70 if "70" in sat_action else 60
        best = sat_candidates[0]
        if best["score"] >= threshold:
            sat_pick = f"｜建議標的：{best['ticker']}（分數 {best['score']}）"

    # 進攻層門檻
    can_aggressive = (env_score >= 80 and vix is not None and vix > 25)
    if "可動" in agg_action and not can_aggressive:
        agg_action = "暫不動（未達雙條件：環境分≥80 + VIX>25）"

    # ===== 比對昨日 =====
    yest_files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    prev_data = None
    for f in yest_files:
        if today_str in f.name:
            continue
        try:
            prev_data = json.loads(f.read_text())
            break
        except Exception:
            continue
    signal_change = ""
    if prev_data and prev_data.get("total_score") is not None:
        prev_score = prev_data["total_score"]
        diff = env_score - prev_score
        if abs(diff) >= 5:
            signal_change = f"📌 環境分數：{prev_score} → {env_score}（{'+' if diff>0 else ''}{diff}），訊號變化"
        else:
            signal_change = f"環境分數：{prev_score} → {env_score}（{'+' if diff>=0 else ''}{diff}），與昨日類似"

    # ===== HTML =====
    layers = portfolio["layers"]
    ctx = {
        "today": today_str,
        "deployed": portfolio["deployed"],
        "total_capital": portfolio["total_capital"],
        "remaining": portfolio["remaining"],
        "core_deployed": layers["core"]["deployed"], "core_target": layers["core"]["target"],
        "sat_deployed": layers["satellite"]["deployed"], "sat_target": layers["satellite"]["target"],
        "agg_deployed": layers["aggressive"]["deployed"], "agg_target": layers["aggressive"]["target"],
        "days_elapsed": days_elapsed,
        "theoretical_progress": theoretical_progress,
        "actual_progress": actual_progress,
        "progress_note": progress_note,
        "env_score": env_score, "label": label,
        "core_action": core_action, "sat_action": sat_action,
        "sat_pick": sat_pick, "agg_action": agg_action,
        "vix": vix, "vix_pct": vix_pct, "vix_note": vix_note,
        "y10": y10, "y10_pct": y10_pct, "y10_change_bps": y10_change_bps,
        "y2": y2, "inverted": inverted,
        "dxy": dxy, "dxy_pct": dxy_pct, "dxy_change_pct": dxy_change_pct,
        "twd": twd,
        "etf_results": etf_results,
        "watch_results": watch_results,
        "earnings_map": earnings_map,
        "signal_change": signal_change,
        "failures": failures,
    }
    html = build_html(ctx)

    # ===== 寫檔 =====
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    history = {
        "date": today_str,
        "total_score": env_score,
        "vix": vix, "yield_10y": y10, "yield_2y": y2,
        "dxy": dxy, "usd_twd": twd,
        "etf_scores": {r["ticker"]: r["score"] for r in etf_results},
        "stock_scores": {r["ticker"]: r["score"] for r in watch_results},
        "upcoming_earnings": {t: str(d) for t, d in earnings_map.items()},
        "recommendation": f"{label}｜核心：{core_action}｜衛星：{sat_action}{sat_pick}｜進攻：{agg_action}",
        "portfolio_progress": actual_progress,
        "deployed_usd": portfolio["deployed"],
        "progress_note": progress_note,
        "signal_change": signal_change,
        "data_fetch_failures": failures,
    }
    (HISTORY_DIR / f"{today_str}.json").write_text(
        json.dumps(history, ensure_ascii=False, indent=2)
    )
    (HISTORY_DIR / f"{today_str}-report.html").write_text(html)
    (HISTORY_DIR / "lastrun.txt").write_text(
        f"{today_str} 執行完成，環境分數={env_score}/100，進度={actual_progress*100:.1f}%，失敗={len(failures)}\n"
    )

    # ===== 寄信 =====
    subject = f"📊 {today_str} 投資決策日報 — 環境分數 {env_score}/100｜{label}｜進度 {actual_progress*100:.1f}%"
    if all(k in os.environ for k in ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN")):
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from gmail_helper import create_draft
            draft_id = create_draft(
                to=os.environ.get("REPORT_RECIPIENT", "d8a2v8i1d4@gmail.com"),
                subject=subject,
                html_body=html,
            )
            print(f"[gmail] draft id={draft_id}")
        except Exception as e:
            print(f"[gmail fail] {e}", file=sys.stderr)
            traceback.print_exc()
            failures.append(f"Gmail draft 失敗：{e}")
    else:
        print("[gmail] 未設定 GMAIL_* 環境變數，跳過寄信")

    print(f"[done] env_score={env_score}, etf_count={len(etf_results)}, failures={len(failures)}")
    for f in failures:
        print(f"  - {f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
