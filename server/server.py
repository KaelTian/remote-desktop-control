import eventlet
eventlet.monkey_patch()  # 关键：必须添加事件循环补丁
from flask import Flask, request  # 添加request导入
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='eventlet')

# 存储客户端连接
controllers = {}
viewers = {}

@socketio.on('connect')
def handle_connect():
    # 可根据需求调整日志级别，此处减少不必要的日志输出
    # print(f"客户端连接成功 - SID: {request.sid}")
    # print(f"客户端IP: {request.remote_addr}")
    pass

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in controllers:
        del controllers[sid]
    elif sid in viewers:
        del viewers[sid]

@socketio.on('register_controller')
def register_controller(data):
    sid = request.sid
    controllers[sid] = {
        'name': data.get('name', '未知控制器'),
        'ip': request.remote_addr
    }

@socketio.on('register_viewer')
def register_viewer(data):
    sid = request.sid
    viewers[sid] = {
        'name': data.get('name', '未知查看器'),
        'ip': request.remote_addr
    }

@socketio.on('control_event')
def handle_control_event(data):
    # 减少日志输出，可根据需求调整
    # sender = controllers.get(request.sid, {}).get('name', '未知控制器')
    # print(f"控制事件来自 [{sender}]: {data}")
    
    # 添加广播目标检查
    if not viewers:
        # 可根据需求调整日志级别
        # print("警告：没有可用的查看器客户端")
        return
        
    socketio.emit('remote_event', data, broadcast=True)  # 改用广播方式

if __name__ == '__main__':
    print("服务器启动在 http://0.0.0.0:5000")
    socketio.run(app,
                host='0.0.0.0',
                port=5000,
                debug=False,  # 关闭调试模式
                use_reloader=False,
                log_output=False)  # 关闭详细日志