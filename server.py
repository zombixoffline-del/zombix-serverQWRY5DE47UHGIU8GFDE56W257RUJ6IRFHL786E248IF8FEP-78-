from flask import Flask, request
from flask_socketio import SocketIO, emit
import time
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

players = {}

@socketio.on("connect")
def on_connect():
    print("[+] connect:", request.sid, "total:", len(players))

@socketio.on("register")
def handle_register(data):
    players[request.sid] = {
        "x": 0, "y": 0, "dir": "down", "anim": "idle",
        "loc": "home", "char": "fighter", "bike": False,
        "rolling": False, "pet": None,
        "name": data.get("name", "Player"),
        "last_seen": time.time()
    }
    others = {sid: {k: v for k, v in p.items() if k != "last_seen"}
              for sid, p in players.items() if sid != request.sid}
    emit("all_players", others)

@socketio.on("state")
def handle_state(data):
    if request.sid not in players:
        return
    players[request.sid].update({
        "x": data.get("x", 0),
        "y": data.get("y", 0),
        "dir": data.get("dir", "down"),
        "anim": data.get("anim", "idle"),
        "loc": data.get("loc", "home"),
        "char": data.get("char", "fighter"),
        "bike": data.get("bike", False),
        "rolling": data.get("rolling", False),
        "pet": data.get("pet", None),
        "last_seen": time.time()
    })
    state_out = {
        "sid": request.sid,
        "x": players[request.sid]["x"],
        "y": players[request.sid]["y"],
        "dir": players[request.sid]["dir"],
        "anim": players[request.sid]["anim"],
        "loc": players[request.sid]["loc"],
        "char": players[request.sid]["char"],
        "bike": players[request.sid]["bike"],
        "rolling": players[request.sid]["rolling"],
        "pet": players[request.sid]["pet"],
        "name": players[request.sid]["name"],
    }
    emit("player_update", state_out, broadcast=True, include_self=False)

@socketio.on("chat")
def handle_chat(data):
    if request.sid not in players:
        return
    msg = str(data.get("text", ""))[:200]
    if not msg.strip():
        return
    payload = {
        "sid": request.sid,
        "name": players[request.sid].get("name", "Player"),
        "text": msg,
        "ts": time.time(),
    }
    emit("chat", payload, broadcast=True)

@socketio.on("disconnect")
def on_disconnect():
    if request.sid in players:
        del players[request.sid]
    emit("player_left", {"sid": request.sid}, broadcast=True)
    print("[-] disconnect:", request.sid, "total:", len(players))

@socketio.on("ping_alive")
def handle_ping():
    if request.sid in players:
        players[request.sid]["last_seen"] = time.time()

@app.route("/")
def index():
    return "Zombix Server. Players online: " + str(len(players))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("Server starting on port", port)
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
