# _*_coding: UTF-8_*_
# 开发作者 ：TXH
# 开发时间 ：2021-09-05 14:42
# 文件名称 ：mplwidget.py
# 开发工具 ：Python 3.7 + Pycharm IDE

from PyQt5 import QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg \
    import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QThread


class MplCanvas(FigureCanvas, QThread):
    def __init__(self):
        self.fig = Figure()
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class mplwidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QtWidgets.QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
