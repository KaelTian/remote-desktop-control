# 项目名称：[Remote-Desktop-Control]

## 项目简介
[Remote-Desktop-Control] 是一个 [远程控制不同Windows系列电脑] 的 Python 小项目。它可以帮助用户 [实现远程控制其他电脑的需求]。

## 安装方法
1. 确保你的系统中已经安装了 Python [指定所需的 Python 版本，如 Python 3.6 及以上]。
2. 克隆本项目仓库到本地：
```bash
git clone https://github.com/KaelTian/remote-desktop-control.git
```
3. 进入项目目录：
```bash
cd remote-desktop-control
```
4. 安装项目依赖：
```bash
pip install -r requirements.txt 可能不全按照错误提示或者依赖库酌情安装即可
```   
5. 项目结构:
remote-desktop-control/
├── .git/
├── .gitignore
├── InputSimulator.dll
├── controlled/
│   ├── InputController.py
│   ├── controlled.py
│   └── requirements.txt
├── controller/
│   ├── controller.py
│   └── requirements.txt
└── server/
    ├── requirements.txt
    └── server.py

6. 配置项目：
- 在 `server.py` 中，根据需要配置信令服务器的 IP 地址和端口号,默认0.0.0.0。
- 在 `controlled.py` 中，根据需要配置被控制电脑的 IP 地址和端口号。
- 在 `controller.py` 中，根据需要配置信令服务器和被控制电脑的 IP 地址和端口号。

7. 运行项目：
```bash
python server.py
python controlled.py
python controller.py
```
8.备注:
- 确保被控制电脑和控制电脑处于同一局域网内。
- 确保被控制电脑和控制电脑的防火墙设置允许远程连接。
- 确保被控制电脑和控制电脑的 Python 环境相同。
- 确保被控制电脑和控制电脑的 Python 版本相同。
- InputSimulator.dll 是一个 [自己build的动态C++库]，用于模拟键盘和鼠标输入。