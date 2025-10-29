from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import json
import uuid
from typing import Dict, List
import uvicorn

# Конфигурация
class Config:
    SECRET_KEY = "tandau-secret-key-2024-render"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440
    DATABASE_URL = "sqlite:///./tandau.db"

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Настройка БД
engine = create_engine(Config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Аутентификация
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

# Менеджер WebSocket соединений
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        if username not in self.active_connections:
            self.active_connections[username] = []
        self.active_connections[username].append(websocket)
        
        # Уведомляем о новом пользователе
        await self.broadcast_system_message(f"🟢 {username} присоединился к чату")
        await self.broadcast_user_list()

    def disconnect(self, websocket: WebSocket, username: str):
        if username in self.active_connections:
            self.active_connections[username].remove(websocket)
            if not self.active_connections[username]:
                del self.active_connections[username]

    async def broadcast(self, message: str):
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_text(message)
                except:
                    continue

    async def broadcast_user_list(self):
        users = list(self.active_connections.keys())
        await self.broadcast(json.dumps({
            "type": "user_list", 
            "users": users
        }))

    async def broadcast_system_message(self, message: str):
        await self.broadcast(json.dumps({
            "type": "system",
            "id": str(uuid.uuid4()),
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }))

    async def send_message(self, message_data: dict):
        await self.broadcast(json.dumps({
            "type": "message",
            "id": str(uuid.uuid4()),
            "username": message_data["username"],
            "content": message_data["content"],
            "timestamp": datetime.utcnow().isoformat()
        }))

# Модели запросов
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# FastAPI приложение
app = FastAPI(title="Tandau Messenger")
manager = ConnectionManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# HTML интерфейс
HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tandau Messenger</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #0F0F1A; 
            color: #FFFFFF;
            height: 100vh;
            overflow: hidden;
        }
        .container { 
            display: flex; 
            height: 100vh; 
        }
        .sidebar {
            width: 300px;
            background: #1A1B2E;
            border-right: 1px solid #373755;
            display: flex;
            flex-direction: column;
        }
        .sidebar-header {
            background: linear-gradient(135deg, #6366F1, #8B5CF6);
            padding: 2rem;
            text-align: center;
        }
        .sidebar-header h1 {
            font-size: 1.8rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .user-info {
            background: #252642;
            margin: 1rem;
            padding: 1.5rem;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .user-avatar {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #6366F1, #8B5CF6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2rem;
        }
        .user-details h3 {
            font-size: 1.1rem;
            margin-bottom: 0.2rem;
        }
        .status-online {
            color: #10B981;
            font-size: 0.9rem;
        }
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .chat-header {
            background: #1A1B2E;
            padding: 1.5rem 2rem;
            border-bottom: 1px solid #373755;
        }
        .chat-header h2 {
            font-size: 1.5rem;
        }
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 2rem;
            background: #0F0F1A;
        }
        .message {
            margin-bottom: 1.5rem;
            display: flex;
            gap: 1rem;
        }
        .message.own {
            flex-direction: row-reverse;
        }
        .message-avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #6366F1, #8B5CF6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9rem;
            flex-shrink: 0;
        }
        .message-content {
            max-width: 60%;
        }
        .message.own .message-content {
            text-align: right;
        }
        .message-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .message.own .message-header {
            justify-content: flex-end;
        }
        .message-username {
            font-weight: bold;
        }
        .message-time {
            font-size: 0.8rem;
            color: #6B6B8B;
        }
        .message-bubble {
            background: #252642;
            padding: 1rem 1.5rem;
            border-radius: 18px;
            display: inline-block;
        }
        .message.own .message-bubble {
            background: #6366F1;
        }
        .system-message {
            text-align: center;
            color: #A0A0B8;
            font-style: italic;
            margin: 1rem 0;
        }
        .input-area {
            background: #1A1B2E;
            padding: 1.5rem 2rem;
            border-top: 1px solid #373755;
        }
        .input-container {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        .message-input {
            flex: 1;
            background: #252642;
            border: 1px solid #373755;
            border-radius: 25px;
            padding: 1rem 1.5rem;
            color: white;
            font-size: 1rem;
            outline: none;
        }
        .message-input:focus {
            border-color: #6366F1;
        }
        .send-button {
            background: #6366F1;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 1rem 2rem;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        .send-button:hover {
            background: #4F46E5;
        }
        .auth-container {
            display: flex;
            height: 100vh;
            background: linear-gradient(135deg, #4F46E5, #0F0F1A);
        }
        .auth-left {
            flex: 1;
            background: #6366F1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .auth-left-content {
            text-align: center;
            max-width: 400px;
        }
        .auth-left h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        .auth-right {
            flex: 1;
            background: #1A1B2E;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .auth-form {
            width: 400px;
            padding: 2rem;
        }
        .auth-form h2 {
            font-size: 2rem;
            margin-bottom: 2rem;
            text-align: center;
        }
        .form-input {
            width: 100%;
            background: #252642;
            border: 1px solid #373755;
            border-radius: 12px;
            padding: 1rem 1.5rem;
            color: white;
            font-size: 1rem;
            margin-bottom: 1.5rem;
            outline: none;
        }
        .form-input:focus {
            border-color: #6366F1;
        }
        .auth-button {
            width: 100%;
            background: #6366F1;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 1rem;
            font-size: 1.1rem;
            cursor: pointer;
            margin-bottom: 1rem;
        }
        .auth-switch {
            text-align: center;
            color: #6366F1;
            cursor: pointer;
        }
        .users-list {
            background: #252642;
            margin: 1rem;
            padding: 1rem;
            border-radius: 12px;
            flex: 1;
            overflow-y: auto;
        }
        .user-list-item {
            padding: 0.5rem;
            margin: 0.2rem 0;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .user-online-indicator {
            width: 8px;
            height: 8px;
            background: #10B981;
            border-radius: 50%;
        }
    </style>
</head>
<body>
    <!-- Экран аутентификации -->
    <div id="authScreen" class="auth-container">
        <div class="auth-left">
            <div class="auth-left-content">
                <h1>Tandau</h1>
                <p style="font-size: 1.2rem; margin-bottom: 2rem;">Современный веб-мессенджер</p>
                <div style="text-align: left;">
                    <div style="margin: 1rem 0; font-size: 1.1rem;">🔒 Безопасное общение</div>
                    <div style="margin: 1rem 0; font-size: 1.1rem;">🌐 Реальное время</div>
                    <div style="margin: 1rem 0; font-size: 1.1rem;">👥 Публичные чаты</div>
                </div>
            </div>
        </div>
        <div class="auth-right">
            <div class="auth-form">
                <h2 id="authTitle">Вход в систему</h2>
                <div id="loginForm">
                    <input type="text" id="loginUsername" class="form-input" placeholder="Имя пользователя">
                    <input type="password" id="loginPassword" class="form-input" placeholder="Пароль">
                    <button class="auth-button" onclick="login()">Войти</button>
                    <div class="auth-switch" onclick="showRegister()">
                        Нет аккаунта? Зарегистрироваться
                    </div>
                </div>
                <div id="registerForm" style="display: none;">
                    <input type="text" id="registerUsername" class="form-input" placeholder="Имя пользователя">
                    <input type="password" id="registerPassword" class="form-input" placeholder="Пароль">
                    <input type="password" id="registerConfirm" class="form-input" placeholder="Повторите пароль">
                    <button class="auth-button" onclick="register()">Зарегистрироваться</button>
                    <div class="auth-switch" onclick="showLogin()">
                        Уже есть аккаунт? Войти
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Основной интерфейс -->
    <div id="mainScreen" class="container" style="display: none;">
        <div class="sidebar">
            <div class="sidebar-header">
                <h1>Tandau</h1>
                <p>Web Messenger</p>
            </div>
            
            <div class="user-info">
                <div class="user-avatar" id="userAvatar">US</div>
                <div class="user-details">
                    <h3 id="userName">User</h3>
                    <div class="status-online">🟢 В сети</div>
                </div>
            </div>

            <div class="users-list">
                <h4 style="margin-bottom: 1rem;">Онлайн сейчас:</h4>
                <div id="onlineUsersList"></div>
            </div>
        </div>

        <div class="chat-area">
            <div class="chat-header">
                <h2>🌐 Публичный чат</h2>
            </div>

            <div class="messages-container" id="messagesContainer">
                <div class="system-message">
                    Добро пожаловать в Tandau Messenger! 🎉
                </div>
            </div>

            <div class="input-area">
                <div class="input-container">
                    <input type="text" id="messageInput" class="message-input" 
                           placeholder="Введите сообщение..." disabled>
                    <button id="sendButton" class="send-button" onclick="sendMessage()" disabled>
                        Отправить
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let currentUser = null;
        let token = null;

        async function login() {
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;

            if (!username || !password) {
                alert('Пожалуйста, заполните все поля');
                return;
            }

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password }),
                });

                const data = await response.json();

                if (response.ok) {
                    token = data.access_token;
                    currentUser = username;
                    startWebSocket();
                    showMainScreen();
                } else {
                    alert(data.detail || 'Ошибка входа');
                }
            } catch (error) {
                alert('Ошибка подключения к серверу');
            }
        }

        async function register() {
            const username = document.getElementById('registerUsername').value;
            const password = document.getElementById('registerPassword').value;
            const confirm = document.getElementById('registerConfirm').value;

            if (!username || !password || !confirm) {
                alert('Пожалуйста, заполните все поля');
                return;
            }

            if (password !== confirm) {
                alert('Пароли не совпадают');
                return;
            }

            if (username.length < 3) {
                alert('Имя пользователя должно быть не менее 3 символов');
                return;
            }

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password }),
                });

                const data = await response.json();

                if (response.ok) {
                    alert('Регистрация успешна! Теперь вы можете войти.');
                    showLogin();
                } else {
                    alert(data.detail || 'Ошибка регистрации');
                }
            } catch (error) {
                alert('Ошибка подключения к серверу');
            }
        }

        function showLogin() {
            document.getElementById('authTitle').textContent = 'Вход в систему';
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('registerForm').style.display = 'none';
        }

        function showRegister() {
            document.getElementById('authTitle').textContent = 'Регистрация';
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('registerForm').style.display = 'block';
        }

        function showMainScreen() {
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('mainScreen').style.display = 'flex';
            document.getElementById('userName').textContent = currentUser;
            document.getElementById('userAvatar').textContent = currentUser.substring(0, 2).toUpperCase();
            document.getElementById('messageInput').disabled = false;
            document.getElementById('sendButton').disabled = false;
        }

        function startWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws?token=${token}`;
            
            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                console.log('WebSocket connected');
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            ws.onclose = function() {
                console.log('WebSocket disconnected');
                setTimeout(() => {
                    if (currentUser) {
                        startWebSocket();
                    }
                }, 3000);
            };
        }

        function handleWebSocketMessage(data) {
            switch (data.type) {
                case 'message':
                    displayMessage(data);
                    break;
                case 'system':
                    displaySystemMessage(data);
                    break;
                case 'user_list':
                    updateOnlineUsers(data.users);
                    break;
            }
        }

        function displayMessage(message) {
            const container = document.getElementById('messagesContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${message.username === currentUser ? 'own' : ''}`;
            
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    ${message.username.substring(0, 2).toUpperCase()}
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-username">${message.username}</span>
                        <span class="message-time">${formatTime(message.timestamp)}</span>
                    </div>
                    <div class="message-bubble">
                        ${message.content}
                    </div>
                </div>
            `;
            
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }

        function displaySystemMessage(message) {
            const container = document.getElementById('messagesContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'system-message';
            messageDiv.textContent = message.content;
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }

        function updateOnlineUsers(users) {
            const container = document.getElementById('onlineUsersList');
            container.innerHTML = '';
            
            users.forEach(user => {
                const userDiv = document.createElement('div');
                userDiv.className = 'user-list-item';
                userDiv.innerHTML = `
                    <div class="user-online-indicator"></div>
                    <span>${user}</span>
                `;
                container.appendChild(userDiv);
            });
        }

        function formatTime(timestamp) {
            const date = new Date(timestamp);
            return date.toLocaleTimeString('ru-RU', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const content = input.value.trim();
            
            if (content && ws && ws.readyState === WebSocket.OPEN) {
                const message = {
                    content: content
                };
                
                ws.send(JSON.stringify(message));
                input.value = '';
            }
        }

        // Обработка Enter для отправки сообщения
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Инициализация
        showLogin();
    </script>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(HTML)

@app.post("/api/auth/register")
async def register(user: UserRegister, db: SessionLocal = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    
    return {"message": "User created successfully"}

@app.post("/api/auth/login")
async def login(user: UserLogin, db: SessionLocal = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    username = verify_token(token)
    if not username:
        await websocket.close()
        return

    await manager.connect(websocket, username)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Сохраняем в базу данных
            db = SessionLocal()
            db_message = Message(
                username=username,
                content=message_data["content"]
            )
            db.add(db_message)
            db.commit()
            db.close()
            
            # Отправляем всем
            await manager.send_message({
                "username": username,
                "content": message_data["content"]
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, username)
        await manager.broadcast_system_message(f"🔴 {username} покинул чат")
        await manager.broadcast_user_list()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5555, log_level="info")
