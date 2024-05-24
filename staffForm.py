# coding:utf-8
import os
import time

import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap

from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QVBoxLayout, QStackedWidget, QLabel, \
    QFileDialog, QMessageBox
from qfluentwidgets import FluentIcon as FIF, Pivot, qrouter, SegmentedWidget, PivotItem, PushButton, setTheme, Theme, FluentIcon,\
    FlyoutView, Flyout, IndeterminateProgressBar, IndeterminateProgressRing, ProgressBar, ProgressRing, CardWidget, InfoBar, InfoBarPosition

from ui_staff import Ui_Form2

from thzsys.zmotion import Zmotion
from thzsys.control import Device, Sensor, Laser, Bias

from PyQt5.QtCore import Qt, QTimer
import numpy as np

class staff(QWidget, Ui_Form2):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.DisplayLabel.setPixmap(QPixmap('./dll/logo.svg'))
        # self.DisplayLabel.setText("(++)")

        self.powerOn = False
        self.secondCnt = 0
        self.secondCnt2 = 0
        self.qssYellow = ('ToolButton{color: black;background: rgba(6, 241, 77, 0.726);border: 1px solid rgba(0, 0, 0, 0.073);border-bottom: 1px solid rgba(0, 0, 0, 0.183);border-radius: 5px;padding: 5px 9px 6px 8px;outline: none;}')
        self.qssLight = ('ToolButton{color: black;background: rgba(255, 255, 255, 0.7);border: 1px solid rgba(0, 0, 0, 0.073);border-bottom: 1px solid rgba(0, 0, 0, 0.183);border-radius: 5px;padding: 5px 9px 6px 8px;outline: none;}')

        self.connectInit()

        # status = sys_module["sensor"].status
        # print({name: status[index] / 10 for index, name in enumerate(["humidity", "temperature"])})

    def connectInit(self):
        # region @connect
        self.btnLaunch.clicked.connect(self.linkStart)
        # self.btnLaunch.clicked.connect(self.qpdebug)

        self.timer = QTimer()
        self.timer.timeout.connect(self.watchPos)
        # endregion

    def qpdebug(self):
        pass

    def linkStart(self):
        if self.powerOn == False:
            try:
                self.control = Zmotion(host='10.168.1.11')
                self.sys_module = {
                    "system": Device(self.control.handle),
                    "sensor": Sensor(self.control.handle),
                    "laser": Laser(self.control.handle),
                    "bias": Bias(self.control.handle),
                }
                self.sensorData = self.sys_module["sensor"].status
                if self.sys_module['bias'].status and self.sys_module['laser'].status:
                    self.powerOn = True
                    self.btnLaunch.setText("POWER OFF")
                else:
                    self.sys_module['system'].toggle() # 如果系统未启动 此时启动
                    # self.sys_module['laser'].toggle()
                    # self.sys_module['bias'].toggle()
            except:
                self.createBOTTOMInfoBar('error','Error', 'Please check the connection of the device')
            else:
                self.btnLaunch.setEnabled(False)
                self.btnLaunch.setText("POWER OFF")
                self.createBOTTOMInfoBar('info',"Info", "距下一次关闭 冷却时间：10s")
                self.timer.start(1000)
        else:
            try:
                if self.sys_module['laser'] and self.sys_module['bias']:
                    self.sys_module['system'].toggle() # 如果系统已启动 此时关闭
                    # self.sys_module['laser'].toggle()
                    # self.sys_module['bias'].toggle()
                    self.btnLaunch.setEnabled(False)
                    self.btnLaunch.setText("POWER ON")
                    self.createBOTTOMInfoBar('info', "Info", "距下一次启动 冷却时间：10s")
                else:
                    pass # 如果系统未启动 跳过
            except:
                self.createBOTTOMInfoBar('error','Error', 'Please check the connection of the device')
            else:
                pass

    def watchPos(self):
        # if self.sys_module['bias'].status and self.sys_module['laser'].status:
        #     self.secondCnt += 1
        #     print(self.secondCnt,1)
        #     if self.secondCnt == 20:
        #         self.btnLaunch.setEnabled(True)
        #         self.secondCnt = 0
        #     self.btnLaser.setStyleSheet(self.qssYellow)
        #     self.powerOn = True
        # else:
        #     self.secondCnt2 += 1
        #     print(self.secondCnt,2)
        #
        #     if self.secondCnt2 == 20:
        #         self.btnLaunch.setEnabled(True)
        #         self.secondCnt2 = 0
        #     self.btnLaser.setStyleSheet(self.qssLight)
        #     self.powerOn = False
        if self.sys_module['laser'].status:
            self.btnLaser.setStyleSheet(self.qssYellow)
        else:
            self.btnLaser.setStyleSheet(self.qssLight)
        if self.sys_module['bias'].status:
            self.btnBias.setStyleSheet(self.qssYellow)
        else:
            self.btnBias.setStyleSheet(self.qssLight)

        if self.sys_module['bias'].status and self.sys_module['laser'].status:
            self.secondCnt += 1
            if self.secondCnt == 10:
                self.btnLaunch.setEnabled(True)
                self.secondCnt = 0
            self.powerOn = True
        else:
            self.secondCnt2 += 1
            if self.secondCnt2 == 10:
                self.btnLaunch.setEnabled(True)
                self.secondCnt2 = 0
            self.powerOn = False

        self.sensorData = self.sys_module["sensor"].status
        self.lineHumi.setText(str(self.sensorData[0]/10))
        self.lineTemp.setText(str(self.sensorData[1]/10))

    def createBOTTOMInfoBar(self, infoClass, title, text):
        if infoClass == 'warning':
            InfoBar.warning(
                title=self.tr(title),
                content=self.tr(text),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self
            )
        elif infoClass == 'error':
            InfoBar.error(
                title=self.tr(title),
                content=self.tr(text),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self
            )
        elif infoClass == 'success':
            InfoBar.success(
                title=self.tr(title),
                content=self.tr(text),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self
            )
        elif infoClass == 'info':
            InfoBar.info(
                title=self.tr(title),
                content=self.tr(text),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self
            )



