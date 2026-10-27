import websocket
import json
import pandas as pd
import datetime
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# 🎯 Assets from Deriv's market
watchlist = [
    "R_100", "R_75", "R_10",          # Volatility Indices
    "frxXAUUSD", "frxNAS100", "frxUS30"  # Metals & Indices
]

DERIV_URL = "wss://ws.derivws.com/websockets/v3"
DEBUG_MODE = False  # ⬅️ Toggle to True for raw signal visibility

def fetch_candles(symbol, granularity=3600, count=60):
    msg = {
        "candles": symbol,
        "subscribe": 0,
        "count": count,
        "granularity": granularity
    }

    df = pd.DataFrame()

    def on_message(ws, message):
        data = json.loads(message)
        if "candles" in data:
            candles = data["candles"]
            df_temp = pd.DataFrame(candles)
            df_temp["time"] = pd.to_datetime(df_temp["epoch"], unit="s")
            df_temp.set_index("time", inplace=True)
            df_temp.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace=True)
            df_temp = df_temp[["Open", "High", "Low", "Close"]]
            nonlocal df
            df = df_temp
            ws.close()

    ws = websocket.WebSocketApp(DERIV_URL, on_message=on_message)
    ws.on_open = lambda ws: ws.send(json.dumps(msg))
    ws.run_forever()
    return df

def calculate_indicators(df):
    df["SMA"] = df["Close"].rolling(5).mean()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    exp1 = df["Close"].ewm(span=12, adjust=False).mean()
    exp2 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
    df["HL"] = df["High"] - df["Low"]
    df["HC"] = abs(df["High"] - df["Close"].shift())
    df["LC"] = abs(df["Low"] - df["Close"].shift())
    df["TR"] = df[["HL", "HC", "LC"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(14).mean()
    return df

def score_trade(symbol):
    try:
        df1 = calculate_indicators(fetch_candles(symbol, 3600, 60))
        df4 = calculate_indicators(fetch_candles(symbol, 14400, 60))
        l1, l4 = df1.iloc[-1], df4.iloc[-1]
        price, sma, atr = l1["Close"], l1["SMA"], l1["ATR"]
        rsi1, macd1 = l1["RSI"], l1["MACD_Hist"]
        rsi4, macd4 = l4["RSI"], l4["MACD_Hist"]

        if pd.isna(sma) or pd.isna(atr) or pd.isna(rsi1) or pd.isna(macd1):
            return None

        direction = "Buy" if price > sma else "Sell"
        rsi_ok = rsi1 > 55 and rsi4 > 55 if direction == "Buy" else rsi1 < 45 and rsi4 < 45
        macd_ok = macd1 > 0 and macd4 > 0 if direction == "Buy" else macd1 < 0 and macd4 < 0
        confirmed = rsi_ok and macd_ok

        try:
            high_10 = float(df1["High"].rolling(10).max().iloc[-2])
            low_10 = float(df1["Low"].rolling(10).min().iloc[-2])
            breakout = price > high_10 if direction == "Buy" else price < low_10
        except:
            breakout = False

        score = abs(price - sma) + abs(macd1) + (1.5 if breakout else 0) + (2 if confirmed else 0)
        entry = round(price, 2)
        sl = round(entry - atr, 2) if direction == "Buy" else round(entry + atr, 2)
        tp = round(entry + atr * 2, 2) if direction == "Buy" else round(entry - atr * 2, 2)

        return {
            "Symbol": symbol,
            "Direction": direction,
            "Confirmed": confirmed,
            "Breakout": breakout,
            "Entry": entry,
            "SL": sl,
            "TP": tp,
            "ATR": round(atr, 2),
            "RSI": f"{rsi1:.1f}/{rsi4:.1f}",
            "MACD": f"{macd1:.2f}/{macd4:.2f}",
            "Strength": score
        }
    except Exception as e:
        print(f"{symbol} error: {e}")
        return None

def format_trades(trades, label, emoji):
    if not trades:
        return ""
    section = f"{emoji} *{label} Confidence*\n"
    for i, t in enumerate(trades[:2], 1):
        tag = "✅ Confirmed" if t["Confirmed"] else "⚠️ Weak"
        breakout_tag = "🚀 Breakout" if t["Breakout"] else "⛔ No Breakout"
        section += (
            f"{i}. {t['Symbol']} — {t['Direction']} ({tag})\n"
            f"{breakout_tag}\n"
            f"📍 Entry: {t['Entry']} | SL: {t['SL']} | TP: {t['TP']}\n"
            f"📊 ATR: {t['ATR']} | RSI: {t['RSI']} | MACD: {t['MACD']}\n\n"
        )
    return section

def scan_deriv():
    results = []
    for symbol in watchlist:
        trade = score_trade(symbol)
        if trade:
            results.append(trade)
    if DEBUG_MODE:
        print("🔎 Signal Strengths:", [(t["Symbol"], round(t["Strength"], 2)) for t in results])

    high = [t for t in results if t["Strength"] >= (2.2 if DEBUG_MODE else 2.5)]
    medium = [t for t in results if 1.5 <= t["Strength"] < (2.2 if DEBUG_MODE else 2.5)]
    low = [t for t in results if 1.0 <= t["Strength"] < 1.5]

    high.sort(key=lambda x: x["Strength"], reverse=True)
    medium.sort(key=lambda x: x["Strength"], reverse=True)
    low.sort(key=lambda x: x["Strength"], reverse=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    report = "📊 *Deriv Market Scanner*\n\n"
    report += format_trades(high, "High", "🟢")
    report += format_trades(medium, "Medium", "🟡")
    report += format_trades(low, "Low", "🔴")
    report += f"🕒 Updated: {timestamp}"

    result_label.config(text=report)

# 🖼️ GUI Interface
app = tb.Window(themename="minty")
app.title("📈 Deriv Signal Scanner")
app.geometry("800x720")
app.resizable(False, False)

tb.Label(app, text="🧠 One-Click Signal Scanner", font=("Segoe UI", 15, "bold")).pack(pady=(20, 10))
tb.Button(app, text="📡 Scan Market", bootstyle=SUCCESS, command=scan_deriv).pack(pady=(5, 15))
result_label = tb.Label(app, text="", font=("Segoe UI", 12), justify="left", wraplength=700)
result_label.pack(pady=20)

app.mainloop()