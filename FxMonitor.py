import threading
import time
from datetime import datetime
from plyer import notification
import pandas as pd
import yfinance as yf

# Forex pairs to analyze
watchlist = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", 
    "USDCAD=X", "NZDUSD=X", "USDCHF=X",
    "EURGBP=X", "EURJPY=X", "EURCHF=X",
    "GBPJPY=X", "GBPCHF=X",
    "CHFJPY=X", "AUDJPY=X", "NZDJPY=X", "CADJPY=X",
]

class ForexScanner:
    def __init__(self):
        self.scanning = False
        self.confidence_thresholds = {
            'High': 2.5,
            'Medium': 1.8,
            'Low': 1.2
        }
        self.scan_interval = 300  # 5 minutes between scans
        
    def fetch_indicators(self, pair, interval):
        try:
            data = yf.download(tickers=pair, interval=interval, period="5d", progress=False)
            if data.empty or len(data["Close"]) < 26:
                return None
                
            # Calculate indicators
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

    def score_trade(self, pair):
        d1 = self.fetch_indicators(pair, "1h")
        d4 = self.fetch_indicators(pair, "4h")
        if d1 is None or d4 is None:
            return None
            
        l1, l4 = d1.iloc[-1], d4.iloc[-1]
        price, sma = float(l1["Close"]), float(l1["SMA"])
        atr = float(l1["ATR"])
        rsi1 = float(l1["RSI"])
        rsi4 = float(l4["RSI"])
        macd1 = float(l1["MACD_Hist"])
        macd4 = float(l4["MACD_Hist"])
        
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

        # Calculate confidence score
        score = abs(price - sma) + abs(macd1)
        if breakout:
            score += 1.5
        if confirmed:
            score += 2

        # Entry points
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
            "Strength": score,
            "Time": datetime.now().strftime("%H:%M:%S")
        }

class ForexApp(App):
    status_text = StringProperty("Scanner: STOPPED")
    results_text = StringProperty("Press 'Scan Market' to begin analysis")
    last_update = StringProperty("Last update: Never")
    
    def build(self):
        self.title = "Forex Breakout Scanner"
        self.scanner = ForexScanner()
        
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Status bar
        status_bar = BoxLayout(size_hint=(1, None), height=40)
        self.status_label = Label(text=self.status_text)
        status_bar.add_widget(self.status_label)
        layout.add_widget(status_bar)
        
        # Control buttons
        btn_layout = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        
        self.start_btn = Button(
            text='START SCANNER',
            background_normal='',
            background_color=(0, 0.7, 0, 1)
        )
        self.start_btn.bind(on_press=self.start_scanning)
        btn_layout.add_widget(self.start_btn)
        
        self.stop_btn = Button(
            text='STOP SCANNER',
            background_normal='',
            background_color=(0.8, 0, 0, 1),
            disabled=True
        )
        self.stop_btn.bind(on_press=self.stop_scanning)
        btn_layout.add_widget(self.stop_btn)
        
        layout.add_widget(btn_layout)
        
        # Confidence thresholds
        thresholds = BoxLayout(size_hint=(1, None), height=30)
        thresholds.add_widget(Label(text="High: ≥2.5", color=(0, 0.7, 0, 1)))
        thresholds.add_widget(Label(text="Medium: ≥1.8", color=(1, 0.5, 0, 1)))
        thresholds.add_widget(Label(text="Low: ≥1.2", color=(0.8, 0, 0, 1)))
        layout.add_widget(thresholds)
        
        # Results display with ScrollView
        scroll = ScrollView(size_hint=(1, 1))
        self.output = TextInput(
            text=self.results_text,
            readonly=True,
            size_hint_y=None,
            font_size=14,
            background_color=(0.95, 0.95, 0.95, 1)
        )
        self.output.bind(minimum_height=self.output.setter('height'))
        scroll.add_widget(self.output)
        layout.add_widget(scroll)
        
        # Update time
        self.update_label = Label(text=self.last_update, size_hint=(1, None), height=30)
        layout.add_widget(self.update_label)
        
        return layout
    
    def start_scanning(self, instance):
        self.status_text = "Scanner: RUNNING"
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.results_text = "Scanning market... Please wait"
        self.scanner.scanning = True
        
        # Start scanning in background thread
        threading.Thread(target=self.run_scanner, daemon=True).start()
    
    def stop_scanning(self, instance):
        self.scanner.scanning = False
        self.status_text = "Scanner: STOPPED"
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
    
    def run_scanner(self):
        while self.scanner.scanning:
            try:
                results = []
                for pair in watchlist:
                    if not self.scanner.scanning:
                        break
                        
                    trade = self.scanner.score_trade(pair)
                    if trade:
                        results.append(trade)
                
                # Sort and filter results
                high_conf = [t for t in results if t["Strength"] >= 2.5]
                medium_conf = [t for t in results if 1.8 <= t["Strength"] < 2.5]
                low_conf = [t for t in results if 1.2 <= t["Strength"] < 1.8]
                
                high_conf.sort(key=lambda x: x["Strength"], reverse=True)
                medium_conf.sort(key=lambda x: x["Strength"], reverse=True)
                low_conf.sort(key=lambda x: x["Strength"], reverse=True)
                
                # Format results text
                report = ""
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if high_conf:
                    report += "=== HIGH CONFIDENCE TRADES ===\n"
                    report += self.format_trades(high_conf)
                    
                if medium_conf:
                    report += "\n=== MEDIUM CONFIDENCE TRADES ===\n"
                    report += self.format_trades(medium_conf)
                    
                if low_conf:
                    report += "\n=== LOW CONFIDENCE TRADES ===\n"
                    report += self.format_trades(low_conf)
                
                if not report:
                    report = "No trade setups found in current market conditions"
                
                report += f"\n\nLast update: {timestamp}"
                
                # Update UI
                Clock.schedule_once(lambda dt: self.update_results(report, len(results), timestamp))
                
                # Send notifications for high confidence trades
                for trade in high_conf[:3]:  # Limit to 3 notifications
                    try:
                        notification.notify(
                            title=f"Trade Signal: {trade['Pair']}",
                            message=f"{trade['Direction']} at {trade['Entry']}\nTP: {trade['TP']} SL: {trade['SL']}",
                            timeout=10
                        )
                    except Exception as e:
                        print(f"Notification failed: {str(e)}")
                
                # Wait for next scan
                time.sleep(self.scanner.scan_interval)
                
            except Exception as e:
                print(f"Scan error: {str(e)}")
                time.sleep(30)
    
    def update_results(self, text, num_trades, timestamp):
        self.results_text = text
        self.last_update = f"Last scan: {timestamp} | Found {num_trades} opportunities"
        # Auto-scroll to top
        self.output.scroll_y = 1
    
    def format_trades(self, trades):
        text = ""
        for t in trades:
            tag = "✅ Confirmed" if t["Confirmed"] else "⚠️ Waiting"
            breakout = "🚀 Breakout!" if t["Breakout"] else ""
            text += (
                f"{t['Pair']} - {t['Direction']} ({tag}) {breakout}\n"
                f"Entry: {t['Entry']} | SL: {t['SL']} | TP: {t['TP']}\n"
                f"RSI: {t['RSI']} | MACD: {t['MACD']} | ATR: {t['ATR']}\n"
                f"Strength: {t['Strength']:.2f}\n\n"
            )
        return text
    
    def on_stop(self):
        self.scanner.scanning = False

if __name__ == "__main__":
    ForexApp().run()
