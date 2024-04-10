# coding:utf-8
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow

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
        # self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))

        self.setAttribute(Qt.WA_TranslucentBackground)
        # 设置背景色
        self.bgColor = QColor(50, 50, 50, 20)

        # 调用api
        hWnd = HWND(int(self.winId()))  # 不能直接HWND(self.winId()),不然会报错
        # areoDll = cdll.LoadLibrary('D:\\FinancialMedia\\CodeCraft\\PYCHARM\\NeoTHz-py312\\Aero\\aeroDll.dll')
        # areoDll = WinDLL(os.path.join(os.path.dirname(__file__), 'aeroDll.dll'))
        # areoDll.setBlur(hWnd)

        self.submain = submain(self)
        self.linerscan = linerscan(self)
        self.addSubInterface(self.submain, FluentIcon.ASTERISK, 'singleScan')
        self.addSubInterface(self.linerscan, FluentIcon.MOVE, 'linerScan')

    def paintEvent(self, e):
        """ 绘制背景 """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.bgColor)
        painter.drawRoundedRect(self.rect(), 10, 10)


if __name__ == '__main__':
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    w = test()
    w.show()
    app.exec()
