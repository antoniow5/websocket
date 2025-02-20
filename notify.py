from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv
import requests
import hashlib
import os


app = FastAPI()

load_dotenv()

AUTH_URL = os.getenv('AUTH_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TESTING = os.getenv('TESTING', 'False').lower() == 'true'



class ConnectionManager:
    def __init__(self):
        self.active_connections = {}  

    async def connect(self, websocket: WebSocket, user_id: int):
        if str(user_id) not in self.active_connections:
            self.active_connections[str(user_id)] = []
        self.active_connections[str(user_id)].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):

        if str(user_id) in self.active_connections:
            self.active_connections[str(user_id)].remove(websocket)
            if not self.active_connections[str(user_id)]:
                del self.active_connections[str(user_id)]

    async def send_personal_message(self, message: dict, user_id: int) -> bool:
        if str(user_id) in self.active_connections:
            websockets = self.active_connections[str(user_id)]
            if websockets:
                for websocket in websockets:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        print(f"Error sending message: {e}")
                        self.disconnect(websocket, user_id)  # Handle disconnection during sending
                return True
        return False
manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, cid: str = Query(...)):
    await websocket.accept()
    user_id = None

    try:
        data = await websocket.receive_json()
        token = data.get('token')
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{AUTH_URL}?cid={cid}", headers=headers)

        if response.status_code == 200:
            user_id = response.json()['data'].get("uid")
            if not user_id:
                await websocket.close()
                return
            
            try:
                user_id = int(user_id) 
            except ValueError:
                print('Invalid user_id, closing websocket')
                await websocket.close(code=1003) 
                return

            await manager.connect(websocket, user_id)

            try:
                while True:
                    data = await websocket.receive_json() 

            except WebSocketDisconnect:
                print('WebSocket disconnected')
                manager.disconnect(websocket, user_id)

        else:
            print('Authentication failed, closing WebSocket')
            await websocket.close(code=1008)  

    except WebSocketDisconnect:
        print('WebSocket closed by client')
        if user_id:
            manager.disconnect(websocket, user_id)
            await websocket.close()
            return

    except Exception as e:
        print(f'Error occurred: {e}')
        await websocket.close(code=1011)
        return  



def get_expected_token(date: str) -> str:
    token_input = f"{CLIENT_ID}{CLIENT_SECRET}{date}"

    hash_object = hashlib.md5(token_input.encode())

    return hash_object.hexdigest()


@app.post("/notify")
async def notify(request: Request):

    data = await request.json()


    if not isinstance(data, dict) or "date" not in data or "notifications" not in data:
        return JSONResponse(content={"error": "Payload must be an object with 'date' and 'notifications' keys"}, status_code=400)

    if not isinstance(data["date"], str) or not isinstance(data["notifications"], list):
        return JSONResponse(content={"error": "'date' must be a string and 'notifications' must be an array"}, status_code=400)


    auth_header = request.headers.get("Authorization")
    date = data['date']


    expected_token = get_expected_token(date)

    if not auth_header or auth_header != f"Bearer {expected_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


    results = []
    for item in data["notifications"]:
        user_id = item.get("user_id")
        body = item.get("body")

        if not user_id or not body or type(body) != dict or type(user_id) != int:
            results.append({"user_id": user_id, "status": "failed", "error": "user_id and body are required"})
            continue

        try:
            message_sent = await manager.send_personal_message(body, user_id)
            if message_sent:
                results.append({"user_id": user_id, "status": "success_sent"})
            else:
                results.append({"user_id": user_id, "status": "success_not_connected"})
        except HTTPException as e:
            results.append({"user_id": user_id, "status": "failed", "error": str(e)})

    return JSONResponse(content=results)




@app.get("/test", response_class=HTMLResponse)
async def get_html():
    if not TESTING:
        raise HTTPException(status_code=403, detail="Testing mode is disabled")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <div>
            <label for="token">Enter token:</label>
            <input type="text" id="token" placeholder="Token" />
        </div>
        <div>
            <label for="cid">Enter CID:</label>
            <input type="text" id="cid" placeholder="CID" />
            <button onclick="connectWebSocket()">Connect</button>
        </div>

        <div>
            <p><strong>Status:</strong> <span id="status">Disconnected</span></p>
        </div>
        <div id="messages"></div>

        <script>
            let websocket = null;

            function connectWebSocket() {
                const token = document.getElementById('token').value;
                const cid = document.getElementById('cid').value;
                websocket = new WebSocket(`wss://${window.location.host}/ws?cid=${cid}`);

                websocket.onopen = function(event) {
                    document.getElementById('status').innerText = 'Connected';
                    websocket.send(JSON.stringify({ token: token }));
                };

                websocket.onclose = function(event) {
                    document.getElementById('status').innerText = 'Disconnected';
                };

                websocket.onmessage = function(event) {
                    const messagesDiv = document.getElementById('messages');
                    const newMessage = document.createElement('p');
                    newMessage.innerText = `Message from server: ${event.data}`;
                    messagesDiv.appendChild(newMessage);
                };
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
