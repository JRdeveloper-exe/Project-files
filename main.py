import threading
import time
from datetime import datetime

from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget

import yfinance as yf
import pandas as pd
from plyer import notification

# Set window size for testing
Window.size = (360, 640)

# ------------ Your core analysis functions ------------
WATCHLIST = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X",
    "USDCAD=X", "NZDUSD=X", "USDCHF=X"
]

def fetch_indicators(pair, interval):
    try:
        data = yf.download(tickers=pair, period="7d", interval=interval, progress=False)
        if data.empty or len(data["Close"]) < 26:
            return None
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
        data["High-Low"] = data["High"] - data["Low"]
        data["High-Close"] = abs(data["High"] - data["Close"].shift())
        data["Low-Close"] = abs(data["Low"] - data["Close"].shift())
        data["TrueRange"] = data[["High-Low", "High-Close", "Low-Close"]].max(axis=1)
        data["ATR"] = data["TrueRange"].rolling(14).mean()
        return data
    except:
        return None

def check_breakout(data):
    latest = data.iloc[-1]
    high_max = data['High'].rolling(20).max().iloc[-1]
    low_min = data['Low'].rolling(20).min().iloc[-1]
    price = latest['Close']
    atr = latest.get('ATR', 0.1)
    if price > high_max + 1.5 * atr:
        return "Bullish Breakout"
    elif price < low_min - 1.5 * atr:
        return "Bearish Breakout"
    return None

def analyze_and_notify():
    logs = []
    for pair in WATCHLIST:
        data = fetch_indicators(pair, "15m")
        if data is not None:
            signal = check_breakout(data)
            if signal:
                msg = f"{pair} potential {signal} at {data['Close'][-1]:.4f}"
                # Send local notification
                notification.notify(title="Breakout Alert", message=msg, timeout=10)
                logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")
    return logs

# ------------ Kivy UI ------------

class ResultsTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.label = Label(text='Forex Scanner Results', size_hint_y=None, height=40)
        self.add_widget(self.label)

        self.btn = Button(text='Start Scan', size_hint_y=None, height=50)
        self.btn.bind(on_release=self.start_scan)
        self.add_widget(self.btn)

        self.output = TextInput(readonly=True)
        scrollview = ScrollView()
        scrollview.add_widget(self.output)
        self.add_widget(scrollview)

    def start_scan(self, instance):
        # Animate button press
        self.output.text = 'Scanning...'
        threading.Thread(target=self.run_scan).start()

    def run_scan(self):
        logs = analyze_and_notify()
        def update_ui():
            if logs:
                self.output.text = "\n".join(logs)
            else:
                self.output.text = 'No signals detected.'
        Clock.schedule_once(lambda dt: update_ui())

class LogsTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.label = Label(text='Activity Logs', size_hint_y=None, height=40)
        self.add_widget(self.label)

        self.log_output = TextInput(readonly=True)
        scrollview = ScrollView()
        scrollview.add_widget(self.log_output)
        self.add_widget(scrollview)

    def append_log(self, message):
        def update():
            self.log_output.text += message + "\n"
            self.log_output.cursor = (0, len(self.log_output.text))
        Clock.schedule_once(lambda dt: update())

class MainPanel(TabbedPanel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_default_tab = False

        self.results_tab = ResultsTab()
        self.logs_tab = LogsTab()

        self.add_widget(self.results_tab, title='Results')
        self.add_widget(self.logs_tab, title='Logs')

        # Example: Periodically run analysis automatically
        # Clock.schedule_interval(lambda dt: self.results_tab.start_scan(None), 600)  # every 10 mins

class MyApp(App):
    def build(self):
        return MainPanel()

if __name__ == '__main__':
    MyApp().run()