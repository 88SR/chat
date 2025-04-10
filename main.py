from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio

app = FastAPI()

# Класс для управления подключениями
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Отправка сообщения всем клиентам
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# WebSocket-обработчик
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Пользователь: {data}")  # Рассылка всем
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# HTML-страница
@app.get("/")
async def get():
    return HTMLResponse("""
    <html>
        <body>
            <div id="messages"></div>
            <input type="text" id="messageInput">
            <button onclick="sendMessage()">Отправить</button>
            <script>
                const ws = new WebSocket("ws://194.87.235.65/ws");
                ws.onmessage = (event) => {
                    const messages = document.getElementById("messages");
                    const message = document.createElement("div");
                    message.textContent = event.data;
                    messages.appendChild(message);
                };
                function sendMessage() {
                    const input = document.getElementById("messageInput");
                    ws.send(input.value);
                    input.value = "";
                }
            </script>
        </body>
    </html>
    """)
