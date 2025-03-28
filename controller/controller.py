import requests
from flask import Flask
import threading
import base64
import io
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import Canvas
import socketio
import time
import os

app = Flask(__name__)
sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1)

SERVER_URL = "http://192.168.0.211:5000"  # 修改为你的服务器地址
CONTROLLED_URL = "http://192.168.0.209:5001"  # 修改为被控端地址


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
        self.canvas.bind("<Button-3>", self.on_right_click)# 绑定右键点击事件
        self.master.bind("<Key>", self.on_key) # 所有按键事件
        self.master.bind('<Control-c>', self.on_ctrl_c)
        self.master.bind('<Control-v>', self.on_ctrl_v)
        

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
            self.photo = ImageTk.PhotoImage(img)

            if self.image_id:
                self.canvas.delete(self.image_id)

            self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.canvas.config(width=self.current_size[0], height=self.current_size[1])

        except Exception as e:
            print(f"Error updating screenshot: {e}")

        # 每100毫秒更新一次
        self.master.after(80, self.update_screenshot)

    def on_click(self, event):
        # 将坐标转换回原始屏幕尺寸
        x = event.x / self.scale
        y = event.y / self.scale

        sio.emit('control_event', {
            'type': 'click',
            'x': x,
            'y': y,
            'button': 'left'
        }, namespace='/')
    def on_right_click(self, event):
        # 将坐标转换回原始屏幕尺寸
        x = event.x / self.scale
        y = event.y / self.scale

        sio.emit('control_event', {
            'type': 'click',
            'x': x,
            'y': y,
            'button': 'right'
        }, namespace='/')

    def on_drag(self, event):
        x = event.x / self.scale
        y = event.y / self.scale

        sio.emit('control_event', {
            'type': 'move',
            'x': x,
            'y': y
        }, namespace='/')

    def on_release(self, event):
        pass

    def on_scroll(self, event):
        sio.emit('control_event', {
            'type': 'scroll',
            'delta': event.delta  # 标准化滚动量
        }, namespace='/')
    def on_ctrl_c(self, event):
        print("检测到组合键: Ctrl+C (复制)")
        return "break"  # 阻止默认行为
    
    def on_ctrl_v(self, event):
        print("检测到组合键: Ctrl+V (粘贴)")
        # 获取剪贴板中的文件路径
        file_path = self.master.clipboard_get()
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'rb') as file:
                    file_data = file.read()
                    file_name = os.path.basename(file_path)
                    sio.emit('control_event', {
                            'type': 'file',
                            'file_name': file_name,
                            'file_data': base64.b64encode(file_data).decode('utf-8')
                        }, namespace='/')
            except Exception as e:
                    print(f"发送文件时出错: {e}")
        else:
                print(f"剪贴板内容不是有效的文件路径: {file_path}")
    def on_key(self, event):
        # 更可靠的修饰键检测方法
        modifiers = []
        state = event.state
        
        # 注意：不同平台/系统下这些位掩码可能不同
        # 以下是常见Linux/Windows下的位掩码
        SHIFT_MASK = 0x0001
        CAPSLOCK_MASK = 0x0002
        CONTROL_MASK = 0x0004
        ALT_MASK = 0x0008
        NUMLOCK_MASK = 0x20000
        
        if state & SHIFT_MASK: modifiers.append("Shift")
        if state & CONTROL_MASK: modifiers.append("Ctrl")
        if state & ALT_MASK: modifiers.append("Alt")
        if state & NUMLOCK_MASK: modifiers.append("NumLock")
        if state & CAPSLOCK_MASK: modifiers.append("CapsLock")
        
        # 排除修饰键自身的事件
        is_modifier_key = event.keysym in ('Shift_L', 'Shift_R', 
                                        'Control_L', 'Control_R',
                                        'Alt_L', 'Alt_R',
                                        'Caps_Lock', 'Num_Lock')
        if is_modifier_key:
            # 这是修饰键自身被按下/释放的事件
            print(f"修饰键按下: {event.keysym}")
            return
        
        if modifiers:
            # 组合键事件 - 这里会捕获所有带修饰键的按键
            print(f"检测到组合键: {', '.join(modifiers)} + {event.keysym}")
        else:
            # 普通按键事件
            print(f"单独按键: {event.char} (keysym: {event.keysym})")
            # 处理普通按键事件
            sio.emit('control_event', {
                'type': 'key',
                'key': event.char
                }, namespace='/')

@sio.event
def connect():
    print("控制器成功连接到信令服务器")
    sio.emit('register_controller', {'name': 'Controller'})

@sio.event
def connect_error(data):
    print("连接失败:", data)

@sio.event
def disconnect():
    print("与信令服务器断开连接")    


def run_flask():
    app.run(host='0.0.0.0', port=5003)

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

if __name__ == '__main__':
    # 启动Flask服务器和SocketIO客户端
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # 启动连接线程
    connect_thread = threading.Thread(target=connect_to_server)
    connect_thread.daemon = True
    connect_thread.start()

    # 启动GUI
    root = tk.Tk()
    root.geometry("800x600")
    controller = RemoteDesktopController(root)
    root.mainloop()
    