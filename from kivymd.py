from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.tab import MDTabbedPanel
from kivymd.uix.button import MDRaisedButton
from kivy.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivy.core.window import Window

# Set window size for testing if needed
Window.size = (360, 640)

class MainApp(MDApp):
    def build(self):
        from kivymd.uix.tab import MDTabs
        self.tabs = MDTabs()

        # Results tab
        results_tab = MDBoxLayout(orientation='vertical', padding=10, spacing=10)
        label = MDLabel(text='Results Area', size_hint_y=None, height=40)
        button = MDRaisedButton(text='Test Button')
        results_box = MDTextField(readonly=True)
        scrollview = MDScrollView()
        scrollview.add_widget(results_box)

        results_tab.add_widget(label)
        results_tab.add_widget(button)
        results_tab.add_widget(scrollview)

        # Logs tab
        logs_tab = MDBoxLayout(orientation='vertical', padding=10)
        logs_label = MDLabel(text='Logs Area', size_hint_y=None, height=40)
        logs_text = MDTextField(readonly=True)
        logs_scroll = MDScrollView()
        logs_scroll.add_widget(logs_text)

        logs_tab.add_widget(logs_label)
        logs_tab.add_widget(logs_scroll)

        # Add tabs
        self.tabs.add_widget(results_tab, title='Results')
        self.tabs.add_widget(logs_tab, title='Logs')

        return self.tabs

if __name__ == '__main__':
    MainApp().run()