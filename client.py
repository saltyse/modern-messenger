import socket
import threading
import json
from datetime import datetime

class ChatClient:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.client_socket = None
        self.connected = False
        self.current_user = None
        self.is_admin = False
        
        # Колбэки для обновления UI
        self.on_message_received = None
        self.on_users_updated = None
        self.on_channels_updated = None
        self.on_connection_status_changed = None
        
    def connect(self):
        """Подключается к серверу"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.connected = True
            
            # Запускаем поток для прослушивания сообщений
            listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            listen_thread.start()
            
            if self.on_connection_status_changed:
                self.on_connection_status_changed(True)
            
            return True
            
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            if self.on_connection_status_changed:
                self.on_connection_status_changed(False)
            return False
    
    def disconnect(self):
        """Отключается от сервера"""
        self.connected = False
        if self.client_socket:
            self.client_socket.close()
        self.current_user = None
        self.is_admin = False
        
        if self.on_connection_status_changed:
            self.on_connection_status_changed(False)
    
    def listen_for_messages(self):
        """Прослушивает сообщения от сервера"""
        while self.connected:
            try:
                data = self.client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                message_data = json.loads(data)
                self.handle_server_message(message_data)
                
            except Exception as e:
                if self.connected:
                    print(f"Ошибка при получении сообщения: {e}")
                break
        
        self.connected = False
        if self.on_connection_status_changed:
            self.on_connection_status_changed(False)
    
    def handle_server_message(self, message_data):
        """Обрабатывает сообщения от сервера"""
        message_type = message_data.get('type')
        
        if message_type == 'login_response':
            if message_data.get('success'):
                self.current_user = message_data.get('user')
                self.is_admin = message_data.get('is_admin', False)
            
        elif message_type == 'new_message':
            if self.on_message_received:
                self.on_message_received(message_data)
        
        elif message_type == 'messages_data':
            if self.on_message_received:
                self.on_message_received(message_data)
        
        elif message_type == 'users_list':
            if self.on_users_updated:
                self.on_users_updated(message_data)
        
        elif message_type == 'channels_list':
            if self.on_channels_updated:
                self.on_channels_updated(message_data)
        
        elif message_type == 'channels_updated':
            # Запрашиваем обновленный список каналов
            self.get_channels()
        
        elif message_type == 'user_online':
            print(f"Пользователь {message_data.get('user')} в сети")
        
        elif message_type == 'user_offline':
            print(f"Пользователь {message_data.get('user')} вышел из сети")
        
        elif message_type == 'message_deleted':
            # Обработка удаления сообщения
            pass
        
        elif message_type == 'error':
            print(f"Ошибка от сервера: {message_data.get('error')}")
    
    def send_message(self, message_data):
        """Отправляет сообщение на сервер"""
        if not self.connected:
            return False
        
        try:
            self.client_socket.send(json.dumps(message_data).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            return False
    
    def login(self, username, password):
        """Вход в систему"""
        message = {
            'type': 'login',
            'username': username,
            'password': password
        }
        return self.send_message(message)
    
    def register(self, username, password):
        """Регистрация нового пользователя"""
        message = {
            'type': 'register',
            'username': username,
            'password': password
        }
        return self.send_message(message)
    
    def send_chat_message(self, chat_type, message_text, target=None, image=None, video=None, voice=None):
        """Отправляет сообщение в чат"""
        message = {
            'type': 'send_message',
            'chat_type': chat_type,
            'message': message_text,
            'target': target,
            'image': image,
            'video': video,
            'voice': voice
        }
        return self.send_message(message)
    
    def load_messages(self, chat_type, target=None):
        """Загружает сообщения"""
        message = {
            'type': 'load_messages',
            'chat_type': chat_type,
            'target': target
        }
        return self.send_message(message)
    
    def create_channel(self, name, description, is_public=True, subscribers_can_write=True):
        """Создает новый канал"""
        message = {
            'type': 'create_channel',
            'name': name,
            'description': description,
            'is_public': is_public,
            'subscribers_can_write': subscribers_can_write
        }
        return self.send_message(message)
    
    def join_channel(self, channel_id):
        """Присоединяется к каналу"""
        message = {
            'type': 'join_channel',
            'channel_id': channel_id
        }
        return self.send_message(message)
    
    def get_channels(self):
        """Запрашивает список каналов"""
        message = {
            'type': 'get_channels'
        }
        return self.send_message(message)
    
    def get_users(self):
        """Запрашивает список пользователей"""
        message = {
            'type': 'get_users'
        }
        return self.send_message(message)
    
    def delete_message(self, message_id, chat_type, target=None):
        """Удаляет сообщение"""
        message = {
            'type': 'delete_message',
            'message_id': message_id,
            'chat_type': chat_type,
            'target': target
        }
        return self.send_message(message)