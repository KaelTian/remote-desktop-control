import requests
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import base64
import io
from PIL import Image
import tkinter as tk
from tkinter import Canvas
import pyautogui

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

SERVER_URL = "http://your-server-ip:5000"  # 修改为你的服务器地址
CONTROLLED_URL = "http://controlled-pc-ip:5001"  # 修改为被控端地址

# 连接到信令服务器
socketio.connect(SERVER_URL)

class RemoteDesktopController:
    def __init__(self, master):
        self.master = master
        self.master.title("远程桌面控制器")
        
        self.canvas = Canvas(master)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.image_id = None
        self.scale = 1.0
        
        # 绑定事件
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.master.bind("<Key>", self.on_key)
        
        # 初始截图
        self.update_screenshot()
        
    def update_screenshot(self):
        try:
            response = requests.get(f"{CONTROLLED_URL}/screenshot")
            data = response.json()
            
            img_data = base64.b64decode(data['image'])
            img = Image.open(io.BytesIO(img_data))
            
            # 调整大小以适应窗口
            window_width = self.master.winfo_width()
            window_height = self.master.winfo_height()
            
            if window_width > 1 and window_height > 1:
                img.thumbnail((window_width, window_height))
            
            self.original_size = (data['width'], data['height'])
            self.current_size = img.size
            
            # 计算缩放比例
            self.scale = self.current_size[0] / self.original_size[0]
            
            # 显示图像
            self.photo = tk.PhotoImage(data=base64.b64encode(img.tobytes()))
            
            if self.image_id:
                self.canvas.delete(self.image_id)
            
            self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.canvas.config(width=self.current_size[0], height=self.current_size[1])
            
        except Exception as e:
            print(f"Error updating screenshot: {e}")
        
        # 每100毫秒更新一次
        self.master.after(100, self.update_screenshot)
    
    def on_click(self, event):
        # 将坐标转换回原始屏幕尺寸
        x = event.x / self.scale
        y = event.y / self.scale
        
        emit('control_event', {
            'type': 'click',
            'x': x,
            'y': y,
            'button': 'left'
        }, namespace='/')
    
    def on_drag(self, event):
        x = event.x / self.scale
        y = event.y / self.scale
        
        emit('control_event', {
            'type': 'move',
            'x': x,
            'y': y
        }, namespace='/')
    
    def on_release(self, event):
        pass
    
    def on_scroll(self, event):
        emit('control_event', {
            'type': 'scroll',
            'dy': event.delta // 120  # 标准化滚动量
        }, namespace='/')
    
    def on_key(self, event):
        emit('control_event', {
            'type': 'key',
            'key': event.char
        }, namespace='/')

@socketio.on('connect')
def on_connect():
    print("Connected to signaling server")
    emit('register_viewer', {'name': 'Controller'})

def run_flask():
    app.run(host='0.0.0.0', port=5003)

if __name__ == '__main__':
    # 启动Flask服务器和SocketIO客户端
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # 启动GUI
    root = tk.Tk()
    root.geometry("800x600")
    controller = RemoteDesktopController(root)
    root.mainloop()