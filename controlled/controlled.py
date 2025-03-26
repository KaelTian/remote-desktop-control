import pyautogui
import mss
import mss.tools
from flask import Flask, jsonify
import threading
import socketio
import base64
import io
from PIL import Image
import time

app = Flask(__name__)
# 创建客户端（兼容旧版本）
sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1)

SERVER_URL = "http://192.168.0.211:5000"

# 解决跨域问题（如果服务器未配置CORS）
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

@app.route('/screenshot', methods=['GET'])
def get_screenshot():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        img = Image.frombytes('RGB', (sct_img.width, sct_img.height), sct_img.rgb)
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=70)
        img_io.seek(0)
        return jsonify({
            'image': base64.b64encode(img_io.read()).decode('utf-8'),
            'width': sct_img.width,
            'height': sct_img.height
        })

@sio.event
def connect():
    print("被控端成功连接到信令服务器")
    sio.emit('register_viewer', {'name': 'Controlled PC'})

@sio.event
def connect_error(data):
    print("连接失败:", data)

@sio.event
def disconnect():
    print("与信令服务器断开连接")

@sio.on('remote_event')
def on_remote_event(data):
    try:
        event_type = data.get('type')
        if event_type == 'click':
            pyautogui.click(data['x'], data['y'], button=data.get('button', 'left'))
        elif event_type == 'move':
            pyautogui.moveTo(data['x'], data['y'])
        elif event_type == 'key':
            pyautogui.press(data['key'])
        elif event_type == 'scroll':
            pyautogui.scroll(data.get('dy', 0))
    except Exception as e:
        print("处理远程事件出错:", e)

def run_flask():
    app.run(host='0.0.0.0', port=5001, threaded=True)

def connect_to_server():
    while True:
        try:
            if not sio.connected:
                print(f"尝试连接到服务器 {SERVER_URL}...")
                sio.connect(
                    SERVER_URL,
                    transports=['websocket', 'polling'],  # 允许降级到轮询
                    namespaces=['/'],
                    wait_timeout=30  # 增加超时时间
                )
                print("成功连接到服务器")
        except Exception as e:
            print(f"连接失败: {str(e)}")
            print("5秒后重试...")
            time.sleep(5)

# 修改客户端连接部分
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # 启动连接线程
    connect_thread = threading.Thread(target=connect_to_server)
    connect_thread.daemon = True
    connect_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序正在退出...")
        if sio.connected:
            sio.disconnect()