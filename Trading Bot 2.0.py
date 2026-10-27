import pandas as pd
import yfinance as yf
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import datetime

# Trade log
trade_log = []

def analyze_trade(pair):
    try:
        data = yf.download(tickers=pair, interval="1h", period="2d", progress=False)

        if data.empty or len(data["Close"]) < 14:
            return "❌ Not enough data to analyze."

        # Indicators
        data["SMA"] = data["Close"].rolling(window=5).mean()
        data["High-Low"] = data["High"] - data["Low"]
        data["High-Close"] = abs(data["High"] - data["Close"].shift())
        data["Low-Close"] = abs(data["Low"] - data["Close"].shift())
        data["TrueRange"] = data[["High-Low", "High-Close", "Low-Close"]].max(axis=1)
        data["ATR"] = data["TrueRange"].rolling(window=14).mean()

        latest = data.iloc[-1]
        price = float(latest["Close"])
        sma = float(latest["SMA"])
        atr = float(latest["ATR"])

        if pd.isna(sma) or pd.isna(atr):
            return "⚠️ Indicators not ready yet. Try again shortly."
        if atr < 0.05:
            return "⚠️ ATR too low — trade signal not strong enough."

        # Trade logic
        direction = "Buy" if price > sma else "Sell"
        entry = round(price, 3)
        sl = round(entry - atr, 3) if direction == "Buy" else round(entry + atr, 3)
        tp = round(entry + atr * 2, 3) if direction == "Buy" else round(entry - atr * 2, 3)

        # Signal strength rating
        diff = abs(price - sma)
        score = "High" if diff > atr * 1.2 else "Medium" if diff >= atr * 0.5 else "Low"

        # Timestamp and logging
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        trade_log.append((pair, direction, entry, sl, tp, f"{atr:.3f}", score, timestamp))
        update_log()

        return (f"📊 Trade Setup for {pair}\n"
                f"Direction: {direction}  |  Confidence: {score}\n"
                f"Entry: {entry}\nStop Loss: {sl}  |  Take Profit: {tp}\n"
                f"ATR Volatility: {atr:.3f}")

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
app.title("🎯 Accurate Forex Assistant")
app.geometry("780x600")
app.resizable(False, False)

# Header
tb.Label(app, text="📥 Enter Currency Pair", font=("Segoe UI", 14)).pack(pady=(20, 5))
entry_box = tb.Entry(app, font=("Segoe UI", 12), width=30, bootstyle="info")
entry_box.pack(pady=(0, 5))

tb.Label(app, text="Format: USDJPY=X (Yahoo Finance ticker)", font=("Segoe UI", 10), bootstyle="warning").pack(pady=(0, 10))
tb.Button(app, text="🔍 Get Trade Setup", command=get_trade, bootstyle="success-outline").pack(pady=10)

# Result
result_label = tb.Label(app, text="", font=("Segoe UI", 12), justify="left", wraplength=700)
result_label.pack(pady=15)

# Trade History Table
tb.Label(app, text="📜 Trade History", font=("Segoe UI", 13, "bold")).pack()
columns = ("#", "Pair", "Direction", "Entry", "SL", "TP", "ATR", "Confidence", "Time")
log_table = tb.Treeview(app, columns=columns, show='headings', height=8, bootstyle="secondary")
for col in columns:
    log_table.heading(col, text=col)
    log_table.column(col, anchor="center", width=80)
log_table.pack(pady=(5, 20), padx=15)

app.mainloop()