import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock

import json
import os
import hashlib
from datetime import datetime

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # Заголовок
        layout.add_widget(Label(
            text='Tandau Messenger',
            font_size=32,
            size_hint_y=0.3
        ))
        
        # Поля ввода
        self.username = TextInput(
            hint_text='Логин',
            size_hint_y=0.2,
            multiline=False
        )
        
        self.password = TextInput(
            hint_text='Пароль',
            password=True,
            size_hint_y=0.2,
            multiline=False
        )
        
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        
        # Кнопки
        login_btn = Button(
            text='Войти',
            size_hint_y=0.15,
            background_color=(0.2, 0.6, 1, 1)
        )
        login_btn.bind(on_press=self.login)
        
        register_btn = Button(
            text='Создать аккаунт',
            size_hint_y=0.15
        )
        register_btn.bind(on_press=self.show_register)
        
        layout.add_widget(login_btn)
        layout.add_widget(register_btn)
        
        self.add_widget(layout)
    
    def login(self, instance):
        app = App.get_running_app()
        if app.login(self.username.text, self.password.text):
            self.manager.current = 'chat'
    
    def show_register(self, instance):
        self.manager.current = 'register'

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=50, spacing=15)
        
        layout.add_widget(Label(
            text='Регистрация',
            font_size=28,
            size_hint_y=0.2
        ))
        
        self.username = TextInput(hint_text='Логин', size_hint_y=0.15, multiline=False)
        self.password = TextInput(hint_text='Пароль', password=True, size_hint_y=0.15, multiline=False)
        self.confirm = TextInput(hint_text='Повторите пароль', password=True, size_hint_y=0.15, multiline=False)
        
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(self.confirm)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        
        back_btn = Button(text='Назад')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        
        register_btn = Button(text='Создать', background_color=(0.2, 0.8, 0.2, 1))
        register_btn.bind(on_press=self.register)
        
        btn_layout.add_widget(back_btn)
        btn_layout.add_widget(register_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def register(self, instance):
        app = App.get_running_app()
        if app.register(self.username.text, self.password.text, self.confirm.text):
            self.manager.current = 'login'

class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_layout = BoxLayout(orientation='vertical')
        
        # Верхняя панель
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        top_bar.add_widget(Label(text='💬 Общий чат', font_size=20))
        
        logout_btn = Button(text='Выход', size_hint_x=0.3)
        logout_btn.bind(on_press=self.logout)
        top_bar.add_widget(logout_btn)
        
        main_layout.add_widget(top_bar)
        
        # Область сообщений
        self.chat_layout = GridLayout(cols=1, size_hint_y=0.8, spacing=10)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        
        scroll = ScrollView()
        scroll.add_widget(self.chat_layout)
        main_layout.add_widget(scroll)
        
        # Панель ввода
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        
        self.message_input = TextInput(hint_text='Введите сообщение...', multiline=False)
        self.message_input.bind(on_text_validate=self.send_message)
        
        send_btn = Button(text='Отпр', size_hint_x=0.3)
        send_btn.bind(on_press=self.send_message)
        
        input_layout.add_widget(self.message_input)
        input_layout.add_widget(send_btn)
        main_layout.add_widget(input_layout)
        
        self.add_widget(main_layout)
    
    def on_enter(self):
        self.load_messages()
    
    def load_messages(self):
        self.chat_layout.clear_widgets()
        messages = App.get_running_app().get_messages()
        
        for msg in messages[-20:]:
            text = f"{msg.get('user', 'Unknown')}: {msg.get('message', '')}"
            label = Label(
                text=text,
                size_hint_y=None,
                height=40,
                text_size=(Window.width - 20, None),
                halign='left'
            )
            self.chat_layout.add_widget(label)
    
    def send_message(self, instance=None):
        text = self.message_input.text.strip()
        if text:
            app = App.get_running_app()
            if app.send_message(text):
                self.message_input.text = ''
                self.load_messages()
    
    def logout(self, instance):
        App.get_running_app().logout()
        self.manager.current = 'login'

class MessengerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user = None
        self.data_file = "messenger_data.json"
        self.initialize_data()
    
    def initialize_data(self):
        if not os.path.exists(self.data_file):
            data = {
                "users": {
                    "admin": {
                        "password": self.hash_password("admin123"),
                        "is_admin": True
                    }
                },
                "messages": []
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(ChatScreen(name='chat'))
        return sm
    
    def login(self, username, password):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            if username in data["users"] and data["users"][username]["password"] == self.hash_password(password):
                self.current_user = username
                return True
        except:
            pass
        return False
    
    def register(self, username, password, confirm):
        if not username or not password:
            return False
        if password != confirm:
            return False
        
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            if username in data["users"]:
                return False
            
            data["users"][username] = {
                "password": self.hash_password(password),
                "is_admin": False
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except:
            return False
    
    def get_messages(self):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            return data.get("messages", [])
        except:
            return []
    
    def send_message(self, text):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            message = {
                "user": self.current_user,
                "message": text,
                "timestamp": datetime.now().isoformat()
            }
            
            data["messages"].append(message)
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except:
            return False
    
    def logout(self):
        self.current_user = None

if __name__ == '__main__':
    MessengerApp().run()