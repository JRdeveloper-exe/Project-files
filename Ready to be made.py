import threading
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from plyer import notification
import pandas as pd
import yfinance as yf

# Forex pairs to analyze
watchlist = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X",
    "USDCAD=X", "NZDUSD=X", "USDCHF=X",
    "EURGBP=X", "EURJPY=X", "EURCHF=X", "EURAUD=X",
    "GBPJPY=X", "GBPAUD=X", "GBPCHF=X",
    "CHFJPY=X", "AUDJPY=X", "NZDJPY=X", "CADJPY=X",
    "AUDCAD=X", "NZDCAD=X", "AUDNZD=X"
]

def fetch_indicators(pair, interval):
    """Fetch technical indicators for a currency pair"""
    try:
        data = yf.download(tickers=pair, interval=interval, period="5d", progress=False)
        if data.empty or len(data["Close"]) < 26:
            return None
            
        # Calculate indicators
        data["SMA"] = data["Close"].rolling(5).mean()
        
        # RSI Calculation
        delta = data["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        data["RSI"] = 100 - (100 / (1 + rs))
        
        # MACD Calculation
        exp1 = data["Close"].ewm(span=12, adjust=False).mean()
        exp2 = data["Close"].ewm(span=26, adjust=False).mean()
        data["MACD"] = exp1 - exp2
        data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
        data["MACD_Hist"] = data["MACD"] - data["MACD_Signal"]
        
        # ATR Calculation
        data["High-Low"] = data["High"] - data["Low"]
        data["High-Close"] = abs(data["High"] - data["Close"].shift())
        data["Low-Close"] = abs(data["Low"] - data["Close"].shift())
        data["TrueRange"] = data[["High-Low", "High-Close", "Low-Close"]].max(axis=1)
        data["ATR"] = data["TrueRange"].rolling(14).mean()
        
        return data
    except Exception as e:
        print(f"Error fetching {pair}: {str(e)}")
        return None

def score_trade(pair, mode="Conservative"):
    """Score trade opportunity for a currency pair"""
    d1 = fetch_indicators(pair, "1h")
    d4 = fetch_indicators(pair, "4h")
    if d1 is None or d4 is None:
        return None
        
    l1, l4 = d1.iloc[-1], d4.iloc[-1]
    price, sma = float(l1["Close"]), float(l1["SMA"])
    atr = float(l1["ATR"])
    rsi1, macd1 = float(l1["RSI"]), float(l1["MACD_Hist"])
    rsi4, macd4 = float(l4["RSI"]), float(l4["MACD_Hist"])
    if pd.isna(sma) or pd.isna(atr) or pd.isna(rsi1) or pd.isna(macd1):
        return None

    direction = "Buy" if price > sma else "Sell"
    rsi_ok = (rsi1 > 55 and rsi4 > 55) if direction == "Buy" else (rsi1 < 45 and rsi4 < 45)
    macd_ok = (macd1 > 0 and macd4 > 0) if direction == "Buy" else (macd1 < 0 and macd4 < 0)
    confirmed = rsi_ok and macd_ok

    try:
        high_10 = float(d1["High"].rolling(10).max().iloc[-2])
        low_10 = float(d1["Low"].rolling(10).min().iloc[-2])
        breakout = (price > high_10) if direction == "Buy" else (price < low_10)
    except:
        breakout = False

    # Calculate score
    score = abs(price - sma) + abs(macd1)
    if breakout:
        score += 1.5
    if confirmed:
        score += 2

    # Adjust score based on trading mode    
    if mode == "Breakout":
        score += 0.5 if breakout else -0.5
    elif mode == "Swing":
        score += 0.5 if confirmed else 0
    elif mode == "Conservative":
        score -= 0.2 if not confirmed else 0

    # Calculate entry, stop loss and take profit
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

def run_analysis():
    """Run analysis on all currency pairs"""
    results = []
    for pair in watchlist:
        trade = score_trade(pair, mode="Conservative")
        if trade:
            results.append(trade)
    return results

class ForexApp(App):
    def build(self):
        """Build the Kivy GUI interface"""
        self.title = "Forex Scanner"
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Result label at top
        self.result_label = Label(
            text="Press 'Scan' to analyze markets",
            size_hint=(1, None),
            height=10,
            font_size=16,
            bold=True
        )
        layout.add_widget(self.result_label)
        
        # Scan button
        self.scan_btn = Button(
            text="SCAN MARKETS",
            size_hint=(1, None),
            border_radius=[10],
            height=10,
            font_size=18,
            background_normal='',
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.scan_btn.bind(on_press=self.start_scan)
        layout.add_widget(self.scan_btn)
        
        # Results output area
        self.output = TextInput(
            readonly=True,
            size_hint=(1, 1),
            text="Analysis results will appear here...",
            font_size=14,
            foreground_color=(0, 0, 0, 1),
            background_color=(0.95, 0.95, 0.95, 1)
        )
        layout.add_widget(self.output)
        
        return layout
    
    def start_scan(self, instance):
        """Handle scan button press"""
        self.result_label.text = "Scanning forex markets..."
        self.output.text = "Analyzing currency pairs, please wait..."
        threading.Thread(target=self.perform_analysis, daemon=True).start()
    
    def perform_analysis(self):
        """Perform analysis in background thread"""
        try:
            self.results = run_analysis()
            
            # Send notifications for strong signals
            for res in self.results:
                if res["Strength"] >= 2.5:
                    notification.notify(
                        title=f"Trade Alert: {res['Pair']}",
                        message=f"{res['Direction']} at {res['Entry']} (TP: {res['TP']} | SL: {res['SL']})",
                        timeout=10
                    )
            
            # Update UI when completed
            Clock.schedule_once(self.update_ui)
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            Clock.schedule_once(lambda dt: self.show_error(str(e)))
    
    def update_ui(self, dt):
        """Update the UI with analysis results"""
        if not self.results:
            self.output.text = "⚠️ No trade setups found in any currency pairs."
        else:
            # Categorize results by confidence
            high = [t for t in self.results if t["Strength"] >= 2.5]
            medium = [t for t in self.results if 1.8 <= t["Strength"] < 2.5]
            low = [t for t in self.results if 1.2 <= t["Strength"] < 1.8]
            
            # Sort each category by strength
            high.sort(key=lambda x: x["Strength"], reverse=True)
            medium.sort(key=lambda x: x["Strength"], reverse=True)
            low.sort(key=lambda x: x["Strength"], reverse=True)
            
            # Generate report
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            report = f"⭐ FOREX SCAN RESULTS ({timestamp}) ⭐\n\n"
            
            if high:
                report += "=== HIGH CONFIDENCE TRADES ===\n"
                report += self.format_trades(high) + "\n"
            
            if medium:
                report += "=== MEDIUM CONFIDENCE TRADES ===\n"
                report += self.format_trades(medium) + "\n"
            
            if low:
                report += "=== LOW CONFIDENCE TRADES ===\n" 
                report += self.format_trades(low) + "\n"
            
            self.output.text = report
        
        self.result_label.text = "Analysis complete"
    
    def show_error(self, message):
        """Display error message in UI"""
        self.result_label.text = "Error occurred"
        self.output.text = f"ERROR: {message}\n\nPlease check logs and try again."
    
    def format_trades(self, trades):
        """Format trade details for display"""
        text = ""
        for t in trades:
            confidence = "✅ HIGH" if t["Strength"] >= 2.5 else ("⚠️ MEDIUM" if t["Strength"] >= 1.8 else "❌ LOW")
            direction_color = "[color=008000]BUY[/color]" if t["Direction"] == "Buy" else "[color=FF0000]SELL[/color]"
            breakout = "[b]🚀 BREAKOUT[/b]" if t["Breakout"] else ""
            
            text += (
                f"[b]{t['Pair']}[/b] - {direction_color} ({confidence}) {breakout}\n"
                f"• Entry: {t['Entry']} | TP: [b]{t['TP']}[/b] | SL: [b]{t['SL']}[/b]\n"
                f"• RSI: {t['RSI']} | MACD: {t['MACD']}\n"
                f"• ATR: {t['ATR']}\n\n"
            )
        return text

if __name__ == "__main__":
    ForexApp().run()
