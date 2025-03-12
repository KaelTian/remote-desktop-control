from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 存储客户端连接
controllers = {}
viewers = {}

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in controllers:
        del controllers[request.sid]
    if request.sid in viewers:
        del viewers[request.sid]
    print(f"Client disconnected: {request.sid}")

@socketio.on('register_controller')
def register_controller(data):
    controllers[request.sid] = data.get('name', 'Unknown')
    print(f"Controller registered: {request.sid}")

@socketio.on('register_viewer')
def register_viewer(data):
    viewers[request.sid] = data.get('name', 'Unknown')
    print(f"Viewer registered: {request.sid}")

@socketio.on('control_event')
def handle_control_event(data):
    # 将控制事件广播给所有查看者
    for viewer_sid in viewers:
        socketio.emit('remote_event', data, room=viewer_sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)