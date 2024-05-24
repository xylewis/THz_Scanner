# coding:utf-8
import ctypes
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDesktopWidget

from qfluentwidgets import SplitFluentWindow, FluentIcon
from submainForm import submain
from linerscanForm import linerscan
from staffForm import staff
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
        self.setWindowFlags(Qt.WindowMinimizeButtonHint)

        # self.windowFlags(Qt.FramelessWindowHint)

        self.setAttribute(Qt.WA_TranslucentBackground)
        # 设置背景色
        self.bgColor = QColor(50, 50, 50, 20)

        dll_dir = "./dll"
        os.environ["PATH"] += ";" +dll_dir

        self.staff = staff(self)
        self.submain = submain(self)
        self.linerscan = linerscan(self)
        self.addSubInterface(self.staff, FluentIcon.SPEED_MEDIUM, 'sensor')
        self.addSubInterface(self.submain, FluentIcon.ASTERISK, 'singleScan')
        self.addSubInterface(self.linerscan, FluentIcon.MOVE, 'linearScan')
        self.setWindowIcon(QIcon('./dll/ico1.ico'))


    def center(self):  # 定义一个函数使得窗口居中显示
        # 获取屏幕坐标系
        screen = QDesktopWidget().screenGeometry()
        # 获取窗口坐标系
        size = self.geometry()
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
