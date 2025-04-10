from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from datetime import datetime
import json
import uuid

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, user_id: str, username: str):
        await websocket.accept()
        self.active_connections[user_id] = {
            "websocket": websocket,
            "username": username
        }

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def broadcast(self, message: dict):
        for user_id in list(self.active_connections.keys()):
            try:
                await self.active_connections[user_id]["websocket"].send_json(message)
            except:
                self.disconnect(user_id)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Принимаем соединение ПЕРВЫМ ДЕЙСТВИЕМ
    await websocket.accept()
    
    try:
        # Получаем никнейм
        username = await websocket.receive_text()
        user_id = str(uuid.uuid4())
        
        # Регистрируем подключение
        await manager.connect(websocket, user_id, username)
        
        # Уведомляем всех о новом пользователе
        await manager.broadcast({
            "system": True,
            "message": f"{username} присоединился к чату"
        })

        # Основной цикл обработки сообщений
        while True:
            data = await websocket.receive_text()
            message = {
                "username": username,
                "message": data,
                "time": datetime.now().strftime("%H:%M:%S")
            }
            await manager.broadcast(message)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast({
            "system": True,
            "message": f"{username} покинул чат"
        })

@app.get("/")
async def get():
    return HTMLResponse("""
    <html>
        <head>
            <style>
                .chat-box { max-width: 600px; margin: 0 auto; padding: 20px; }
                .message { margin: 10px 0; padding: 8px; border-radius: 5px; background: #f0f0f0; }
                .time { font-size: 0.8em; color: #666; }
                .username { font-weight: bold; color: #2c3e50; }
            </style>
        </head>
        <body>
            <div class="chat-box">
                <div id="messages"></div>
                <input type="text" id="messageInput">
                <button onclick="sendMessage()">Отправить</button>
            </div>

            <script>
                let username = localStorage.getItem('chat_username');
                if (!username) {
                    username = prompt('Введите ваш ник:');
                    localStorage.setItem('chat_username', username);
                }

                const ws = new WebSocket(`ws://${window.location.host}/ws`);
                
                // Отправляем ник при подключении
                ws.onopen = () => ws.send(username);
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    const messages = document.getElementById("messages");
                    
                    const messageDiv = document.createElement("div");
                    messageDiv.className = "message";
                    
                    if (data.system) {
                        messageDiv.innerHTML = `<em>${data.message}</em>`;
                    } else {
                        messageDiv.innerHTML = `
                            <span class="username">${data.username}</span>
                            <span class="time">[${data.time}]</span><br>
                            ${data.message}
                        `;
                    }
                    
                    messages.appendChild(messageDiv);
                    messages.scrollTop = messages.scrollHeight;
                };

                function sendMessage() {
                    const input = document.getElementById("messageInput");
                    if (input.value.trim()) {
                        ws.send(input.value);
                        input.value = "";
                    }
                }

                // Отправка по Enter
                document.getElementById("messageInput").addEventListener("keypress", (e) => {
                    if (e.key === "Enter") sendMessage();
                });
            </script>
        </body>
    </html>
    """)
