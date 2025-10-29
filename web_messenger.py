from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
    SECRET_KEY = "tandau-secret-key-2024"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 часа
    DATABASE_URL = "sqlite:///./tandau.db"

Base = declarative_base()

# Модели базы данных
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50))
    content = Column(Text)
    message_type = Column(String(20), default="text")
    timestamp = Column(DateTime, default=datetime.utcnow)

# Настройка БД
engine = create_engine(Config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Аутентификация
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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

# Менеджер соединений
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        if username not in self.user_connections:
            self.user_connections[username] = []
        self.user_connections[username].append(websocket)
        
        await self.broadcast_system_message(f"🟢 {username} присоединился к чату")
        await self.broadcast_user_list()

    def disconnect(self, websocket: WebSocket, username: str):
        if username in self.user_connections:
            self.user_connections[username].remove(websocket)
            if not self.user_connections[username]:
                del self.user_connections[username]

    async def broadcast(self, message: str):
        for connections in self.user_connections.values():
            for connection in connections:
                try:
                    await connection.send_text(message)
                except:
                    continue

    async def broadcast_user_list(self):
        users = list(self.user_connections.keys())
        await self.broadcast(json.dumps({"type": "user_list", "users": users}))

    async def broadcast_system_message(self, message: str):
        msg = {
            "type": "system",
            "id": str(uuid.uuid4()),
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(msg))

    async def send_message(self, message_data: dict):
        msg = {
            "type": "message",
            "id": str(uuid.uuid4()),
            "username": message_data["username"],
            "content": message_data["content"],
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(msg))

# Pydantic модели
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# FastAPI приложение
app = FastAPI(title="Tandau Web Messenger")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# HTML фронтенд
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
            font-family: 'Segoe UI', sans-serif; 
            background: #0F0F1A; 
            color: white;
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
        .user-info {
            background: #252642;
            margin: 1rem;
            padding: 1rem;
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
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 2rem;
            background: #0F0F1A;
        }
        .message {
            margin-bottom: 1rem;
            display: flex;
            gap: 1rem;
        }
        .message.own { flex-direction: row-reverse; }
        .message-avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #6366F1, #8B5CF6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            flex-shrink: 0;
        }
        .message-bubble {
            background: #252642;
            padding: 1rem 1.5rem;
            border-radius: 18px;
            max-width: 60%;
        }
        .message.own .message-bubble {
            background: #6366F1;
        }
        .input-area {
            background: #1A1B2E;
            padding: 1.5rem 2rem;
            border-top: 1px solid #373755;
        }
        .input-container {
            display: flex;
            gap: 1rem;
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
        .send-button {
            background: #6366F1;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 1rem 2rem;
            cursor: pointer;
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
        .form-input {
            width: 100%;
            background: #252642;
            border: 1px solid #373755;
            border-radius: 12px;
            padding: 1rem;
            color: white;
            margin-bottom: 1rem;
            outline: none;
        }
        .auth-button {
            width: 100%;
            background: #6366F1;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 1rem;
            cursor: pointer;
            margin-bottom: 1rem;
        }
        .system-message {
            text-align: center;
            color: #A0A0B8;
            font-style: italic;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <div id="authScreen" class="auth-container">
        <div class="auth-left">
            <div style="text-align: center;">
                <h1 style="font-size: 3rem; margin-bottom: 1rem;">Tandau</h1>
                <p style="font-size: 1.2rem;">Современный веб-мессенджер</p>
            </div>
        </div>
        <div class="auth-right">
            <div class="auth-form">
                <h2 id="authTitle" style="text-align: center; margin-bottom: 2rem;">Вход в систему</h2>
                <div id="loginForm">
                    <input type="text" id="loginUsername" class="form-input" placeholder="Имя пользователя">
                    <input type="password" id="loginPassword" class="form-input" placeholder="Пароль">
                    <button class="auth-button" onclick="login()">Войти</button>
                    <div style="text-align: center; color: #6366F1; cursor: pointer;" onclick="showRegister()">
                        Нет аккаунта? Зарегистрироваться
                    </div>
                </div>
                <div id="registerForm" style="display: none;">
                    <input type="text" id="registerUsername" class="form-input" placeholder="Имя пользователя">
                    <input type="password" id="registerPassword" class="form-input" placeholder="Пароль">
                    <input type="password" id="registerConfirm" class="form-input" placeholder="Повторите пароль">
                    <button class="auth-button" onclick="register()">Зарегистрироваться</button>
                    <div style="text-align: center; color: #6366F1; cursor: pointer;" onclick="showLogin()">
                        Уже есть аккаунт? Войти
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="mainScreen" class="container" style="display: none;">
        <div class="sidebar">
            <div class="sidebar-header">
                <h1>Tandau</h1>
                <p>Web Messenger</p>
            </div>
            <div class="user-info">
                <div class="user-avatar" id="userAvatar">US</div>
                <div>
                    <h3 id="userName">User</h3>
                    <div style="color: #10B981;">🟢 В сети</div>
                </div>
            </div>
        </div>
        <div class="chat-area">
            <div class="chat-header">
                <h2>🌐 Публичный чат</h2>
            </div>
            <div class="messages-container" id="messagesContainer">
                <div class="system-message">Добро пожаловать в Tandau Messenger! 🎉</div>
            </div>
            <div class="input-area">
                <div class="input-container">
                    <input type="text" id="messageInput" class="message-input" placeholder="Введите сообщение..." disabled>
                    <button class="send-button" onclick="sendMessage()" disabled>Отправить</button>
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

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });

            if (response.ok) {
                const data = await response.json();
                token = data.access_token;
                currentUser = username;
                startWebSocket();
                showMainScreen();
            } else {
                alert('Ошибка входа');
            }
        }

        async function register() {
            const username = document.getElementById('registerUsername').value;
            const password = document.getElementById('registerPassword').value;
            const confirm = document.getElementById('registerConfirm').value;

            if (password !== confirm) {
                alert('Пароли не совпадают');
                return;
            }

            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });

            if (response.ok) {
                alert('Регистрация успешна!');
                showLogin();
            } else {
                alert('Ошибка регистрации');
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
            document.querySelector('.send-button').disabled = false;
        }

        function startWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws?token=${token}`);

            ws.onopen = () => console.log('Connected');
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'message') displayMessage(data);
                if (data.type === 'system') displaySystemMessage(data);
            };
        }

        function displayMessage(message) {
            const container = document.getElementById('messagesContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${message.username === currentUser ? 'own' : ''}`;
            messageDiv.innerHTML = `
                <div class="message-avatar">${message.username.substring(0, 2).toUpperCase()}</div>
                <div class="message-bubble">
                    <div><strong>${message.username}</strong></div>
                    <div>${message.content}</div>
                </div>
            `;
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }

        function displaySystemMessage(message) {
            const container = document.getElementById('messagesContainer');
            const div = document.createElement('div');
            div.className = 'system-message';
            div.textContent = message.content;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const content = input.value.trim();
            if (content && ws) {
                ws.send(JSON.stringify({content}));
                input.value = '';
            }
        }

        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
"""

# API endpoints
@app.get("/")
async def root():
    return HTMLResponse(HTML)

@app.post("/api/auth/register")
async def register(user: UserRegister, db: SessionLocal = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed = get_password_hash(user.password)
    db_user = User(username=user.username, password_hash=hashed)
    db.add(db_user)
    db.commit()
    return {"message": "User created"}

@app.post("/api/auth/login")
async def login(user: UserLogin, db: SessionLocal = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

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
            
            # Сохраняем в БД
            db = SessionLocal()
            db_message = Message(username=username, content=message_data["content"])
            db.add(db_message)
            db.commit()
            db.close()
            
            # Рассылаем
            await manager.send_message({"username": username, "content": message_data["content"]})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, username)
        await manager.broadcast_system_message(f"🔴 {username} покинул чат")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
