import pyautogui
import mss
import mss.tools
from flask import Flask, jsonify
import threading
import socketio
import base64
import io
from PIL import Image
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import InputController

app = Flask(__name__)
# 创建客户端（兼容旧版本）
# 修改为异步客户端
sio = socketio.AsyncClient(reconnection=True, reconnection_attempts=5, reconnection_delay=1)

SERVER_URL = "http://192.168.0.211:5000"

# 定义事件队列
# 使用 asyncio.Queue 替代 queue.Queue
event_queue = asyncio.Queue()

# 配置 Flask 日志，禁止请求日志输出到控制台
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# 创建固定大小的线程池
executor = ThreadPoolExecutor(max_workers=4)

# 在文件顶部添加
input_ctrl = InputController.InputController()


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
async def connect():
    print("被控端成功连接到信令服务器")
    await sio.emit('register_viewer', {'name': 'Controlled PC'})

@sio.event
def connect_error(data):
    print("连接失败:", data)

@sio.event
def disconnect():
    print("与信令服务器断开连接")

@sio.on('remote_event')
async def on_remote_event(data):
    try:
        # 将事件添加到异步队列
        await event_queue.put(data)
    except Exception as e:
        print("添加事件到队列出错:", e)

async def process_events():
    while True:
        try:
            # 从异步队列中获取事件
            data = await event_queue.get()
            event_type = data.get('type')
            if event_type == 'click':
                button = data.get('button', 'left')
                input_ctrl.click(int(data['x']), int(data['y']), button)
            elif event_type == 'key':
                input_ctrl.key_press(data['key'])
            elif event_type == 'move':
                input_ctrl.move(int(data['x']), int(data['y']))
            elif event_type == 'scroll':
                input_ctrl.scroll(int(data['delta']))
            elif event_type == 'text':
                input_ctrl.text(data['text'])
            event_queue.task_done()
        except Exception as e:
            print("处理远程事件出错:", e)

def run_flask():
    app.run(host='0.0.0.0', port=5001, threaded=True)

async def connect_to_server():
    while True:
        try:
            if not sio.connected:
                print(f"尝试连接到服务器 {SERVER_URL}...")
                await sio.connect(
                    SERVER_URL,
                    transports=['websocket', 'polling'],  # 允许降级到轮询
                    namespaces=['/'],
                    wait_timeout=30  # 增加超时时间
                )
                print("成功连接到服务器")
                # 等待连接保持，避免过早退出循环
                while sio.connected:
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"连接失败: {str(e)}")
            print("5秒后重试...")
            await asyncio.sleep(5)

# 处理断开连接事件
@sio.event
async def disconnect():
    print("与信令服务器断开连接，尝试重新连接...")

# 修改客户端连接部分
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    loop = asyncio.get_event_loop()
    try:
        # 启动事件处理协程
        loop.create_task(process_events())
        loop.create_task(connect_to_server())
        loop.run_forever()
    except KeyboardInterrupt:
        print("程序正在退出...")
        if sio.connected:
            loop.run_until_complete(sio.disconnect())
        loop.close()