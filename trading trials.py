import yfinance as yf
import pandas as pd

def analyze_asset(symbol):
    data = yf.download(symbol, period="30d", interval="1h")
    if data.empty or len(data) < 50:
        return f"🚫 Not enough data for {symbol}"

    data["SMA_fast"] = data["Close"].rolling(window=5).mean()
    data["SMA_slow"] = data["Close"].rolling(window=15).mean()
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    last = data.iloc[-1]
    entry = round(last["Close"], 2)
    atr = round(data["High"].rolling(window=14).max().iloc[-1] - data["Low"].rolling(window=14).min().iloc[-1], 2)
    sl = round(entry - atr * 0.75, 2)
    tp = round(entry + atr * 1.5, 2)

    signal = "BUY" if last["SMA_fast"] > last["SMA_slow"] and last["RSI"] < 70 else "SELL" if last["SMA_fast"] < last["SMA_slow"] and last["RSI"] > 30 else "NEUTRAL"
    score = 70 + int(abs(last["RSI"] - 50)) if signal != "NEUTRAL" else 50

    return (
        f"🔍 {symbol}\n"
        f"Signal: {signal}\n"
        f"Entry: {entry} | SL: {sl} | TP: {tp}\n"
        f"Confidence: {score}%\n"
    )

# 🔎 Examples: Try these symbols
symbols = [
    "USDJPY=X",     # Forex
    "XAUUSD=X",     # Gold
    "^DJI",         # Dow Jones Index
    "AAPL",         # Stock
    "BTC-USD"       # Crypto
]

for sym in symbols:
    print(analyze_asset(sym))
    print("-" * 50) 