# main.py
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse


app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Chat</title>
    </head>
    <body>
        <script>
            const ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = (event) => {
                const messages = document.getElementById('messages');
                const message = document.createElement('li');
                message.textContent = event.data;
                messages.appendChild(message);
            };
            function sendMessage() {
                const input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = '';
            }
        </script>
        <input type="text" id="messageText"/>
        <button onclick="sendMessage()">Send</button>
        <ul id="messages"></ul>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message: {data}")

# Запуск: uvicorn main:app --reload