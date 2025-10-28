import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

class ModernMessenger(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Заголовок
        layout.add_widget(Label(
            text='💬 Modern Messenger',
            font_size=24,
            bold=True
        ))
        
        # Область сообщений
        scroll = ScrollView()
        self.messages_layout = BoxLayout(
            orientation='vertical', 
            size_hint_y=None,
            spacing=10
        )
        self.messages_layout.bind(minimum_height=self.messages_layout.setter('height'))
        scroll.add_widget(self.messages_layout)
        layout.add_widget(scroll)
        
        # Панель ввода
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        self.message_input = TextInput(
            hint_text='Введите сообщение...',
            multiline=False
        )
        
        send_btn = Button(
            text='Отправить',
            size_hint_x=0.3
        )
        send_btn.bind(on_press=self.send_message)
        
        input_layout.add_widget(self.message_input)
        input_layout.add_widget(send_btn)
        layout.add_widget(input_layout)
        
        # Тестовые сообщения
        self.add_message("Система", "Добро пожаловать!")
        self.add_message("Бот", "Мессенджер готов к работе!")
        
        return layout
    
    def add_message(self, user, text):
        message_label = Label(
            text=f"{user}: {text}",
            size_hint_y=None,
            height=40,
            halign='left'
        )
        self.messages_layout.add_widget(message_label)
    
    def send_message(self, instance):
        text = self.message_input.text.strip()
        if text:
            self.add_message("Вы", text)
            self.message_input.text = ''

if __name__ == '__main__':
    ModernMessenger().run()
