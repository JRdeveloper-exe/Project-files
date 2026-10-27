import pandas as pd
import yfinance as yf
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import datetime

# 💹 Forex watchlist
watchlist = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X",
    "USDCAD=X", "NZDUSD=X", "USDCHF=X", "EURCHF=X",
    "GBPJPY=X", "CHFJPY=X", "EURGBP=X", "GBPCHF=X"
]

def fetch_indicators(pair, interval):
    data = yf.download(tickers=pair, interval=interval, period="5d", progress=False)
    if data.empty or len(data["Close"]) < 26:
        return None

    # SMA
    data["SMA"] = data["Close"].rolling(window=5).mean()

    # RSI
    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = data["Close"].ewm(span=12, adjust=False).mean()
    exp2 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = exp1 - exp2
    data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["MACD_Hist"] = data["MACD"] - data["MACD_Signal"]

    # ATR
    data["High-Low"] = data["High"] - data["Low"]
    data["High-Close"] = abs(data["High"] - data["Close"].shift())
    data["Low-Close"] = abs(data["Low"] - data["Close"].shift())
    data["TrueRange"] = data[["High-Low", "High-Close", "Low-Close"]].max(axis=1)
    data["ATR"] = data["TrueRange"].rolling(window=14).mean()

    return data

def score_trade(pair):
    data_1h = fetch_indicators(pair, "1h")
    data_4h = fetch_indicators(pair, "4h")
    if data_1h is None or data_4h is None:
        return None

    latest_1h = data_1h.iloc[-1]
    latest_4h = data_4h.iloc[-1]

    price = float(latest_1h["Close"])
    sma = float(latest_1h["SMA"])
    atr = float(latest_1h["ATR"])
    rsi_1h = float(latest_1h["RSI"])
    macd_1h = float(latest_1h["MACD_Hist"])
    rsi_4h = float(latest_4h["RSI"])
    macd_4h = float(latest_4h["MACD_Hist"])

    if pd.isna(sma) or pd.isna(atr) or pd.isna(rsi_1h) or pd.isna(macd_1h):
        return None
    if atr < 0.05:
        return None

    direction = "Buy" if price > sma else "Sell"

    # Multi-timeframe confluence
    rsi_ok = rsi_1h > 55 and rsi_4h > 55 if direction == "Buy" else rsi_1h < 45 and rsi_4h < 45
    macd_ok = macd_1h > 0 and macd_4h > 0 if direction == "Buy" else macd_1h < 0 and macd_4h < 0
    confirmed = bool(rsi_ok) and bool(macd_ok)

    # Skip weak signals
    price_diff = abs(price - sma)
    macd_strength = abs(macd_1h)
    if price_diff < atr * 0.6 and macd_strength < 0.01:
        return None

    # Breakout logic with safety
    try:
        high_10 = data_1h["High"].rolling(10).max().iloc[-2]
        low_10 = data_1h["Low"].rolling(10).min().iloc[-2]
        breakout = bool(price > high_10) if direction == "Buy" else bool(price < low_10)
    except Exception:
        breakout = False

    # Scoring
    strength = price_diff + macd_strength + (1.5 if breakout else 0) + (2 if confirmed else 0)
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
        "RSI": f"{rsi_1h:.1f}/{rsi_4h:.1f}",
        "MACD": f"{macd_1h:.3f}/{macd_4h:.3f}",
        "Strength": strength
    }

def show_strong_trades():
    results = []
    for pair in watchlist:
        trade = score_trade(pair)
        if trade:
            results.append(trade)

    # Filter for strong trades only
    strong_trades = [t for t in results if t["Strength"] >= 2.5]

    if not strong_trades:
        result_label.config(text="⚠️ No high-confidence trades at the moment.")
        return

    strong_trades.sort(key=lambda x: x["Strength"], reverse=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    display = "🔥 *Elite Trade Setups Today*\n\n"
    for i, t in enumerate(strong_trades, 1):
        tag = "✅ Confirmed" if t["Confirmed"] else "⚠️ Weak"
        breakout_tag = "🚀 Breakout" if t["Breakout"] else "⛔ No Breakout"
        display += (
            f"{i}. {t['Pair']} — {t['Direction']} ({tag})\n"
            f"{breakout_tag}\n"
            f"📍 Entry: {t['Entry']}  |  SL: {t['SL']}  |  TP: {t['TP']}\n"
            f"📊 ATR: {t['ATR']} | RSI (1H/4H): {t['RSI']} | MACD: {t['MACD']}\n\n"
        )

    result_label.config(text=display + f"🕒 Updated: {timestamp}")

# 🎨 UI Setup
app = tb.Window(themename="minty")
app.title("📈 Elite Multi-Signal Scanner")
app.geometry("780x620")
app.resizable(False, False)

tb.Label(app, text="🔍 Finding High-Confidence Setups...", font=("Segoe UI", 15, "bold")).pack(pady=(20, 5))
result_label = tb.Label(app, text="", font=("Segoe UI", 12), justify="left", wraplength=700)
result_label.pack(pady=20)

show_strong_trades()
app.mainloop()