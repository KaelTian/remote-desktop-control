import ctypes
import logging
from ctypes import wintypes

class InputController:
    def __init__(self, dll_path='./InputSimulator.dll'):
        try:
            self.lib = ctypes.CDLL(dll_path)
            
            # 设置函数参数和返回类型
            self.lib.move_mouse.argtypes = [ctypes.c_int, ctypes.c_int]
            self.lib.move_mouse.restype = wintypes.BOOL
            
            self.lib.click_mouse.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
            self.lib.click_mouse.restype = wintypes.BOOL
            
            self.lib.scroll_mouse.argtypes = [ctypes.c_int]
            self.lib.scroll_mouse.restype = wintypes.BOOL
            
            self.lib.send_key.argtypes = [ctypes.c_char, ctypes.c_int]
            self.lib.send_key.restype = wintypes.BOOL
            
            self.lib.send_key_vk.argtypes = [wintypes.BYTE, ctypes.c_int]
            self.lib.send_key_vk.restype = wintypes.BOOL
            
            self.lib.send_text.argtypes = [ctypes.c_char_p]
            self.lib.send_text.restype = wintypes.BOOL
            
        except Exception as e:
            logging.error(f"Failed to load input simulator DLL: {e}")
            raise

    def move(self, x, y):
        """移动鼠标到指定位置"""
        return bool(self.lib.move_mouse(int(x), int(y)))

    def click(self, x, y, button='left'):
        """在指定位置点击鼠标"""
        btn = 0 if button == 'left' else (1 if button == 'right' else 2)
        return bool(self.lib.click_mouse(int(x), int(y), btn))

    def scroll(self, delta):
        """滚动鼠标滚轮"""
        return bool(self.lib.scroll_mouse(int(delta)))

    def key_press(self, key):
        """按下并释放一个键"""
        if len(key) != 1:
            return self.text(key)
        return bool(self.lib.send_key(key.encode('ascii'), 2))  # 2 = KEY_PRESS

    def key_down(self, key):
        """按下键"""
        if len(key) != 1:
            return False
        return bool(self.lib.send_key(key.encode('ascii'), 0))  # 0 = KEY_DOWN

    def key_up(self, key):
        """释放键"""
        if len(key) != 1:
            return False
        return bool(self.lib.send_key(key.encode('ascii'), 1))  # 1 = KEY_UP

    def text(self, text):
        """输入文本"""
        return bool(self.lib.send_text(text.encode('utf-8')))