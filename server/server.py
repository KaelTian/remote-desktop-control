import eventlet
eventlet.monkey_patch()  # 关键：必须添加事件循环补丁
from flask import Flask, request  # 添加request导入
from flask_socketio import SocketIO, emit


app = Flask(__name__)
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='eventlet')

# 存储客户端连接
controllers = {}
viewers = {}

@socketio.on('connect')
def handle_connect():
    print(f"客户端连接成功 - SID: {request.sid}")
    print(f"客户端IP: {request.remote_addr}")  # 打印客户端IP

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in controllers:
        print(f"控制器断开: {controllers[sid]}({sid})")
        del controllers[sid]
    elif sid in viewers:
        print(f"查看器断开: {viewers[sid]}({sid})")
        del viewers[sid]

@socketio.on('register_controller')
def register_controller(data):
    sid = request.sid
    controllers[sid] = {
        'name': data.get('name', '未知控制器'),
        'ip': request.remote_addr
    }
    print(f"控制器注册: {controllers[sid]['name']} | IP: {controllers[sid]['ip']}")

@socketio.on('register_viewer')
def register_viewer(data):
    sid = request.sid
    viewers[sid] = {
        'name': data.get('name', '未知查看器'),
        'ip': request.remote_addr
    }
    print(f"查看器注册: {viewers[sid]['name']} | IP: {viewers[sid]['ip']}")

@socketio.on('control_event')
def handle_control_event(data):
    sender = controllers.get(request.sid, {}).get('name', '未知控制器')
    print(f"控制事件来自 [{sender}]: {data}")
    
    # 添加广播目标检查
    if not viewers:
        print("警告：没有可用的查看器客户端")
        return
        
    socketio.emit('remote_event', data, broadcast=True)  # 改用广播方式

if __name__ == '__main__':
    print("服务器启动在 http://0.0.0.0:5000")
    socketio.run(app,
                host='0.0.0.0',
                port=5000,
                debug=True,
                use_reloader=False,
                log_output=True)  # 开启详细日志