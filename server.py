# server.py — Tandau Online Server
import socket
import threading
import json
import os
import hashlib
from datetime import datetime

HOST = '0.0.0.0'
PORT = 5555

print("""
╔═══════════════════════════════════════╗
║       Tandau Messenger Server         ║
║        IP: 72.44.48.182:5555           ║
║        Админ: saltys                  ║
╚═══════════════════════════════════════╝
""")

# Папки
for dir in ['chat_images', 'chat_videos', 'voice_messages', 'user_avatars']:
    os.makedirs(dir, exist_ok=True)

# Файлы
FILES = {
    'users': 'users.json',
    'messages': 'messages.json',
    'private': 'private_messages.json',
    'channels': 'channels.json',
    'channel_msgs': 'channel_messages.json'
}

data = {}
for k, f in FILES.items():
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            data[k] = json.load(file)
    else:
        data[k] = [] if k in ['messages', 'channel_msgs'] else {}

clients = {}
lock = threading.Lock()

def broadcast(msg, exclude=None):
    with lock:
        for client in list(clients.values()):
            if client != exclude:
                try:
                    client.send(msg.encode('utf-8'))
                except:
                    pass

def handle_client(conn, addr):
    username = None
    try:
        conn.send(b'LOGIN')
        auth = conn.recv(1024).decode('utf-8')
        if not auth.startswith('LOGIN:'):
            conn.close()
            return
        username, password = auth[6:].split(':', 1)
        with lock:
            users = data['users']
            if username in users and users[username]['password'] == hashlib.sha256(password.encode()).hexdigest():
                conn.send(b'OK')
                clients[username] = conn
                broadcast(f"ONLINE:{username}")
                print(f"[+] {username} вошёл ({addr[0]})")
            else:
                conn.send(b'FAIL')
                conn.close()
                return

        while True:
            msg = conn.recv(4096).decode('utf-8')
            if not msg: break

            if msg.startswith('MSG:'):
                handle_public(msg[4:], username)
            elif msg.startswith('PRIVATE:'):
                handle_private(msg[8:], username)
            elif msg.startswith('CHANNEL:'):
                handle_channel(msg[8:], username)
            elif msg.startswith('FILE:'):
                handle_file(msg[5:], conn, username)

    except Exception as e:
        print(f"Ошибка клиента {addr}: {e}")
    finally:
        if username:
            with lock:
                clients.pop(username, None)
            broadcast(f"OFFLINE:{username}")
            print(f"[-] {username} вышел")
        conn.close()

def handle_public(text, user):
    msg = {
        'user': user,
        'message': text,
        'timestamp': datetime.now().isoformat(),
        'is_admin': data['users'].get(user, {}).get('is_admin', False),
        'id': str(int(datetime.now().timestamp() * 1000))
    }
    with lock:
        data['messages'].append(msg)
        with open(FILES['messages'], 'w', encoding='utf-8') as f:
            json.dump(data['messages'], f, ensure_ascii=False, indent=4)
    broadcast(f"MSG:{json.dumps(msg)}")

def handle_private(data_str, sender):
    recipient, text = data_str.split(':', 1)
    msg = {
        'user': sender,
        'message': text,
        'timestamp': datetime.now().isoformat(),
        'id': str(int(datetime.now().timestamp() * 1000))
    }
    key = f"{min(sender, recipient)}_{max(sender, recipient)}"
    with lock:
        if key not in data['private']:
            data['private'][key] = []
        data['private'][key].append(msg)
        with open(FILES['private'], 'w', encoding='utf-8') as f:
            json.dump(data['private'], f, ensure_ascii=False, indent=4)
    for u in [sender, recipient]:
        if u in clients:
            clients[u].send(f"PRIVATE:{u}:{json.dumps(msg)}".encode('utf-8'))

def handle_channel(data_str, user):
    parts = data_str.split(':', 2)
    if len(parts) < 3: return
    cid, action, payload = parts
    if action == 'MSG':
        with lock:
            if cid not in data['channel_msgs']:
                data['channel_msgs'][cid] = []
            msg = {
                'user': user,
                'message': payload,
                'timestamp': datetime.now().isoformat(),
                'id': str(int(datetime.now().timestamp() * 1000))
            }
            data['channel_msgs'][cid].append(msg)
            with open(FILES['channel_msgs'], 'w', encoding='utf-8') as f:
                json.dump(data['channel_msgs'], f, ensure_ascii=False, indent=4)
        subs = data['channels'].get(cid, {}).get('subscribers', [])
        for sub in subs:
            if sub in clients:
                clients[sub].send(f"CHANNEL:{cid}:MSG:{json.dumps(msg)}".encode('utf-8'))

def handle_file(info, conn, user):
    try:
        filename, size_str = info.split(':')
        size = int(size_str)
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.png','.jpg','.jpeg','.gif','.bmp']:
            path = os.path.join('chat_images', filename)
        elif ext in ['.mp4','.avi','.mov','.mkv']:
            path = os.path.join('chat_videos', filename)
        else:
            path = os.path.join('voice_messages', filename)
        with open(path, 'wb') as f:
            received = 0
            while received < size:
                data = conn.recv(4096)
                if not data: break
                f.write(data)
                received += len(data)
        broadcast(f"FILE:{filename}")
    except Exception as e:
        print(f"Ошибка файла: {e}")

# Запуск
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
print(f"[SERVER] Запущен на {HOST}:{PORT}")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()