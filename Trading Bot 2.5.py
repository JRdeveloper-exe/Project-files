import pandas as pd
import yfinance as yf
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import datetime

trade_log = []

def fetch_indicators(pair, interval, period="5d"):
    data = yf.download(tickers=pair, interval=interval, period=period, progress=False)

    if data.empty or len(data["Close"]) < 26:
        return None

    data["SMA"] = data["Close"].rolling(window=5).mean()
    data["High-Low"] = data["High"] - data["Low"]
    data["High-Close"] = abs(data["High"] - data["Close"].shift())
    data["Low-Close"] = abs(data["Low"] - data["Close"].shift())
    data["TrueRange"] = data[["High-Low", "High-Close", "Low-Close"]].max(axis=1)
    data["ATR"] = data["TrueRange"].rolling(window=14).mean()

    # RSI
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
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

    return data

def analyze_trade(pair):
    try:
        data_1h = fetch_indicators(pair, "1h")
        data_4h = fetch_indicators(pair, "4h")

        if data_1h is None or data_4h is None:
            return "❌ Not enough data on one or both timeframes."

        latest_1h = data_1h.iloc[-1]
        latest_4h = data_4h.iloc[-1]

        # Extract indicators
        price = float(latest_1h["Close"])
        sma = float(latest_1h["SMA"])
        atr = float(latest_1h["ATR"])
        rsi_1h = float(latest_1h["RSI"])
        macd_1h = float(latest_1h["MACD_Hist"])
        rsi_4h = float(latest_4h["RSI"])
        macd_4h = float(latest_4h["MACD_Hist"])

        if pd.isna(sma) or pd.isna(atr) or pd.isna(rsi_1h) or pd.isna(macd_1h):
            return "⚠️ Indicators still warming up. Try again shortly."
        if atr < 0.05:
            return "⚠️ ATR too low — market might be too quiet to trade safely."

        # Direction based on SMA
        direction = "Buy" if price > sma else "Sell"

        # Confirm signal using RSI and MACD
        rsi_pass = (rsi_1h > 55 and rsi_4h > 55) if direction == "Buy" else (rsi_1h < 45 and rsi_4h < 45)
        macd_pass = (macd_1h > 0 and macd_4h > 0) if direction == "Buy" else (macd_1h < 0 and macd_4h < 0)

        if not (rsi_pass and macd_pass):
            return "⚠️ Signal not confirmed by RSI and MACD on both timeframes."

        # Trade setup
        entry = round(price, 3)
        sl = round(entry - atr, 3) if direction == "Buy" else round(entry + atr, 3)
        tp = round(entry + atr * 2, 3) if direction == "Buy" else round(entry - atr * 2, 3)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        trade_log.append((pair, direction, entry, sl, tp, f"{atr:.3f}", "Confirmed", timestamp))
        update_log()

        return (f"✅ Confirmed Signal for {pair}\n"
                f"Direction: {direction}\n"
                f"Entry: {entry}\nStop Loss: {sl}  |  Take Profit: {tp}\n"
                f"ATR Volatility: {atr:.3f}\nRSI: {rsi_1h:.1f} / {rsi_4h:.1f} | MACD Hist: {macd_1h:.3f} / {macd_4h:.3f}")

    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_trade():
    pair = entry_box.get().strip().upper()
    if not pair:
        messagebox.showwarning("Input Required", "Please enter a currency pair like USDJPY=X")
        return
    result = analyze_trade(pair)
    result_label.config(text=result)

def update_log():
    log_table.delete(*log_table.get_children())
    for i, trade in enumerate(trade_log, start=1):
        log_table.insert('', 'end', values=(i,) + trade)

# 🎨 UI Setup
app = tb.Window(themename="minty")
app.title("📈 RSI + MACD Forex Assistant")
app.geometry("800x600")
app.resizable(False, False)

tb.Label(app, text="📥 Enter Currency Pair", font=("Segoe UI", 14)).pack(pady=(20, 5))
entry_box = tb.Entry(app, font=("Segoe UI", 12), width=30, bootstyle="info")
entry_box.pack(pady=(0, 5))
tb.Label(app, text="Format: USDJPY=X (Yahoo Finance)", font=("Segoe UI", 10), bootstyle="warning").pack(pady=(0, 10))
tb.Button(app, text="🔍 Get Trade Setup", command=get_trade, bootstyle="success-outline").pack(pady=10)

result_label = tb.Label(app, text="", font=("Segoe UI", 12), justify="left", wraplength=700)
result_label.pack(pady=15)

tb.Label(app, text="📜 Trade History", font=("Segoe UI", 13, "bold")).pack()
columns = ("#", "Pair", "Direction", "Entry", "SL", "TP", "ATR", "Signal", "Time")
log_table = tb.Treeview(app, columns=columns, show='headings', height=8, bootstyle="secondary")
for col in columns:
    log_table.heading(col, text=col)
    log_table.column(col, anchor="center", width=85)
log_table.pack(pady=(5, 20), padx=15)

app.mainloop()