import websocket
import json
import pandas as pd
import datetime
import ttkbootstrap as tb
from ttkbootstrap.constants import *


# 🎯 Top-performing Deriv assets
watchlist = [
    # 🇺🇸 U.S. Markets
    "^GSPC",     # S&P 500
    "^NDX",      # Nasdaq 100
    "^DJI",      # Dow Jones Industrial Average

    # 🇪🇺 European Indices
    "^GDAXI",    # Germany DAX 40
    "^FCHI",     # France CAC 40
    "^FTSE",     # UK FTSE 100
    "^STOXX50E", # Euro STOXX 50

    # 🇯🇵 Asian Indices
    "^N225",     # Japan Nikkei 225
    "^HSI",      # Hong Kong Hang Seng Index
    "^AXJO",     # Australia ASX 200

    # 🪙 Commodities
    "GC=F",      # Gold (Comex Futures)
    "SI=F",      # Silver
    "CL=F",      # Crude Oil (WTI)
    "BZ=F",      # Brent Oil

    # 🌡️ Volatility & Sentiment
    "^VIX",      # Volatility Index (Fear Gauge)
    "^XAUUSD",   # Spot Gold (alternative symbol)

    # 📦 U.S. Sectors (Bonus Plays)
    "XLF",       # Financials
    "XLK",       # Technology
    "XLE",       # Energy
    "XLI",       # Industrials
]

DERIV_URL = "wss://ws.derivws.com/websockets/v3"

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
    df["TR"] = df[["High", "Low", "Close"]].apply(
        lambda row: max(row["High"] - row["Low"], abs(row["High"] - row["Close"]), abs(row["Low"] - row["Close"])),
        axis=1
    )
    df["ATR"] = df["TR"].rolling(14).mean()
    return df

def score_trade(symbol, mode="Conservative"):
    try:
        df1 = calculate_indicators(fetch_candles(symbol, 3600, 60))
        df4 = calculate_indicators(fetch_candles(symbol, 14400, 60))
        l1, l4 = df1.iloc[-1], df4.iloc[-1]
        price, sma = l1["Close"], l1["SMA"]
        atr = l1["ATR"]
        rsi1, macd1 = l1["RSI"], l1["MACD_Hist"]
        rsi4, macd4 = l4["RSI"], l4["MACD_Hist"]

        if pd.isna(sma) or pd.isna(atr) or pd.isna(rsi1) or pd.isna(macd1):
            return None

        direction = "Buy" if price > sma else "Sell"
        rsi_ok = rsi1 > 55 and rsi4 > 55 if direction == "Buy" else rsi1 < 45 and rsi4 < 45
        macd_ok = macd1 > 0 and macd4 > 0 if direction == "Buy" else macd1 < 0 and macd4 < 0
        confirmed = rsi_ok and macd_ok

        high_10 = float(df1["High"].rolling(10).max().iloc[-2])
        low_10 = float(df1["Low"].rolling(10).min().iloc[-2])
        breakout = price > high_10 if direction == "Buy" else price < low_10

        score = abs(price - sma) + abs(macd1)
        if breakout: score += 1.5
        if confirmed: score += 2
        if mode == "Breakout": score += 0.5 if breakout else -0.5
        if mode == "Swing": score += 0.5 if confirmed else 0
        if mode == "Conservative": score -= 0.2 if not confirmed else 0

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
    if not trades: return ""
    section = f"{emoji} *{label} Confidence*\n"
    for i, t in enumerate(trades[:3], 1):
        tag = "✅ Confirmed" if t["Confirmed"] else "⚠️ Weak"
        breakout_tag = "🚀 Breakout" if t["Breakout"] else "⛔ No Breakout"
        section += (
            f"{i}. {t['Symbol']} — {t['Direction']} ({tag})\n"
            f"{breakout_tag}\n"
            f"📍 Entry: {t['Entry']} | SL: {t['SL']} | TP: {t['TP']}\n"
            f"📊 ATR: {t['ATR']} | RSI: {t['RSI']} | MACD: {t['MACD']}\n\n"
        )
    return section

def run_scan():
    loading_label = tb.Label(app, text="", font=("Segoe UI", 12, "italic"), foreground="gray")
    loading_label.pack(pady=(0, 10))
    loading_label.config(text="📡 Scanning Market... Please wait")
    frame = tb.Frame(app)
    frame.pack(padx=15, pady=10, fill=BOTH, expand=True)

    scrollbar = tb.Scrollbar(frame, orient=VERTICAL)
    scrollbar.pack(side=RIGHT, fill=Y)

    result_box = tb.Text(frame, font=("Segoe UI", 12), wrap="word", yscrollcommand=scrollbar.set)
    result_box.pack(side=LEFT, fill=BOTH, expand=True)

    scrollbar.config(command=result_box.yview)

    app.update_idletasks()
    mode = strategy_mode.get()
    results = []
    for symbol in watchlist:
        trade = score_trade(symbol, mode)
        if trade:
            results.append(trade)
    loading_label.config(text="")
    if not results:
        result_box.delete("1.0", "end")
        result_box.insert("end", "⚠️ No trade setups found.")
        return

    high = [t for t in results if t["Strength"] >= 2.5]
    medium = [t for t in results if 1.8 <= t["Strength"] < 2.5]
    low = [t for t in results if 1.2 <= t["Strength"] < 1.8]
    high.sort(key=lambda x: x["Strength"], reverse=True)
    medium.sort(key=lambda x: x["Strength"], reverse=True)
    low.sort(key=lambda x: x["Strength"], reverse=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    report = "📊 *Deriv Signal Scanner Results*\n\n"
    report += format_trades(high, "High", "🟢")
    report += format_trades(medium, "Medium", "🟡")
    report += format_trades(low, "Low", "🔴")
    report += f"🕒 Updated: {timestamp}"

    result_box.delete("1.0", "end")
    result_box.insert("end", report)

# 🎨 GUI Setup
app = tb.Window(themename="minty")
app.title("📈 Signal Scanner")
app.geometry("880x740")
app.resizable(True, True)

tb.Label(app, text="📡 High-Confidence Deriv Scanner", font=("Segoe UI", 15, "bold")).pack(pady=(20, 5))

strategy_mode = tb.StringVar(value="Conservative")
tb.Label(app, text="🎯 Strategy Mode:").pack()
tb.OptionMenu(app, strategy_mode, "Conservative", "Swing", "Breakout").pack(pady=(0, 10))

scan_button = tb
scan_button = tb.Button(app, text="🔍 Scan Market", bootstyle=SUCCESS, command=run_scan)
scan_button.pack(pady=(5, 10))

app.mainloop()