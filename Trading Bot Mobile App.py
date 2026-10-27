import pandas as pd
import yfinance as yf
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import datetime

trade_log = []

def analyze_trade(pair):
    try:
        data = yf.download(tickers=pair, interval="1h", period="5d", progress=False)
        if data.empty or len(data["Close"]) < 20:
            return "❌ Not enough data to analyze."

        # SMA & slope
        data["SMA"] = data["Close"].rolling(window=5).mean()
        data["SMA_slope"] = data["SMA"] - data["SMA"].shift(5)

        # ATR
        data["High-Low"] = data["High"] - data["Low"]
        data["High-Close"] = abs(data["High"] - data["Close"].shift())
        data["Low-Close"] = abs(data["Low"] - data["Close"].shift())
        data["TrueRange"] = data[["High-Low", "High-Close", "Low-Close"]].max(axis=1)
        data["ATR"] = data["TrueRange"].rolling(window=14).mean()

        # RSI
        delta = data["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        data["RSI"] = 100 - (100 / (1 + rs))

        latest = data.iloc[-1]
        price = round(latest["Close"], 3)
        sma = round(latest["SMA"], 3)
        atr = round(latest["ATR"], 3)
        rsi = round(latest["RSI"], 2)
        slope = round(latest["SMA_slope"], 3)

        if pd.isna(sma) or pd.isna(atr) or pd.isna(rsi) or pd.isna(slope):
            return "⚠️ Indicators not ready. Please wait for more candles."

        # Trade logic
        if price > sma and rsi < 70 and slope > 0:
            direction = "Buy"
            sl = round(price - atr, 3)
            tp = round(price + atr * 2, 3)
        elif price < sma and rsi > 30 and slope < 0:
            direction = "Sell"
            sl = round(price + atr, 3)
            tp = round(price - atr * 2, 3)
        else:
            direction = "Neutral"
            sl = tp = None

        # Confidence score
        score = 50
        if direction != "Neutral":
            score += int(abs(rsi - 50))
            score += int(abs(slope * 10))
            score = min(score, 95)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sl_str = str(sl) if sl else "—"
        tp_str = str(tp) if tp else "—"

        trade_log.append((pair, direction, price, sl_str, tp_str, atr, rsi, slope, f"{score}%", timestamp))
        update_log()

        return (f"📊 Trade Setup for {pair}\n"
                f"Direction: {direction}\nEntry: {price}\n"
                f"Stop Loss: {sl_str} | Take Profit: {tp_str}\n"
                f"ATR Volatility: {atr} | RSI: {rsi} | SMA Trend: {slope}\n"
                f"Confidence Score: {score}%")

    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_trade():
    pair = entry_box.get().strip().upper()
    if not pair:
        messagebox.showwarning("Input Required", "Please enter a symbol like USDJPY=X")
        return
    result = analyze_trade(pair)
    result_label.config(text=result)

def update_log():
    log_table.delete(*log_table.get_children())
    for i, trade in enumerate(trade_log, start=1):
        log_table.insert('', 'end', values=(i,) + trade)

# 🎨 GUI Setup
app = tb.Window(themename="minty")
app.title("📈 Precision Trading Assistant")
app.geometry("880x600")
app.resizable(False, False)

tb.Label(app, text="📥 Enter Symbol", font=("Segoe UI", 14)).pack(pady=(20, 5))
entry_box = tb.Entry(app, font=("Segoe UI", 12), width=35, bootstyle="info")
entry_box.pack(pady=(0, 10))

tb.Button(app, text="🔍 Analyze", command=get_trade, bootstyle="success-outline").pack(pady=10)

result_label = tb.Label(app, text="", font=("Segoe UI", 11), justify="left", wraplength=820)
result_label.pack(pady=15)

tb.Label(app, text="📜 Trade History", font=("Segoe UI", 13, "bold")).pack()

columns = ("#", "Pair", "Direction", "Entry", "SL", "TP", "ATR", "RSI", "Trend", "Confidence", "Time")
log_table = tb.Treeview(app, columns=columns, show='headings', height=9, bootstyle="secondary")
for col in columns:
    log_table.heading(col, text=col)
    log_table.column(col, anchor="center", width=75)
log_table.pack(pady=(5, 20), padx=15)

app.mainloop()