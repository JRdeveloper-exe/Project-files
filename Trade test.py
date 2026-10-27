import pandas as pd
import yfinance as yf
import tkinter as tk
from tkinter import messagebox

def analyze_trade(pair):
    try:
        # Fetch 2 days of hourly data
        data = yf.download(tickers=pair, interval="1h", period="2d", progress=False)

        # Check if data is valid
        if data.empty or len(data["Close"]) < 5:
            raise ValueError("Not enough data for analysis.")

        # Calculate SMA
        data["SMA"] = data["Close"].rolling(window=5).mean()
        latest_price = data["Close"].iloc[-1].item()
        latest_sma = data["SMA"].iloc[-1].item()

        # Basic trade logic
        if latest_price > latest_sma:
            direction = "Buy"
            entry = round(latest_price, 3)
            sl = round(entry - 0.300, 3)
            tp = round(entry + 0.500, 3)
        else:
            direction = "Sell"
            entry = round(latest_price, 3)
            sl = round(entry + 0.300, 3)
            tp = round(entry - 0.500, 3)

        return f"📊 Trade Setup for {pair}\nDirection: {direction}\nEntry: {entry}\nStop Loss: {sl}\nTake Profit: {tp}"

    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_trade():
    pair = entry_box.get().strip()
    if not pair:
        messagebox.showwarning("Input Error", "Please enter a currency pair like USDJPY=X or EURUSD=X")
        return
    result = analyze_trade(pair)
    result_label.config(text=result)

# GUI Setup
app = tk.Tk()
app.title("Forex Trade Assistant")

tk.Label(app, text="Enter Currency Pair (e.g. USDJPY=X):", font=("Arial", 12)).pack(pady=10)
entry_box = tk.Entry(app, width=20, font=("Arial", 12))
entry_box.pack()

tk.Button(app, text="Get Trade Setup", command=get_trade, font=("Arial", 12)).pack(pady=10)
result_label = tk.Label(app, text="", justify="left", font=("Arial", 12))
result_label.pack(pady=10)

app.geometry("400x250")
app.mainloop()