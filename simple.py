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
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

import json
import os
import hashlib
from datetime import datetime

class ChatBubble(BoxLayout):
    def __init__(self, message_data, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(80)
        self.padding = [dp(10), dp(5)]
        
        is_own = message_data.get('is_own', False)
        username = message_data.get('user', 'Unknown')
        message_text = message_data.get('message', '')
        is_admin = message_data.get('is_admin', False)
        
        # Цвета
        if is_own:
            bubble_color = (0.39, 0.58, 0.93, 1)  # Синий
            text_color = (1, 1, 1, 1)  # Белый
        else:
            bubble_color = (0.95, 0.96, 0.98, 1)  # Серый
            text_color = (0.12, 0.16, 0.22, 1)    # Темный
        
        # Аватарка с инициалами
        if len(username) >= 2:
            initials = username[:2].upper()
        else:
            initials = username[0].upper() if username else "U"
        
        avatar_color = (0.55, 0.42, 0.96, 1) if is_admin else (0.39, 0.58, 0.93, 1)
        
        if not is_own:
            # Сообщение другого пользователя
            with self.canvas.before:
                Color(*avatar_color)
                Rectangle(pos=(self.x, self.y), size=(dp(40), dp(40)))
            
            self.add_widget(Label(
                text=initials,
                size_hint=(None, None),
                size=(dp(40), dp(40)),
                color=(1, 1, 1, 1),
                bold=True
            ))
            
            message_layout = BoxLayout(orientation='vertical', size_hint=(0.8, 1))
            
            # Имя пользователя
            name_label = Label(
                text=f"{username} {'👑' if is_admin else ''}",
                size_hint_y=0.3,
                color=(0.42, 0.45, 0.5, 1),
                bold=True
            )
            message_layout.add_widget(name_label)
            
            # Текст сообщения
            with message_layout.canvas.before:
                Color(*bubble_color)
                Rectangle(pos=message_layout.pos, size=message_layout.size)
            
            message_label = Label(
                text=message_text,
                size_hint_y=0.7,
                color=text_color,
                text_size=(Window.width * 0.6, None)
            )
            message_layout.add_widget(message_label)
            
            self.add_widget(message_layout)
            self.add_widget(Label(size_hint=(0.1, 1)))  # Пустое пространство
            
        else:
            # Собственное сообщение
            self.add_widget(Label(size_hint=(0.1, 1)))  # Пустое пространство
            
            message_layout = BoxLayout(orientation='vertical', size_hint=(0.8, 1))
            
            # Имя пользователя (выровнено по правому краю)
            name_label = Label(
                text=f"{username} {'👑' if is_admin else ''}",
                size_hint_y=0.3,
                color=(0.42, 0.45, 0.5, 1),
                bold=True
            )
            message_layout.add_widget(name_label)
            
            # Текст сообщения
            with message_layout.canvas.before:
                Color(*bubble_color)
                Rectangle(pos=message_layout.pos, size=message_layout.size)
            
            message_label = Label(
                text=message_text,
                size_hint_y=0.7,
                color=text_color,
                text_size=(Window.width * 0.6, None)
            )
            message_layout.add_widget(message_label)
            
            self.add_widget(message_layout)
            
            # Аватарка
            with self.canvas.before:
                Color(*avatar_color)
                Rectangle(pos=(self.right - dp(40), self.y), size=(dp(40), dp(40)))
            
            self.add_widget(Label(
                text=initials,
                size_hint=(None, None),
                size=(dp(40), dp(40)),
                color=(1, 1, 1, 1),
                bold=True
            ))

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=dp(50), spacing=dp(20))
        
        # Заголовок
        title_layout = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(10))
        title_layout.add_widget(Label(
            text='💬 Tandau Messenger',
            font_size=dp(32),
            bold=True
        ))
        title_layout.add_widget(Label(
            text='Кроссплатформенная версия',
            font_size=dp(16),
            color=(0.42, 0.45, 0.5, 1)
        ))
        layout.add_widget(title_layout)
        
        # Поля ввода
        input_layout = BoxLayout(orientation='vertical', size_hint_y=0.6, spacing=dp(15))
        
        self.username = TextInput(
            hint_text='Логин',
            size_hint_y=None,
            height=dp(60),
            multiline=False,
            padding=[dp(20), dp(15)]
        )
        
        self.password = TextInput(
            hint_text='Пароль',
            password=True,
            size_hint_y=None,
            height=dp(60),
            multiline=False,
            padding=[dp(20), dp(15)]
        )
        
        input_layout.add_widget(self.username)
        input_layout.add_widget(self.password)
        
        # Кнопки
        login_btn = Button(
            text='Войти',
            size_hint_y=None,
            height=dp(60),
            background_color=(0.39, 0.58, 0.93, 1)
        )
        login_btn.bind(on_press=self.login)
        
        register_btn = Button(
            text='Создать аккаунт',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.95, 0.96, 0.98, 1)
        )
        register_btn.bind(on_press=self.show_register)
        
        input_layout.add_widget(login_btn)
        input_layout.add_widget(register_btn)
        
        layout.add_widget(input_layout)
        self.add_widget(layout)
    
    def login(self, instance):
        username = self.username.text.strip()
        password = self.password.text.strip()
        
        if not username or not password:
            self.show_popup("Ошибка", "Заполните все поля")
            return
            
        app = App.get_running_app()
        if app.login(username, password):
            self.manager.current = 'chat'
        else:
            self.show_popup("Ошибка", "Неверный логин или пароль")
    
    def show_register(self, instance):
        self.manager.current = 'register'
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        content.add_widget(Label(text=message))
        close_btn = Button(text='OK', size_hint_y=None, height=dp(50))
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=dp(50), spacing=dp(20))
        
        layout.add_widget(Label(
            text='Регистрация',
            font_size=dp(28),
            bold=True,
            size_hint_y=0.2
        ))
        
        # Поля ввода в ScrollView для мобильных
        scroll = ScrollView()
        input_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(15))
        input_layout.bind(minimum_height=input_layout.setter('height'))
        
        self.username = TextInput(
            hint_text='Логин',
            size_hint_y=None,
            height=dp(60),
            multiline=False,
            padding=[dp(20), dp(15)]
        )
        
        self.password = TextInput(
            hint_text='Пароль',
            password=True,
            size_hint_y=None,
            height=dp(60),
            multiline=False,
            padding=[dp(20), dp(15)]
        )
        
        self.confirm = TextInput(
            hint_text='Повторите пароль',
            password=True,
            size_hint_y=None,
            height=dp(60),
            multiline=False,
            padding=[dp(20), dp(15)]
        )
        
        input_layout.add_widget(self.username)
        input_layout.add_widget(self.password)
        input_layout.add_widget(self.confirm)
        input_layout.height = dp(200)  # Фиксированная высота
        
        scroll.add_widget(input_layout)
        layout.add_widget(scroll)
        
        # Кнопки
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=dp(10))
        
        back_btn = Button(
            text='Назад',
            background_color=(0.42, 0.45, 0.5, 1)
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        
        register_btn = Button(
            text='Создать',
            background_color=(0.39, 0.58, 0.93, 1)
        )
        register_btn.bind(on_press=self.register)
        
        btn_layout.add_widget(back_btn)
        btn_layout.add_widget(register_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def register(self, instance):
        username = self.username.text.strip()
        password = self.password.text.strip()
        confirm = self.confirm.text.strip()
        
        if not all([username, password, confirm]):
            self.show_popup("Ошибка", "Заполните все поля")
            return
            
        if password != confirm:
            self.show_popup("Ошибка", "Пароли не совпадают")
            return
            
        if len(password) < 6:
            self.show_popup("Ошибка", "Пароль должен содержать минимум 6 символов")
            return
            
        app = App.get_running_app()
        if app.register(username, password):
            self.show_popup("Успех", "Регистрация завершена!")
            self.manager.current = 'login'
        else:
            self.show_popup("Ошибка", "Пользователь уже существует")
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        content.add_widget(Label(text=message))
        close_btn = Button(text='OK', size_hint_y=None, height=dp(50))
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_layout = BoxLayout(orientation='vertical')
        
        # Верхняя панель
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=0.1, padding=[dp(15), dp(10)])
        
        self.chat_title = Label(
            text='💬 Общий чат',
            font_size=dp(20),
            bold=True,
            halign='left'
        )
        top_bar.add_widget(self.chat_title)
        
        # Кнопки управления
        controls_layout = BoxLayout(orientation='horizontal', size_hint_x=0.5, spacing=dp(5))
        
        users_btn = Button(text='👥', size_hint_x=0.25, font_size=dp(18))
        users_btn.bind(on_press=self.show_users)
        
        channels_btn = Button(text='📡', size_hint_x=0.25, font_size=dp(18))
        channels_btn.bind(on_press=self.show_channels)
        
        admin_btn = Button(text='👑', size_hint_x=0.25, font_size=dp(18))
        admin_btn.bind(on_press=self.show_admin)
        
        logout_btn = Button(text='🚪', size_hint_x=0.25, font_size=dp(18))
        logout_btn.bind(on_press=self.logout)
        
        controls_layout.add_widget(users_btn)
        controls_layout.add_widget(channels_btn)
        controls_layout.add_widget(admin_btn)
        controls_layout.add_widget(logout_btn)
        
        top_bar.add_widget(controls_layout)
        main_layout.add_widget(top_bar)
        
        # Область сообщений
        self.chat_layout = GridLayout(cols=1, size_hint_y=0.8, spacing=dp(10), padding=[dp(15), dp(10)])
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        
        scroll = ScrollView()
        scroll.add_widget(self.chat_layout)
        main_layout.add_widget(scroll)
        
        # Панель ввода
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=dp(10), padding=[dp(15), dp(10)])
        
        # Кнопки медиа
        media_layout = BoxLayout(orientation='horizontal', size_hint_x=0.3, spacing=dp(5))
        
        image_btn = Button(text='📷', font_size=dp(18))
        image_btn.bind(on_press=self.attach_image)
        
        video_btn = Button(text='🎥', font_size=dp(18))
        video_btn.bind(on_press=self.attach_video)
        
        voice_btn = Button(text='🎤', font_size=dp(18))
        voice_btn.bind(on_press=self.toggle_voice)
        
        media_layout.add_widget(image_btn)
        media_layout.add_widget(video_btn)
        media_layout.add_widget(voice_btn)
        
        input_layout.add_widget(media_layout)
        
        self.message_input = TextInput(
            hint_text='Введите сообщение...',
            multiline=False,
            padding=[dp(15), dp(10)]
        )
        self.message_input.bind(on_text_validate=self.send_message)
        input_layout.add_widget(self.message_input)
        
        send_btn = Button(
            text='Отпр',
            size_hint_x=0.2,
            background_color=(0.39, 0.58, 0.93, 1)
        )
        send_btn.bind(on_press=self.send_message)
        input_layout.add_widget(send_btn)
        
        main_layout.add_widget(input_layout)
        
        self.add_widget(main_layout)
        
        # Переменные чата
        self.current_chat_type = "public"  # public, private, channel
        self.current_private_with = None
        self.current_channel_id = None
    
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_messages(), 0.1)
    
    def load_messages(self):
        self.chat_layout.clear_widgets()
        app = App.get_running_app()
        
        messages = app.get_messages(
            self.current_chat_type,
            self.current_private_with,
            self.current_channel_id
        )
        
        for msg in messages[-30:]:  # Последние 30 сообщений
            if not isinstance(msg, dict):
                continue
            
            # Определяем свое ли это сообщение
            msg['is_own'] = msg.get('user') == app.current_user
            
            bubble = ChatBubble(msg)
            self.chat_layout.add_widget(bubble)
        
        # Прокручиваем вниз
        Clock.schedule_once(self.scroll_to_bottom, 0.1)
    
    def scroll_to_bottom(self, dt):
        if self.chat_layout.parent:
            self.chat_layout.parent.scroll_y = 0
    
    def send_message(self, instance=None):
        text = self.message_input.text.strip()
        if not text:
            return
            
        app = App.get_running_app()
        success = app.send_message(
            text,
            self.current_chat_type,
            self.current_private_with,
            self.current_channel_id
        )
        
        if success:
            self.message_input.text = ''
            self.load_messages()
    
    def show_users(self, instance):
        app = App.get_running_app()
        users = app.get_users()
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text='👥 Пользователи', font_size=dp(20), bold=True))
        
        scroll = ScrollView()
        user_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        user_layout.bind(minimum_height=user_layout.setter('height'))
        
        for username in users:
            if username != app.current_user:
                btn = Button(
                    text=f'💬 {username}',
                    size_hint_y=None,
                    height=dp(50)
                )
                btn.bind(on_press=lambda instance, u=username: self.start_private_chat(u))
                user_layout.add_widget(btn)
        
        scroll.add_widget(user_layout)
        content.add_widget(scroll)
        
        close_btn = Button(text='Закрыть', size_hint_y=None, height=dp(50))
        popup = Popup(title='Выберите пользователя', content=content, size_hint=(0.8, 0.8))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        
        popup.open()
    
    def start_private_chat(self, username):
        self.current_chat_type = "private"
        self.current_private_with = username
        self.chat_title.text = f"💬 {username}"
        self.load_messages()
        
        # Закрываем попап
        for child in Window.children:
            if isinstance(child, Popup):
                child.dismiss()
    
    def show_channels(self, instance):
        app = App.get_running_app()
        channels = app.get_channels()
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text='📡 Каналы', font_size=dp(20), bold=True))
        
        for channel_id, channel_data in channels.items():
            btn = Button(
                text=f"📡 {channel_data.get('name', 'Без названия')}",
                size_hint_y=None,
                height=dp(60)
            )
            btn.bind(on_press=lambda instance, cid=channel_id: self.join_channel(cid))
            content.add_widget(btn)
        
        # Кнопка создания канала
        create_btn = Button(
            text='➕ Создать канал',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.39, 0.58, 0.93, 1)
        )
        create_btn.bind(on_press=self.show_create_channel)
        content.add_widget(create_btn)
        
        close_btn = Button(text='Закрыть', size_hint_y=None, height=dp(50))
        popup = Popup(title='Каналы', content=content, size_hint=(0.8, 0.8))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        
        popup.open()
    
    def show_create_channel(self, instance):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text='Создание канала', font_size=dp(20), bold=True))
        
        name_input = TextInput(
            hint_text='Название канала',
            size_hint_y=None,
            height=dp(50),
            multiline=False
        )
        desc_input = TextInput(
            hint_text='Описание',
            size_hint_y=None,
            height=dp(50),
            multiline=False
        )
        
        content.add_widget(name_input)
        content.add_widget(desc_input)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        
        create_btn = Button(text='Создать', background_color=(0.39, 0.58, 0.93, 1))
        cancel_btn = Button(text='Отмена')
        
        def create_channel(btn):
            name = name_input.text.strip()
            if name:
                app = App.get_running_app()
                if app.create_channel(name, desc_input.text.strip()):
                    popup.dismiss()
                    self.show_channels(None)
        
        create_btn.bind(on_press=create_channel)
        cancel_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(create_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(title='Новый канал', content=content, size_hint=(0.8, 0.6))
        popup.open()
    
    def join_channel(self, channel_id):
        app = App.get_running_app()
        channels = app.get_channels()
        channel_data = channels.get(channel_id, {})
        
        self.current_chat_type = "channel"
        self.current_channel_id = channel_id
        self.chat_title.text = f"📡 {channel_data.get('name', 'Канал')}"
        self.load_messages()
        
        # Закрываем попап
        for child in Window.children:
            if isinstance(child, Popup):
                child.dismiss()
    
    def show_admin(self, instance):
        app = App.get_running_app()
        if not app.is_admin:
            self.show_popup("Ошибка", "Требуются права администратора")
            return
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text='👑 Админ-панель', font_size=dp(20), bold=True))
        
        # Статистика
        stats = app.get_stats()
        content.add_widget(Label(text=f"👥 Пользователей: {stats['users']}"))
        content.add_widget(Label(text=f"💬 Сообщений: {stats['messages']}"))
        content.add_widget(Label(text=f"📡 Каналов: {stats['channels']}"))
        
        # Кнопки управления
        clear_btn = Button(
            text='🧹 Очистить все сообщения',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.93, 0.27, 0.27, 1)
        )
        clear_btn.bind(on_press=self.clear_messages)
        content.add_widget(clear_btn)
        
        close_btn = Button(text='Закрыть', size_hint_y=None, height=dp(50))
        popup = Popup(title='Админ-панель', content=content, size_hint=(0.8, 0.6))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        
        popup.open()
    
    def clear_messages(self, instance):
        app = App.get_running_app()
        if app.clear_all_messages():
            self.load_messages()
            self.show_popup("Успех", "Все сообщения очищены")
        
        for child in Window.children:
            if isinstance(child, Popup):
                child.dismiss()
    
    def attach_image(self, instance):
        self.show_popup("Инфо", "Прикрепление изображений в разработке")
    
    def attach_video(self, instance):
        self.show_popup("Инфо", "Прикрепление видео в разработке")
    
    def toggle_voice(self, instance):
        self.show_popup("Инфо", "Голосовые сообщения в разработке")
    
    def logout(self, instance):
        app = App.get_running_app()
        app.logout()
        self.manager.current = 'login'
        
        # Сброс состояния чата
        self.current_chat_type = "public"
        self.current_private_with = None
        self.current_channel_id = None
        self.chat_title.text = '💬 Общий чат'
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        content.add_widget(Label(text=message))
        close_btn = Button(text='OK', size_hint_y=None, height=dp(50))
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

class MessengerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user = None
        self.is_admin = False
        self.data_file = "messenger_data.json"
        self.initialize_data()
    
    def initialize_data(self):
        if not os.path.exists(self.data_file):
            data = {
                "users": {
                    "admin": {
                        "password": self.hash_password("admin123"),
                        "is_admin": True,
                        "registered": datetime.now().isoformat()
                    }
                },
                "messages": [],
                "private_messages": {},
                "channels": {},
                "channel_messages": {}
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
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
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if username in data["users"] and data["users"][username]["password"] == self.hash_password(password):
                self.current_user = username
                self.is_admin = data["users"][username].get("is_admin", False)
                return True
        except Exception as e:
            print(f"Ошибка входа: {e}")
        
        return False
    
    def register(self, username, password):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if username in data["users"]:
                return False
            
            data["users"][username] = {
                "password": self.hash_password(password),
                "is_admin": False,
                "registered": datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            return False
    
    def get_messages(self, chat_type="public", private_with=None, channel_id=None):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if chat_type == "public":
                return data.get("messages", [])
            elif chat_type == "private" and private_with:
                private_messages = data.get("private_messages", {})
                chat_key = f"{self.current_user}_{private_with}"
                chat_key_alt = f"{private_with}_{self.current_user}"
                
                for key in [chat_key, chat_key_alt]:
                    if key in private_messages:
                        return private_messages[key]
                return []
            elif chat_type == "channel" and channel_id:
                channel_messages = data.get("channel_messages", {})
                return channel_messages.get(channel_id, [])
                
        except Exception as e:
            print(f"Ошибка загрузки сообщений: {e}")
        
        return []
    
    def send_message(self, message_text, chat_type="public", private_with=None, channel_id=None):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            message_data = {
                'user': self.current_user,
                'message': message_text,
                'timestamp': datetime.now().isoformat(),
                'is_admin': self.is_admin,
                'id': str(int(datetime.now().timestamp()))
            }
            
            if chat_type == "public":
                if "messages" not in data:
                    data["messages"] = []
                data["messages"].append(message_data)
                
            elif chat_type == "private" and private_with:
                if "private_messages" not in data:
                    data["private_messages"] = {}
                
                chat_key = f"{self.current_user}_{private_with}"
                if chat_key not in data["private_messages"]:
                    data["private_messages"][chat_key] = []
                data["private_messages"][chat_key].append(message_data)
                
            elif chat_type == "channel" and channel_id:
                if "channel_messages" not in data:
                    data["channel_messages"] = {}
                
                if channel_id not in data["channel_messages"]:
                    data["channel_messages"][channel_id] = []
                data["channel_messages"][channel_id].append(message_data)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            return False
    
    def get_users(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return list(data.get("users", {}).keys())
        except:
            return []
    
    def get_channels(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("channels", {})
        except:
            return {}
    
    def create_channel(self, name, description=""):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "channels" not in data:
                data["channels"] = {}
            
            channel_id = str(int(datetime.now().timestamp()))
            data["channels"][channel_id] = {
                'name': name,
                'description': description,
                'owner': self.current_user,
                'created': datetime.now().isoformat(),
                'subscribers': [self.current_user]
            }
            
            # Создаем место для сообщений канала
            if "channel_messages" not in data:
                data["channel_messages"] = {}
            data["channel_messages"][channel_id] = []
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Ошибка создания канала: {e}")
            return False
    
    def get_stats(self):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            return {
                'users': len(data.get("users", {})),
                'messages': len(data.get("messages", [])),
                'channels': len(data.get("channels", {}))
            }
        except:
            return {'users': 0, 'messages': 0, 'channels': 0}
    
    def clear_all_messages(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data["messages"] = []
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Ошибка очистки: {e}")
            return False
    
    def logout(self):
        self.current_user = None
        self.is_admin = False

if __name__ == '__main__':
    MessengerApp().run()