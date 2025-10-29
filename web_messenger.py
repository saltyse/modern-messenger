from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from datetime import datetime
import json
import uuid
from typing import Dict, List
import uvicorn

# Менеджер WebSocket соединений
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.messages_history = []

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        if username not in self.active_connections:
            self.active_connections[username] = []
        self.active_connections[username].append(websocket)
        
        # Отправляем историю сообщений новому пользователю
        for msg in self.messages_history[-50:]:  # Последние 50 сообщений
            await websocket.send_text(json.dumps(msg))
        
        # Уведомляем о новом пользователе
        system_msg = {
            "type": "system",
            "id": str(uuid.uuid4()),
            "content": f"🟢 {username} присоединился к чату",
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(json.dumps(system_msg))
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

    async def send_message(self, message_data: dict):
        message = {
            "type": "message",
            "id": str(uuid.uuid4()),
            "username": message_data["username"],
            "content": message_data["content"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Сохраняем в историю
        self.messages_history.append(message)
        
        # Ограничиваем историю 100 сообщениями
        if len(self.messages_history) > 100:
            self.messages_history = self.messages_history[-100:]
        
        await self.broadcast(json.dumps(message))

# FastAPI приложение
app = FastAPI(title="Tandau Messenger")
manager = ConnectionManager()

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
                    <div style="margin: 1rem 0; font-size: 1.1rem;">🔒 Анонимное общение</div>
                    <div style="margin: 1rem 0; font-size: 1.1rem;">🌐 Реальное время</div>
                    <div style="margin: 1rem 0; font-size: 1.1rem;">👥 Публичные чаты</div>
                </div>
            </div>
        </div>
        <div class="auth-right">
            <div class="auth-form">
                <h2>Вход в чат</h2>
                <div>
                    <input type="text" id="usernameInput" class="form-input" placeholder="Введите ваше имя">
                    <button class="auth-button" onclick="login()">Войти в чат</button>
                    <div class="auth-switch" style="color: #A0A0B8;">
                        Просто введите имя и начинайте общаться!
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

        function login() {
            const username = document.getElementById('usernameInput').value.trim();
            
            if (!username) {
                alert('Пожалуйста, введите ваше имя');
                return;
            }

            if (username.length < 2) {
                alert('Имя должно быть не менее 2 символов');
                return;
            }

            currentUser = username;
            startWebSocket();
            showMainScreen();
        }

        function showMainScreen() {
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('mainScreen').style.display = 'flex';
            document.getElementById('userName').textContent = currentUser;
            document.getElementById('userAvatar').textContent = currentUser.substring(0, 2).toUpperCase();
            document.getElementById('messageInput').disabled = false;
            document.getElementById('sendButton').disabled = false;
            
            // Фокус на поле ввода
            document.getElementById('messageInput').focus();
        }

        function startWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws?username=${encodeURIComponent(currentUser)}`;
            
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
                // Пытаемся переподключиться через 3 секунды
                setTimeout(() => {
                    if (currentUser) {
                        startWebSocket();
                    }
                }, 3000);
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
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

        // Обработка Enter в поле имени пользователя
        document.getElementById('usernameInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                login();
            }
        });

        // Фокус на поле ввода имени при загрузке
        document.getElementById('usernameInput').focus();
    </script>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(HTML)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, username: str = "Anonymous"):
    await manager.connect(websocket, username)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Отправляем сообщение всем
            await manager.send_message({
                "username": username,
                "content": message_data["content"]
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, username)
        await manager.broadcast_system_message(f"🔴 {username} покинул чат")
        await manager.broadcast_user_list()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
