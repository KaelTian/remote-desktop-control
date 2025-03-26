import pyautogui
import mss
import mss.tools
from flask import Flask, request, jsonify
import threading
from flask_socketio import SocketIO, emit
import base64
import io
from PIL import Image

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

SERVER_URL = "http://192.168.0.211:5000"  # 修改为你的服务器地址

# 连接到信令服务器
socketio.connect(SERVER_URL)

@app.route('/screenshot', methods=['GET'])
def get_screenshot():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 主显示器
        sct_img = sct.grab(monitor)
        
        # 转换为PIL Image
        img = Image.frombytes('RGB', (sct_img.width, sct_img.height), sct_img.rgb)
        
        # 转换为JPEG并压缩
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=70)
        img_io.seek(0)
        
        return jsonify({
            'image': base64.b64encode(img_io.read()).decode('utf-8'),
            'width': sct_img.width,
            'height': sct_img.height
        })

@socketio.on('connect')
def on_connect():
    print("Connected to signaling server")
    emit('register_controller', {'name': 'Controlled PC'})

@socketio.on('remote_event')
def on_remote_event(data):
    event_type = data.get('type')
    
    if event_type == 'click':
        x, y = data['x'], data['y']
        button = data.get('button', 'left')
        pyautogui.click(x, y, button=button)
    elif event_type == 'move':
        x, y = data['x'], data['y']
        pyautogui.moveTo(x, y)
    elif event_type == 'key':
        key = data['key']
        pyautogui.press(key)
    elif event_type == 'scroll':
        dx, dy = data.get('dx', 0), data.get('dy', 0)
        pyautogui.scroll(dy)

def run_flask():
    app.run(host='0.0.0.0', port=5001)

if __name__ == '__main__':
    # 启动Flask服务器和SocketIO客户端
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    socketio.run(app, host='0.0.0.0', port=5002)