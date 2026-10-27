import pandas as pd
import yfinance as yf
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import datetime

# 📈 Forex Watchlist
watchlist = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X",
    "USDCAD=X", "NZDUSD=X", "USDCHF=X", "EURCHF=X",
    "GBPJPY=X", "CHFJPY=X", "EURGBP=X", "GBPCHF=X"
]

def fetch_indicators(pair, interval):
    data = yf.download(tickers=pair, interval=interval, period="5d", progress=False)
    if data.empty or len(data["Close"]) < 26:
        return None

    data["SMA"] = data["Close"].rolling(5).mean()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    exp1 = data["Close"].ewm(span=12, adjust=False).mean()
    exp2 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = exp1 - exp2
    data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["MACD_Hist"] = data["MACD"] - data["MACD_Signal"]

    data["High-Low"] = data["High"] - data["Low"]
    data["High-Close"] = abs(data["High"] - data["Close"].shift())
    data["Low-Close"] = abs(data["Low"] - data["Close"].shift())
    data["TrueRange"] = data[["High-Low", "High-Close", "Low-Close"]].max(axis=1)
    data["ATR"] = data["TrueRange"].rolling(14).mean()

    return data

def score_trade(pair):
    d1 = fetch_indicators(pair, "1h")
    d4 = fetch_indicators(pair, "4h")
    if d1 is None or d4 is None:
        return None

    l1, l4 = d1.iloc[-1], d4.iloc[-1]
    price = float(l1["Close"])
    sma = float(l1["SMA"])
    atr = float(l1["ATR"])
    rsi1 = float(l1["RSI"])
    macd1 = float(l1["MACD_Hist"])
    rsi4 = float(l4["RSI"])
    macd4 = float(l4["MACD_Hist"])

    if pd.isna(sma) or pd.isna(atr) or pd.isna(rsi1) or pd.isna(macd1):
        return None

    direction = "Buy" if price > sma else "Sell"

    rsi_ok = rsi1 > 55 and rsi4 > 55 if direction == "Buy" else rsi1 < 45 and rsi4 < 45
    macd_ok = macd1 > 0 and macd4 > 0 if direction == "Buy" else macd1 < 0 and macd4 < 0
    confirmed = bool(rsi_ok) and bool(macd_ok)

    try:
        high_10 = float(d1["High"].rolling(10).max().iloc[-2])
        low_10 = float(d1["Low"].rolling(10).min().iloc[-2])
        breakout = price > high_10 if direction == "Buy" else price < low_10
    except:
        breakout = False

    score = abs(price - sma) + abs(macd1) + (1.5 if breakout else 0) + (2 if confirmed else 0)

    entry = round(price, 3)
    sl = round(entry - atr, 3) if direction == "Buy" else round(entry + atr, 3)
    tp = round(entry + atr * 2, 3) if direction == "Buy" else round(entry - atr * 2, 3)

    return {
        "Pair": pair,
        "Direction": direction,
        "Confirmed": confirmed,
        "Breakout": breakout,
        "Entry": entry,
        "SL": sl,
        "TP": tp,
        "ATR": round(atr, 3),
        "RSI": f"{rsi1:.1f}/{rsi4:.1f}",
        "MACD": f"{macd1:.3f}/{macd4:.3f}",
        "Strength": score
    }

def format_trades(trades, tier, emoji):
    if not trades:
        return ""
    section = f"{emoji} *{tier} Confidence*\n"
    for i, t in enumerate(trades[:2], 1):
        tag = "✅ Confirmed" if t["Confirmed"] else "⚠️ Weak"
        breakout_tag = "🚀 Breakout" if t["Breakout"] else "⛔ No Breakout"
        section += (
            f"{i}. {t['Pair']} — {t['Direction']} ({tag})\n"
            f"{breakout_tag}\n"
            f"📍 Entry: {t['Entry']} | SL: {t['SL']} | TP: {t['TP']}\n"
            f"📊 ATR: {t['ATR']} | RSI: {t['RSI']} | MACD: {t['MACD']}\n\n"
        )
    return section

def run_scan():
    results = []
    for pair in watchlist:
        trade = score_trade(pair)
        if trade:
            results.append(trade)

    if not results:
        result_label.config(text="⚠️ No trade setups found.")
        return

    high = [t for t in results if t["Strength"] >= 2.5]
    medium = [t for t in results if 1.8 <= t["Strength"] < 2.5]
    low = [t for t in results if 1.2 <= t["Strength"] < 1.8]

    high.sort(key=lambda x: x["Strength"], reverse=True)
    medium.sort(key=lambda x: x["Strength"], reverse=True)
    low.sort(key=lambda x: x["Strength"], reverse=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    report = "📊 *Confidence-Ranked Trade Setups*\n\n"
    report += format_trades(high, "High", "🟢")
    report += format_trades(medium, "Medium", "🟡")
    report += format_trades(low, "Low", "🔴")
    report += f"🕒 Updated: {timestamp}"
    result_label.config(text=report)

# 🖼️ GUI Setup
app = tb.Window(themename="minty")
app.title("📈 One-Click Trade Scanner")
app.geometry("780x700")
app.resizable(False, False)

tb.Label(app, text="📊 Click to Scan Trades", font=("Segoe UI", 15, "bold")).pack(pady=(20, 10))
scan_button = tb.Button(app, text="🔍 Scan Trades", bootstyle=SUCCESS, command=run_scan)
scan_button.pack(pady=(5, 15))

result_label = tb.Label(app, text="", font=("Segoe UI", 12), justify="left", wraplength=700)
result_label.pack(pady=20)

app.mainloop()
