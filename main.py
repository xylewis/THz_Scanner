# coding:utf-8
import ctypes
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDesktopWidget

from qfluentwidgets import SplitFluentWindow, FluentIcon
from submainForm import submain
from linerscanForm import linerscan
from ctypes import cdll
from ctypes.wintypes import HWND
from PyQt5.QtGui import QColor, QPainter
from ctypes import *
import os.path


class test(SplitFluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('THz Capture')
        self.resize(int(800/0.618), 800)
        # self.windowFlags(Qt.FramelessWindowHint)
        # self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))

        self.setAttribute(Qt.WA_TranslucentBackground)
        # 设置背景色
        self.bgColor = QColor(50, 50, 50, 20)

        # 调用api
        hWnd = HWND(int(self.winId()))  # 不能直接HWND(self.winId()),不然会报错

        dll_dir = "./dll"
        os.environ["PATH"] += ";" +dll_dir
        # areoDll = ctypes.CDLL("aeroDll.dll",winmode=0)
        # areoDll = cdll.LoadLibrary('Aero/aeroDll.dll')
        # areoDll = WinDLL(os.path.join(os.path.dirname(__file__), 'aeroDll.dll'))
        # areoDll.setBlur(hWnd)

        self.submain = submain(self)
        self.linerscan = linerscan(self)
        self.addSubInterface(self.submain, FluentIcon.ASTERISK, 'singleScan')
        self.addSubInterface(self.linerscan, FluentIcon.MOVE, 'linerScan')

    # def paintEvent(self, e):
    #     """ 绘制背景 """
    #     painter = QPainter(self)
    #     painter.setRenderHint(QPainter.Antialiasing)
    #     painter.setPen(Qt.NoPen)
    #     painter.setBrush(self.bgColor)
    #     painter.drawRoundedRect(self.rect(), 10, 10)

    def center(self):  # 定义一个函数使得窗口居中显示
        # 获取屏幕坐标系
        screen = QDesktopWidget().screenGeometry()
        # 获取窗口坐标系
        size = self.geometry()
        print(size)
        newLeft = (screen.width() - size.width()) / 2
        newTop = (screen.height() - size.height()) / 2
        self.move(int(newLeft), int(newTop))


if __name__ == '__main__':
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    w = test()
    w.center()
    w.show()
    app.exec()
