# coding:utf-8
import os
import random
import time
import json
import pandas as pd
import math

import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QVBoxLayout, QStackedWidget, QLabel, \
    QFileDialog, QMessageBox
from qfluentwidgets import FluentIcon as FIF, Pivot, qrouter, SegmentedWidget, PivotItem, PushButton, setTheme, Theme, \
    FlyoutView, Flyout, IndeterminateProgressBar, IndeterminateProgressRing, ProgressBar, ProgressRing, CardWidget, InfoBar, InfoBarPosition

from ui_linerscan import Ui_Form1

from thzsys.acquisition import AcquisitionType, TerminalConfiguration, Edge
from thzsys.acquisition import DataCollection
from thzsys.delayline import DelayControl
from thzsys.zmotion import Zmotion, Axis

# from thzsignal import SignalCollection, SingleScan, LinearScan
# from delayline import DelayType
from PyQt5.QtCore import QRunnable, Qt, QThreadPool, QObject, pyqtSignal, pyqtSlot, QTimer
import numpy as np
from dataplot import DataPlot

STOP = False

class linerscan(QWidget, Ui_Form1):
    # region @property
    @property
    def xRange(self):
        return int((self.x_end + self.x_step - self.x_start) / self.x_step)
    @property
    def yRange(self):
        return int((self.y_end + self.y_step - self.y_start) / self.y_step)
    @property
    def x_sequence(self):
        return np.arange(self.x_start, self.x_end + self.x_step, self.x_step)
    @property
    def y_sequence(self):
        return np.arange(self.y_start, self.y_end + self.y_step, self.y_step)
    @property
    def y_sequence2(self):
        return np.arange(self.y_end, self.y_start - self.y_step, -self.y_step)
    # endregion

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.lastx = 0  # 获取鼠标按下时的坐标X
        self.lasty = 0  # 获取鼠标按下时的坐标Y
        self.press = False

        self.f0 = 0.75
        self.x_start = 0
        self.x_end = 1
        self.x_step = 1
        self.y_start = 0
        self.y_end = 2
        self.y_step = 1
        self.x_speed = 1
        self.y_speed = 1
        self.axisGroup = [3,4]
        self.channel = 1

        self.length = 70
        self.offset = 0
        self.iter = 1
        self.ave = 10
        self.delay = "10.168.1.16"
        self.motion = "10.168.1.11"
        self.device = "Dev1"
        self.magunit = 0
        self.phaunit = 0
        self.IsOpenExtClock = True
        self.ISAutoBak = False
        self.result = []
        self.bakPath = os.path.abspath('.') + '\\.temp'
        if not os.path.exists(self.bakPath):
            os.makedirs(self.bakPath)
        self.config = {
            "userPath": "",
            "other": ""
        }
        if not os.path.exists('config.json'):
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        self.confPath = os.path.abspath('.') + '\\config.json'

        self.togbtnClock.setChecked(False)
        self.comboDelay.addItems(["127.0.0.1", "10.168.1.16"])
        self.comboMotion.addItems(["127.0.0.1", "10.168.1.11"])
        self.comboDevice.addItems(["Dev1", "Dev2", "Dev3", "Dev4"])
        self.comboFig.addItems(["Time","Mag","Pha"])
        self.comboChannel.addItems(["Channel1","Channel2"])
        self.comboDelay.setCurrentIndex(1)
        self.comboMotion.setCurrentIndex(1)
        self.comboDevice.setCurrentIndex(0)
        self.dspinLength.setRange(0, 400 - self.dspinOffset.value())
        self.dspinLength.setValue(self.length)
        self.dspinOffset.setRange(-400, 400)
        self.dspinOffset.setValue(self.offset)
        self.spinIter.setRange(0, 1000)
        self.spinIter.setValue(self.iter)
        self.spinAve.setRange(0, 999)
        self.spinAve.setValue(self.ave)
        # self.spinMagUnit.setRange(0, 1)
        # self.spinPhaUnit.setRange(0, 1)
        self.ProgressBar.setRange(0, 1000)
        self.ProgressBar.setValue(0)
        self.btnStop.setEnabled(False)
        self.linePath.setText(self.bakPath)
        self.spinXstart.setValue(self.x_start)
        self.spinXend.setValue(self.x_end)
        self.spinXstep.setValue(self.x_step)
        self.spinYstart.setValue(self.y_start)
        self.spinYend.setValue(self.y_end)
        self.spinYstep.setValue(self.y_step)
        self.dspinXspeed.setValue(self.x_speed)
        self.dspinXspeed.setMaximum(3.0)
        self.dspinYspeed.setValue(self.y_speed)
        self.dspinYspeed.setMaximum(3.0)
        self.spinXstart.setRange(-400, 400)
        self.spinXend.setRange(-400, 400)
        self.spinYstart.setRange(-400, 400)
        self.spinYend.setRange(-400, 400)
        self.dspinFreq.setValue(self.f0)
        self.spinXstart.setRange(-15, 15)
        self.spinXend.setRange(-15, 15)
        self.spinYstart.setRange(-15, 15)
        self.spinYend.setRange(-15, 15)
        self.dspinAbsPos1.setRange(-15, 15)
        self.dspinAbsPos2.setRange(-15, 15)
        self.threadpool = QThreadPool()

        self.ProgressBar.setVisible(True)
        self.ProgressRing.setVisible(False)
        self.IndeterminateProgressBar.setVisible(False)
        self.linePath.setEnabled(False)
        self.btnSelectPath.setEnabled(False)
        self.btnOpenPath.setEnabled(False)
        self.btnLoad.setVisible(False)
        self.btnExit.setVisible(False)
        self.togbtnClock.setChecked(True)
        self.SimpleCardWidget_7.setEnabled(False)
        self.SimpleCardWidget_8.setEnabled(False)
        self.rbtnAxis34.setChecked(True)
        self.StrongBodyLabel.setText("SelectedAxis#1")
        self.StrongBodyLabel_2.setText("SelectedAxis#2")
        self.swFForNF.setChecked(True)

        self.canvas = self.widget.canvas
        self.canvas.ax1 = self.canvas.fig.add_subplot(111)
        self.canvas.ax1.get_yaxis().grid(False)
        self.canvas1 = self.widget_2.canvas
        self.canvas1.ax1 = self.canvas1.fig.add_subplot(111)
        self.canvas1.ax1.get_yaxis().grid(False)
        self.canvas2 = self.widget_3.canvas
        self.canvas2.ax1 = self.canvas2.fig.add_subplot(111)
        self.canvas2.ax1.get_yaxis().grid(False)
        self.canvas3 = self.widget_4.canvas
        self.canvas3.ax1 = self.canvas3.fig.add_subplot(111)
        self.canvas3.ax1.get_yaxis().grid(False)
        self.canvas4 = self.widget_5.canvas
        self.canvas4.ax1 = self.canvas4.fig.add_subplot(111)
        self.canvas4.ax1.get_yaxis().grid(False)

        self.canvas.ax1.clear()
        self.canvas.ax1.spines['right'].set_visible(False)
        self.canvas.ax1.spines['top'].set_visible(False)
        self.canvas.fig.patch.set_facecolor("None")
        self.canvas.ax1.patch.set_alpha(0)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.canvas1.ax1.clear()
        self.canvas1.ax1.spines['right'].set_visible(False)
        self.canvas1.ax1.spines['top'].set_visible(False)
        self.canvas1.fig.patch.set_facecolor("None")
        self.canvas1.ax1.patch.set_alpha(0)
        self.canvas1.setStyleSheet("background-color:transparent;")
        self.canvas2.ax1.clear()
        self.canvas2.ax1.spines['right'].set_visible(False)
        self.canvas2.ax1.spines['top'].set_visible(False)
        self.canvas2.fig.patch.set_facecolor("None")
        self.canvas2.ax1.patch.set_alpha(0)
        self.canvas2.setStyleSheet("background-color:transparent;")
        self.canvas3.ax1.clear()
        self.canvas3.ax1.spines['right'].set_visible(False)
        self.canvas3.ax1.spines['top'].set_visible(False)
        self.canvas3.fig.patch.set_facecolor("None")
        self.canvas3.ax1.patch.set_alpha(0)
        self.canvas3.setStyleSheet("background-color:transparent;")
        self.canvas4.ax1.clear()
        self.canvas4.ax1.spines['right'].set_visible(False)
        self.canvas4.ax1.spines['top'].set_visible(False)
        self.canvas4.fig.patch.set_facecolor("None")
        self.canvas4.ax1.patch.set_alpha(0)
        self.canvas4.setStyleSheet("background-color:transparent;")
        self.canvas.ax1.xaxis.grid()
        self.canvas.ax1.yaxis.grid()
        self.canvas1.ax1.xaxis.grid()
        self.canvas1.ax1.yaxis.grid()
        self.canvas2.ax1.xaxis.grid()
        self.canvas2.ax1.yaxis.grid()
        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_move)
        self.canvas.mpl_connect('scroll_event', self.call_back)
        self.canvas1.mpl_connect("button_press_event", self.on_press1)
        self.canvas1.mpl_connect("button_release_event", self.on_release1)
        self.canvas1.mpl_connect("motion_notify_event", self.on_move1)
        self.canvas1.mpl_connect('scroll_event', self.call_back1)
        self.canvas2.mpl_connect("button_press_event", self.on_press2)
        self.canvas2.mpl_connect("button_release_event", self.on_release2)
        self.canvas2.mpl_connect("motion_notify_event", self.on_move2)
        self.canvas2.mpl_connect('scroll_event', self.call_back2)

        self.segSetting = PivotItem('Motion')
        self.segOperation = PivotItem('AxisScan')
        self.segAxis = PivotItem('DelayScan')
        self.segDev = PivotItem('Dev')
        self.SegmentedWidget.insertWidget(0, 'Motion', self.segSetting, onClick=lambda: self.stackedWidget.setCurrentIndex(4))
        self.SegmentedWidget.insertWidget(1, 'AxisScan', self.segOperation, onClick=lambda: self.stackedWidget.setCurrentIndex(3))
        self.SegmentedWidget.insertWidget(2, 'DelayScan', self.segAxis, onClick=lambda: self.stackedWidget.setCurrentIndex(0))
        # self.SegmentedWidget.insertWidget(3, 'Dev', self.segDev, onClick=lambda: self.stackedWidget.setCurrentIndex(2))
        self.SegmentedWidget.setItemFontSize(12)
        self.SegmentedWidget.setCurrentItem('Motion')
        self.stackedWidget.setCurrentIndex(4)

        # self.segScan = PivotItem('Outline')
        self.segRuntime = PivotItem('Runtime')
        self.segAmp = PivotItem('Magnitude')
        self.segPha = PivotItem('Phase')
        # self.SegmentedWidget_2.insertWidget(0, 'Outline', self.segScan, onClick=lambda: self.stackedWidget_2.setCurrentIndex(1))
        self.SegmentedWidget_2.insertWidget(0, 'Runtime', self.segRuntime, onClick=lambda: self.stackedWidget_2.setCurrentIndex(0))
        self.SegmentedWidget_2.insertWidget(1, 'Magnitude', self.segAmp, onClick=lambda: self.stackedWidget_2.setCurrentIndex(2))
        self.SegmentedWidget_2.insertWidget(2, 'Phase', self.segPha, onClick=lambda: self.stackedWidget_2.setCurrentIndex(3))
        self.SegmentedWidget_2.setItemFontSize(12)
        self.SegmentedWidget_2.setCurrentItem('Runtime')
        self.stackedWidget_2.setCurrentIndex(0)

        self.connectInit()

        self.btnStart.setIcon(FIF.POWER_BUTTON)
        self.btnGo1.setIcon(FIF.ACCEPT_MEDIUM)
        self.btnGo2.setIcon(FIF.ACCEPT_MEDIUM)
        self.btnR1.setIcon(FIF.RIGHT_ARROW)
        self.btnR2.setIcon(FIF.RIGHT_ARROW)
        self.btnL1.setIcon(FIF.LEFT_ARROW)
        self.btnL2.setIcon(FIF.LEFT_ARROW)
        self.btnSta1.setIcon(FIF.PAUSE_BOLD)
        self.btnSta2.setIcon(FIF.PAUSE_BOLD)

    def connectInit(self):
        # region @connect
        self.btnLink.clicked.connect(self.linkStart)
        self.btnStart.clicked.connect(self.oh_no)
        self.btnStart.clicked.connect(lambda: self.btnHome.setEnabled(False))
        # self.btnStart.clicked.connect(self.qpdebug)
        self.btnStart.clicked.connect(self.progress_busy)
        # self.btnStart.clicked.connect(self.startScan)
        self.btnStop.clicked.connect(self.stopThread)
        self.btnSave.clicked.connect(self.saveResult)
        self.btnLoad.clicked.connect(self.loadResult)
        self.dspinLength.valueChanged.connect(self.lengthAssert)
        self.dspinOffset.valueChanged.connect(self.offsetAssert)
        self.spinIter.valueChanged.connect(self.iterAssert)
        self.spinAve.valueChanged.connect(self.aveAssert)
        self.swMag.checkedChanged.connect(self.magUnitAssert)
        self.swPha.checkedChanged.connect(self.phaUnitAssert)
        self.swFForNF.checkedChanged.connect(self.NForFFAssert)
        self.comboDelay.currentIndexChanged.connect(self.ipChange)
        self.comboMotion.currentIndexChanged.connect(self.ipChange)
        self.comboDevice.currentIndexChanged.connect(self.ipChange)
        self.comboDelay.currentTextChanged.connect(self.ipChange)
        self.comboMotion.currentTextChanged.connect(self.ipChange)
        self.comboDevice.currentTextChanged.connect(self.ipChange)
        self.comboChannel.currentIndexChanged.connect(self.ipChange)
        self.spinXstart.valueChanged.connect(self.XstartAssert)
        self.spinXend.valueChanged.connect(self.XendAssert)
        self.spinXstep.valueChanged.connect(self.XstepAssert)
        self.spinYstart.valueChanged.connect(self.YstartAssert)
        self.spinYend.valueChanged.connect(self.YendAssert)
        self.spinYstep.valueChanged.connect(self.YstepAssert)
        self.dspinXspeed.valueChanged.connect(self.XspeedAssert)
        self.dspinYspeed.valueChanged.connect(self.YspeedAssert)
        self.dspinFreq.valueChanged.connect(self.FreqAssert)
        self.btnOpenPath.clicked.connect(self.OpenPath)
        self.btnSelectPath.clicked.connect(self.SelectPath)
        self.togbtnAutoBak.clicked.connect(self.AutoBakEnable)
        self.dspinXmin.valueChanged.connect(self.axesChange)
        self.dspinXmax.valueChanged.connect(self.axesChange)
        self.dspinYmin.valueChanged.connect(self.axesChange)
        self.dspinYmax.valueChanged.connect(self.axesChange)
        self.btnVanilla.clicked.connect(self.axesReset)

        self.togbtnClock.clicked.connect(self.clockEnable)
        self.SwitchButton.checkedChanged.connect(self.themeChange)
        self.btnGo1.clicked.connect(self.axisMove)
        self.btnGo2.clicked.connect(self.axisMove)
        self.btnL1.clicked.connect(self.axisMove)
        self.btnL2.clicked.connect(self.axisMove)
        self.btnR1.clicked.connect(self.axisMove)
        self.btnR2.clicked.connect(self.axisMove)
        self.btnCancelMotion.clicked.connect(self.axisMove)
        self.btnHome.clicked.connect(self.axisMove)
        self.btnSlot.clicked.connect(self.savePara)
        self.btnRestore.clicked.connect(self.loadPara)

        self.timer = QTimer()
        self.timer.timeout.connect(self.watchPos)
        # endregion

    def linkStart(self):
        try:
            if self.rbtnAxis12.isChecked():
                self.axisGroup = [1, 2]
                self.StrongBodyLabel_2.setText("Axis1 Motion (mm/deg)")
                self.StrongBodyLabel.setText("Axis2 Motion (mm/deg)")
            elif self.rbtnAxis34.isChecked():
                self.axisGroup = [3, 4]
                self.StrongBodyLabel_2.setText("Axis3 Motion (mm/deg)")
                self.StrongBodyLabel.setText("Axis4 Motion (mm/deg)")
            elif self.rbtnAxis56.isChecked():
                self.axisGroup = [5, 6]
                self.StrongBodyLabel_2.setText("Axis5 Motion (mm/deg)")
                self.StrongBodyLabel.setText("Axis6 Motion (mm/deg)")
            self.control = Zmotion(self.motion)
            self.axis = [Axis(self.control.handle, i) for i in self.axisGroup]
            self.axis[0].speed = self.dspinXspeed.value()
            self.axis[1].speed = self.dspinYspeed.value()
        except:
            self.createTopRightInfoBar('error','Error', 'Please check the connection of the device')
        else:
            self.createTopRightInfoBar('success',"Info", "AxisGroup"+str(self.axisGroup)+"Link Success")
            self.SimpleCardWidget_7.setEnabled(True)
            self.SimpleCardWidget_8.setEnabled(True)
            self.timer.start(1000)

    def axisMove(self):
        try:
            self.axis[0].speed = self.x_speed
            self.axis[1].speed = self.y_speed
        except:
            self.createTopRightInfoBar('warning','Warning', 'Please check the connection of the device')
        else:
            if self.btnGo1.isHover:
                if self.dspinAbsPos1.value() <= 15 and self.dspinAbsPos1.value() >= -15 or not self.swFForNF.isChecked():
                    self.axis[0].move(self.dspinAbsPos1.value())
                else:
                    self.createTopRightInfoBar('warning', 'Warning', 'Please check the motor limit')
            elif self.btnL1.isHover:
                if self.axis[0].dpos - self.dspinStep1.value() >= -15 or not self.swFForNF.isChecked():
                    self.axis[0].step(-self.dspinStep1.value())
                else:
                    self.createTopRightInfoBar('warning', 'Warning', 'Please check the motor limit')
            elif self.btnR1.isHover:
                if self.axis[0].dpos + self.dspinStep1.value() <= 15 or not self.swFForNF.isChecked():
                    self.axis[0].step(self.dspinStep1.value())
                else:
                    self.createTopRightInfoBar('warning', 'Warning', 'Please check the motor limit')
            elif self.btnGo2.isHover:
                if self.dspinAbsPos2.value() <= 15 and self.dspinAbsPos2.value() >= -15 or not self.swFForNF.isChecked():
                    self.axis[1].move(self.dspinAbsPos2.value())
                else:
                    self.createTopRightInfoBar('warning', 'Warning', 'Please check the motor limit')
            elif self.btnL2.isHover:
                if self.axis[1].dpos - self.dspinStep2.value() >= -15 or not self.swFForNF.isChecked():
                    self.axis[1].step(-self.dspinStep2.value())
                else:
                    self.createTopRightInfoBar('warning', 'Warning', 'Please check the motor limit')
            elif self.btnR2.isHover:
                if self.axis[1].dpos + self.dspinStep2.value() <= 15 or not self.swFForNF.isChecked():
                    self.axis[1].step(self.dspinStep2.value())
                else:
                    self.createTopRightInfoBar('warning', 'Warning', 'Please check the motor limit')
            elif self.btnCancelMotion.isHover:
                self.axis[0].cancel()
                self.axis[1].cancel()
                self.createTopRightInfoBar('info', 'Info', 'All axes have been stopped')
            elif self.btnHome.isHover:
                self.axis[0].move(0)
                self.axis[1].move(0)

    def watchPos(self):
        if self.axis[0].idle == 0:
            self.btnSta1.setIcon(FIF.PLAY_SOLID)
            self.btnSta1.setText("Runing")
        else:
            self.btnSta1.setIcon(FIF.PAUSE_BOLD)
            self.btnSta1.setText("Standby")
        if self.axis[1].idle == 0:
            self.btnSta2.setIcon(FIF.PLAY_SOLID)
            self.btnSta2.setText("Runing")
        else:
            self.btnSta2.setIcon(FIF.PAUSE_BOLD)
            self.btnSta2.setText("Standby")
        self.labelPos1.setText(str(round(self.axis[0].dpos,2)))
        self.labelPos2.setText(str(round(self.axis[1].dpos,2)))

    def savePara(self):
        json_path = self.confPath
        # 检查文件是否存在
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"文件 {json_path} 不存在。")

            # 尝试读取JSON文件
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)  # 解析JSON文件为Python字典

            data['f0'] = self.f0
            data['x_start'] = self.x_start
            data['x_end'] = self.x_end
            data['x_step'] = self.x_step
            data['y_start'] = self.y_start
            data['y_end'] = self.y_end
            data['y_step'] = self.y_step

            data['length'] = self.length
            data['offset'] = self.offset
            data['iter'] = self.iter
            data['ave'] = self.ave
            data['channel'] = self.channel

            if self.rbtnAxis12.isChecked():
                self.axisGroup = [1, 2]
            elif self.rbtnAxis34.isChecked():
                self.axisGroup = [3, 4]
            elif self.rbtnAxis56.isChecked():
                self.axisGroup = [5, 6]
            data['axisGroup'] = self.axisGroup
            data['x_speed'] = self.x_speed
            data['y_speed'] = self.y_speed
            data['FForNF'] = 1 if self.swFForNF.isChecked() else 0

            # 将修改后的字典写回JSON文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"文件 {json_path} 修改成功。")

        except json.JSONDecodeError:
            raise ValueError(f"文件 {json_path} 不是有效的JSON文件。")

        except IOError:
            raise IOError(f"读取或写入文件 {json_path} 时发生错误。")

    def loadPara(self):
        json_path = self.confPath
        # 检查文件是否存在
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"文件 {json_path} 不存在。")
            # 尝试读取JSON文件
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)  # 解析JSON文件为Python字典

                self.f0 = data['f0']
                self.dspinFreq.setValue(self.f0)
                self.x_start = data['x_start']
                self.spinXstart.setValue(self.x_start)
                self.x_end = data['x_end']
                self.spinXend.setValue(self.x_end)
                self.x_step = data['x_step']
                self.spinXstep.setValue(self.x_step)
                self.y_start = data['y_start']
                self.spinYstart.setValue(self.y_start)
                self.y_end = data['y_end']
                self.spinYend.setValue(self.y_end)
                self.y_step = data['y_step']
                self.spinYstep.setValue(self.y_step)

                self.length = data['length']
                self.dspinLength.setValue(self.length)
                self.offset = data['offset']
                self.dspinOffset.setValue(self.offset)
                self.iter = data['iter']
                self.spinIter.setValue(self.iter)
                self.ave = data['ave']
                self.spinAve.setValue(self.ave)
                self.channel = data['channel']
                self.comboChannel.setCurrentIndex(self.channel - 1)

                self.axisGroup = data['axisGroup']

                if self.axisGroup == [3, 4]:
                    self.rbtnAxis34.setChecked(True)
                elif self.axisGroup == [1, 2]:
                    self.rbtnAxis12.setChecked(True)
                else:
                    self.rbtnAxis56.setChecked(True)

                self.x_speed = data['x_speed']
                self.dspinXspeed.setValue(self.x_speed)
                self.y_speed = data['y_speed']
                self.dspinYspeed.setValue(self.y_speed)
                if data['FForNF'] == 1:
                    self.swFForNF.setChecked(True)
                else:
                    self.swFForNF.setChecked(False)

        except json.JSONDecodeError:
            raise ValueError(f"文件 {json_path} 不是有效的JSON文件。")

        except IOError:
            raise IOError(f"读取文件 {json_path} 时发生错误。")

    def createTopRightInfoBar(self, infoClass, title, text):
        if infoClass == 'warning':
            InfoBar.warning(
                title=self.tr(title),
                content=self.tr(text),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
        elif infoClass == 'error':
            InfoBar.error(
                title=self.tr(title),
                content=self.tr(text),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
        elif infoClass == 'success':
            InfoBar.success(
                title=self.tr(title),
                content=self.tr(text),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
        elif infoClass == 'info':
            InfoBar.info(
                title=self.tr(title),
                content=self.tr(text),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )

    def qpdebug(self):
        im = self.canvas3.ax1.pcolormesh(np.array([[1,2,1],[1,2,4]]), shading='nearest', cmap='gist_heat',vmin=-180, vmax=180)
        cax = self.canvas3.ax1.inset_axes([1.04, 0, 0.04, 1], transform=self.canvas3.ax1.transAxes)
        cbar = self.canvas3.fig.colorbar(im, cax=cax,ticks=[-180,0,180])
        self.canvas3.ax1.set_title('Amplitude Diagram')
        self.canvas3.ax1.set_xlabel('scanXPos(mm)')
        self.canvas3.ax1.set_ylabel('scanYPos(mm)')
        self.canvas3.ax1.set_aspect('equal')
        self.canvas3.ax1.minorticks_on()

        self.canvas3.fig.tight_layout()
        self.canvas3.draw()

        # self.canvas1.ax1.clear()
        # self.canvas1.fig.tight_layout()
        # self.canvas1.draw()

    def startScan(self):
        # for j in range(5,5 + int(self.ypos.value())):
        #     for i in range(5,5 + int(self.xpos.value())):
        #         if self.findChild(ProgressRing, u'PR_' + str(i)+ str(j)) is not None:
        #             self.findChild(ProgressRing, u'PR_' + str(i)+ str(j)).setVisible(False)
        #             self.findChild(IndeterminateProgressRing, u'IPR_' + str(i)+ str(j)).setVisible(False)

        vly = QtWidgets.QVBoxLayout(self.CardWidget_2)
        vly.setObjectName("vly")

        for j in range(5,5 + self.yRange):
            hly = QtWidgets.QHBoxLayout()
            hly.setObjectName(u'hly_' + str(j))
            vly.insertLayout(0, hly)

            for i in range(5,5 + self.xRange):
                PR = ProgressRing(self.CardWidget_2)
                PR.setMinimumSize(QtCore.QSize(20, 20))
                PR.setMaximumSize(QtCore.QSize(20, 20))
                PR.setMaximum(100)
                PR.setProperty("value", 0)
                PR.setStrokeWidth(4)
                PR.setObjectName(u'PR_' + str(i)+ str(j))

                IPR = IndeterminateProgressRing(self.CardWidget_2)
                IPR.setMinimumSize(QtCore.QSize(20, 20))
                IPR.setMaximumSize(QtCore.QSize(20, 20))
                IPR.setMaximum(100)
                IPR.setProperty("value", 0)
                IPR.setStrokeWidth(4)
                IPR.setObjectName(u'IPR_' + str(i)+ str(j))

                vlym=QtWidgets.QVBoxLayout()
                vlym.setObjectName(u'vlym_' + str(i) + str(j))

                vlym.addWidget(PR)
                vlym.addWidget(IPR)
                hly.addLayout(vlym)
                self.findChild(ProgressRing, u'PR_' + str(i)+ str(j)).setVisible(True)
                self.findChild(IndeterminateProgressRing, u'IPR_' + str(i)+ str(j)).setVisible(False)
        self.findChild(ProgressRing, u'PR_' + str(5+0) + str(5+0)).setVisible(False)
        self.findChild(IndeterminateProgressRing, u'IPR_' + str(5+0) + str(5+0)).setVisible(True)

    def spotCtrl(self, i, j ):
        self.findChild(IndeterminateProgressRing, u'IPR_' + str(5 + i) + str(5 + j)).setVisible(False)
        self.findChild(ProgressRing, u'PR_' + str(5 + i) + str(5 + j)).setVisible(True)
        self.findChild(ProgressRing, u'PR_' + str(5 + i) + str(5 + j)).setValue(100)
        if i + 1 < self.xRange:
            self.findChild(ProgressRing, u'PR_' + str(5 + i+1) + str(5 + j)).setVisible(False)
            self.findChild(IndeterminateProgressRing, u'IPR_' + str(5 + i+1) + str(5 + j)).setVisible(True)
        else:
            if  j + 1 < self.yRange:
                self.findChild(ProgressRing, u'PR_' + str(5 + i-i) + str(5 + j+1)).setVisible(False)
                self.findChild(IndeterminateProgressRing, u'IPR_' + str(5 + i-i) + str(5 + j+1)).setVisible(True)

    def oh_no(self):
        worker = Worker(self.execute_this_fn,
                        self.iter,
                        self.ave,
                        self.length,
                        self.offset,
                        self.delay,
                        self.motion,
                        self.IsOpenExtClock,
                        self.f0,
                        self.x_start,
                        self.x_end,
                        self.x_step,
                        self.y_start,
                        self.y_end,
                        self.y_step,
                        self.x_speed,
                        self.y_speed,
                        self.device,
                        self.axisGroup,
                        self.channel
                        )
        worker.signals.result.connect(lambda: self.getResult(worker.result))
        # worker.signals.finished.connect(self.thread_complete)
        worker.signals.render_ave.connect(
            lambda: self.render_ave_ding(worker.data_buffer))
        worker.signals.render_iter.connect(lambda: self.render_iter_ding(worker.data))
        worker.signals.progress.connect(lambda: self.progress_ding(worker.progress_count))
        worker.signals.progress2.connect(lambda: self.progress_ding_2(worker.progress_total))
        worker.signals.stop.connect(lambda: self.stopThreadAfter())
        worker.signals.youCanStop.connect(lambda: self.btnStop.setEnabled(True))
        # worker.signals.axIdle.connect(lambda: self.spotCtrl(worker.axIndex[0], worker.axIndex[1]))
        # Execute
        self.threadpool.start(worker)

    def themeChange(self):
        if self.iter == 13 and self.ave == 9:
            self.btnReset.clicked.connect(self.showSBRFlyout)
        if self.SwitchButton.isChecked():
            setTheme(Theme.DARK)
            self.setStyleSheet('Demo{background: rgb(32, 32, 32)}')
            # self.canvas.ax1.clear()
            # self.canvas.ax1.spines['right'].set_visible(False)
            # self.canvas.ax1.spines['top'].set_visible(False)
            # self.canvas.fig.patch.set_facecolor("None")
            # self.canvas.ax1.patch.set_alpha(0)
            # self.canvas.setStyleSheet("background-color:transparent;")
            # self.canvas1.ax1.clear()
            # self.canvas1.ax1.spines['right'].set_visible(False)
            # self.canvas1.ax1.spines['top'].set_visible(False)
            # self.canvas1.fig.patch.set_facecolor("None")
            # self.canvas1.ax1.patch.set_alpha(0)
            # self.canvas1.setStyleSheet("background-color:transparent;")
            # self.canvas2.ax1.clear()
            # self.canvas2.ax1.spines['right'].set_visible(False)
            # self.canvas2.ax1.spines['top'].set_visible(False)
            # self.canvas2.fig.patch.set_facecolor("None")
            # self.canvas2.ax1.patch.set_alpha(0)
            # self.canvas2.setStyleSheet("background-color:transparent;")

        else:
            setTheme(Theme.LIGHT)
            # self.canvas.ax1.clear()
            # self.canvas.fig.patch.set_facecolor('white')
            # self.canvas.ax1.patch.set_facecolor('white')
            # self.canvas.draw()
            # self.canvas1.ax1.clear()
            # self.canvas1.fig.patch.set_facecolor('white')
            # self.canvas1.ax1.patch.set_facecolor('white')
            # self.canvas1.draw()
            # self.canvas2.ax1.clear()
            # self.canvas2.fig.patch.set_facecolor('white')
            # self.canvas2.ax1.patch.set_facecolor('white')
            # self.canvas2.draw()

    def getResult(self, result):
        # self.canvas3.ax1.clear()
        # self.canvas4.ax1.clear()
        # X, Y = np.meshgrid(self.x_sequence,self.y_sequence2)
        # f_seq_array = 10 ** (result.amp[:,0:len(result.f)] / 20)
        # temp1 = np.where((result.f-self.f0) == min(abs(result.f-self.f0)))
        # temp2 = np.where((result.f-self.f0) == -min(abs(result.f-self.f0)))
        # if temp1:
        #     fN=temp1[0][0]
        # elif temp2:
        #     fN=temp2[0][0]
        # f0_seq = (f_seq_array[:, fN])
        # f0_plane = f0_seq.reshape(len(self.y_sequence), len(self.x_sequence))
        # self.canvas3.ax1.pcolor(X, Y, np.abs(f0_plane))
        # self.canvas4.ax1.pcolor(X, Y, np.angle(f0_plane))
        # self.canvas3.fig.tight_layout()
        # self.canvas3.draw()
        # self.canvas4.fig.tight_layout()
        # self.canvas4.draw()
        self.btnHome.setEnabled(True)

    def execute_this_fn(self):
        pass

    def progress_busy(self):
        self.ProgressBar.setVisible(False)
        self.IndeterminateProgressBar.setVisible(True)

    def progress_ding(self, progress_count):
        # self.ui.lineEditScanNo.setText(str(progress_count))
        self.ProgressBar.setVisible(True)
        # self.ProgressRing.setVisible(True)
        # self.ProgressRing.setTextVisible(True)

        self.IndeterminateProgressBar.setVisible(False)
        self.ProgressBar.setValue(progress_count)
        # self.ProgressRing.setValue(progress_count)

    def progress_ding_2(self, progress_total):
        self.ProgressBar.setRange(0, progress_total)
        # self.ProgressRing.setRange(0, progress_total)

    def render_ave_ding(self, data_buffer):
        self.canvas.ax1.clear()
        self.canvas1.ax1.clear()
        self.canvas2.ax1.clear()
        if self.SwitchButton.isChecked():
            self.canvas.ax1.patch.set_alpha(0)
            self.canvas.setStyleSheet("background-color:transparent;")
            # self.setStyleSheet('Demo{background: rgb(32, 32, 32)}')
            # self.canvas.ax1.patch.set_facecolor('#323232')
            # self.canvas1.ax1.patch.set_facecolor('#323232')
            # self.canvas2.ax1.patch.set_facecolor('#323232')
        self.canvas.ax1.plot(np.array([i * 0.02 for i in range(0, 5000)]), data_buffer)

        # if self.swMag.isChecked():
        #     # self.canvas1.ax1.plot(10, 10 ** (data.amp[-1][0:len(data.f)] / 20))
        #     pass
        # else:
        #     self.canvas1.ax1.plot(np.fft.fftfreq(5000), abs(f_data)[0:5000])

        # if self.swPha.isChecked():
        #     self.canvas2.ax1.plot(10, data.pha[-1][0:len(data.f)] / 180 * np.pi)
        # else:
        #     self.canvas2.ax1.plot(10, data.pha[-1][0:len(data.f)])

        self.canvas.fig.tight_layout()
        self.canvas.draw()
        self.canvas1.fig.tight_layout()
        self.canvas1.draw()
        self.canvas2.fig.tight_layout()
        self.canvas2.draw()

    def render_iter_ding(self, data):
        self.canvas.ax1.clear()
        self.canvas1.ax1.clear()
        self.canvas2.ax1.clear()
        self.canvas3.ax1.clear()
        self.canvas4.ax1.clear()

        if self.SwitchButton.isChecked():
            self.canvas.ax1.patch.set_facecolor('#323232')
            self.canvas1.ax1.patch.set_facecolor('#323232')
            self.canvas2.ax1.patch.set_facecolor('#323232')

        self.canvas.ax1.plot(data.t, data.mat[-1])
        self.canvas.ax1.set_title("T-domain"+'  '+'[Vpp: %.2f]' % (np.max(data.mat[-1]) - np.min(data.mat[-1])))
        self.canvas.ax1.set_xlabel("Time(ps)")
        self.canvas.ax1.set_ylabel("Voltage")

        self.canvas1.ax1.set_title("Mag")
        self.canvas1.ax1.set_xlabel("Frequency(THz)")
        self.canvas2.ax1.set_title("Pha")
        self.canvas2.ax1.set_xlabel("Frequency(THz)")

        if self.swMag.isChecked():
            self.canvas1.ax1.plot(data.f, 10 ** (data.amp[-1][0:len(data.f)] / 20))
            self.canvas1.ax1.xaxis.set_ticks(np.arange(0, 11, 5))
            self.canvas1.ax1.set_ylabel("Magnitude(a.u)")
        else:
            self.canvas1.ax1.plot(data.f, data.amp[-1][0:len(data.f)])
            self.canvas1.ax1.xaxis.set_ticks(np.arange(0, 11, 5))
            self.canvas1.ax1.set_ylabel("Magnitude(dB)")

        if self.swPha.isChecked():
            self.canvas2.ax1.plot(data.f, np.unwrap(data.pha[-1][0:len(data.f)], period = 360))
            self.canvas2.ax1.set_ylabel("Phase(deg)")
        else:
            self.canvas2.ax1.plot(data.f, np.unwrap(data.pha[-1][0:len(data.f)], period = 360) / 180 * np.pi)
            self.canvas2.ax1.set_ylabel("Phase(rad)")

        # 近场
        if self.swFForNF.isChecked():
            X, Y = np.meshgrid(self.x_sequence, self.y_sequence)
            f_seq_array = 10 ** (data.amp[:,0:len(data.f)] / 20)
            f_seq_array1 = (data.pha[:,0:len(data.f)])
            temp1 = np.where((data.f-self.f0) == min(abs(data.f-self.f0)))
            temp2 = np.where((data.f-self.f0) == -min(abs(data.f-self.f0)))
            if len(temp1[0]):
                fN=temp1[0][0]
            elif len(temp2[0]):
                fN=temp2[0][0]
            else:
                print("no found")
            f0_seq = (f_seq_array[:, fN])
            f0_seq1 = (f_seq_array1[:, fN])

            if len(f0_seq) < len(self.y_sequence) * len(self.x_sequence):
                f0_seq = np.pad(f0_seq,(0,len(self.y_sequence) * len(self.x_sequence)-len(f0_seq)),'constant',constant_values=(0,0))
                f0_seq1 = np.pad(f0_seq1,(0,len(self.y_sequence) * len(self.x_sequence)-len(f0_seq1)),'constant',constant_values=(0,0))

            f0_plane = f0_seq.reshape(len(self.y_sequence), len(self.x_sequence))
            f0_plane1 = f0_seq1.reshape(len(self.y_sequence), len(self.x_sequence))
            if len(f0_seq) == len(self.y_sequence) * len(self.x_sequence):
                np.savetxt('幅值场图.txt',f0_plane)
                np.savetxt('相位场图.txt',f0_plane1)

            im = self.canvas3.ax1.pcolormesh(X, Y, np.abs(f0_plane), shading='nearest', cmap='gist_heat')
            cax = self.canvas3.ax1.inset_axes([1.04, 0, 0.04, 1], transform=self.canvas3.ax1.transAxes)
            cbar = self.canvas3.fig.colorbar(im, cax=cax)
            self.canvas3.ax1.set_title('Amplitude Diagram')
            self.canvas3.ax1.set_xlabel('scanXPos(mm)')
            self.canvas3.ax1.set_ylabel('scanYPos(mm)')
            self.canvas3.ax1.set_aspect('equal')
            self.canvas3.ax1.minorticks_on()

            im1 = self.canvas4.ax1.pcolormesh(X, Y, np.abs(f0_plane1), shading='nearest', cmap='jet', vmin=-180, vmax=180)
            cax1 = self.canvas4.ax1.inset_axes([1.04, 0, 0.04, 1], transform=self.canvas4.ax1.transAxes)
            cbar1 = self.canvas4.fig.colorbar(im1, cax=cax1, ticks=[-180, 0, 180])
            self.canvas4.ax1.set_title('Phase Diagram')
            self.canvas4.ax1.set_xlabel('scanXPos(mm)')
            self.canvas4.ax1.set_ylabel('scanYPos(mm)')
            self.canvas4.ax1.set_aspect('equal')
            self.canvas4.ax1.minorticks_on()
        #远场
        else:
            f_seq_array = 10 ** (data.amp[:, 0:len(data.f)] / 20)
            f_seq_array1 = (data.pha[:, 0:len(data.f)])
            temp1 = np.where((data.f - 3) == min(abs(data.f - 3)))
            temp2 = np.where((data.f - 3) == -min(abs(data.f - 3)))
            if len(temp1[0]):
                fN = temp1[0][0]
            elif len(temp2[0]):
                fN = temp2[0][0]
            else:
                print("no found")
            f0_seq = (f_seq_array[:, 0:fN])
            f0_seq1 = (f_seq_array1[:, 0:fN])
            if len(f0_seq) < max(len(self.y_sequence),len(self.x_sequence)):
                f0_seq = np.vstack((f0_seq, np.zeros((len(self.y_sequence) * len(self.x_sequence) - len(f0_seq), f0_seq.shape[1]))))
                f0_seq1 = np.vstack((f0_seq1, np.zeros((len(self.y_sequence) * len(self.x_sequence) - len(f0_seq1), f0_seq1.shape[1]))))
            theta = self.y_sequence if self.xRange == 1 else self.x_sequence
            freq = data.f[0:fN]
            X, Y = np.meshgrid(theta, freq)
            im = self.canvas3.ax1.pcolormesh(X, Y, np.abs(f0_seq.T), shading='nearest', cmap='gist_heat')
            cax = self.canvas3.ax1.inset_axes([1.04, 0, 0.04, 1], transform=self.canvas3.ax1.transAxes)
            cbar = self.canvas3.fig.colorbar(im, cax=cax)
            self.canvas3.ax1.set_title('Amplitude Diagram')
            self.canvas3.ax1.set_xlabel('scanXPos(deg)')
            self.canvas3.ax1.set_ylabel('freqency(THz)')
            self.canvas3.ax1.set_aspect('equal')
            self.canvas3.ax1.minorticks_on()
            im1 = self.canvas4.ax1.pcolormesh(X, Y, np.abs(f0_seq1.T), shading='nearest', cmap='jet')
            cax1 = self.canvas4.ax1.inset_axes([1.04, 0, 0.04, 1], transform=self.canvas4.ax1.transAxes)
            cbar1 = self.canvas4.fig.colorbar(im1, cax=cax1)
            self.canvas4.ax1.set_title('Phase Diagram')
            self.canvas4.ax1.set_xlabel('scanXPos(deg)')
            self.canvas4.ax1.set_ylabel('freqency(THz)')
            self.canvas4.ax1.set_aspect('equal')
            self.canvas4.ax1.minorticks_on()

        self.canvas.ax1.xaxis.grid()
        self.canvas.ax1.yaxis.grid()
        self.canvas1.ax1.xaxis.grid()
        self.canvas1.ax1.yaxis.grid()
        self.canvas2.ax1.xaxis.grid()
        self.canvas2.ax1.yaxis.grid()

        self.canvas.fig.tight_layout()
        self.canvas1.fig.tight_layout()
        self.canvas2.fig.tight_layout()
        self.canvas3.fig.tight_layout()
        self.canvas4.fig.tight_layout()
        self.canvas.draw()
        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()
        self.canvas4.draw()

        self.xylim = [self.canvas.ax1.get_xlim(),self.canvas.ax1.get_ylim()]
        self.xylim1 = [self.canvas1.ax1.get_xlim(),self.canvas1.ax1.get_ylim()]
        self.xylim2 = [self.canvas2.ax1.get_xlim(),self.canvas2.ax1.get_ylim()]

        if self.xRange * self.yRange == len(data.mat):
            self.result = data.mat
            self.filename = time.strftime("%Y%m%d_%H%M", time.localtime()) + ".txt"
            np.savetxt(
                os.path.abspath('.') + '\\.temp' + '/' + self.filename,
                data.mat,
                fmt="%.6f", delimiter='\t')


    def stopThread(self):
        global STOP
        STOP = True

    def stopThreadAfter(self):
        """
        停止运动轴的线程后进行相关的界面和状态更新。

        全局变量 STOP 被用来控制线程的停止状态。此函数尝试取消两个轴的运动，
        如果成功，则更新用户界面，包括进度条重置、删除旧的卡片视图、创建新的卡片视图、
        清除画布内容以及更新按钮状态。如果在尝试取消轴运动时发生异常，
        则会显示警告信息。

        参数:
        self - 对象自身的引用。

        返回值:
        无
        """
        global STOP  # 访问全局变量STOP以控制线程

        try:
            self.axis[0].cancel()  # 尝试取消第一个轴的运动
            self.axis[1].cancel()  # 尝试取消第二个轴的运动
        except:
            # 如果在取消轴运动时发生异常，显示警告信息
            self.createTopRightInfoBar('warning', 'Warning', '请连接电机再测试停止功能')
        else:
            # 如果成功取消轴的运动，进行下面的界面和状态更新
            self.ProgressBar.setValue(0)  # 重置进度条
            self.CardWidget_2.deleteLater()  # 删除当前的卡片视图
            self.CardWidget_2 = CardWidget(self.page_10)  # 创建新的卡片视图
            self.CardWidget_2.setObjectName("CardWidget_2")
            self.verticalLayout_12.addWidget(self.CardWidget_2)  # 将新卡片视图添加到布局中
            self.canvas.ax1.clear()  # 清除第一个画布的内容
            self.canvas1.ax1.clear()  # 清除第二个画布的内容
            self.canvas2.ax1.clear()  # 清除第三个画布的内容
            if self.SwitchButton.isChecked():
                # 如果切换按钮处于选中状态，设置画布背景色为灰色
                self.canvas.ax1.patch.set_facecolor('#323232')
                self.canvas1.ax1.patch.set_facecolor('#323232')
                self.canvas2.ax1.patch.set_facecolor('#323232')
            self.canvas.draw()  # 更新第一个画布的显示
            self.canvas1.draw()  # 更新第二个画布的显示
            self.canvas2.draw()  # 更新第三个画布的显示
            STOP = False  # 重置停止标志为False
            self.btnStop.setEnabled(False)  # 禁用停止按钮
            self.btnHome.setEnabled(True)  # 启用回家按钮

    def saveResult(self):
        if self.result:
            openPath = readJson('userPath', self.confPath)
            if os.path.exists(openPath):
                pass
            else:
                openPath = self.bakPath
            Sig = np.array(self.result)
            t = np.arange(0, self.length, 0.02).reshape([1, Sig.shape[1]])
            Sig = np.concatenate((t, Sig), axis=0)
            filedir = QFileDialog.getExistingDirectory(self, "选择输出目录文件", openPath)
            if self.xRange == 1 and self.yRange != 1 and not self.swFForNF.isChecked():
                labelDeg = ['ts'] + [f'{i:.3f}' + 'deg' for i in self.y_sequence]
                df = pd.DataFrame(Sig.T, columns=labelDeg)
                df.to_csv(filedir + '\\' + self.filename.split('.')[0] + '.csv', index=False)
            elif self.xRange != 1 and self.yRange == 1 and not self.swFForNF.isChecked():
                labelDeg = ['ts'] + [f'{i:.3f}' + 'deg' for i in self.x_sequence]
                df = pd.DataFrame(Sig.T, columns=labelDeg)
                df.to_csv(filedir + '\\' + self.filename.split('.')[0] + '.csv', index=False)
            elif self.swFForNF.isChecked():
                labelMm = ['ts'] + ['[' + f'{j:.3f}'+ ',' +f'{i:.3f}'+']mm' for j in self.y_sequence for i in self.x_sequence]
                df = pd.DataFrame(Sig.T, columns=labelMm)
                df.to_csv(filedir + '\\' + self.filename.split('.')[0] + '.csv', index=False)
            # header = '\t'.join(['Iter{}'.format(i + 1) for i in range(Sig.shape[0] - 1)]) + '\t' +'ts' '\n'
            # with open(filedir + '\\' + self.filename, 'w') as f:
            #     f.write(header)
            #     np.savetxt(f, Sig.T, fmt="%.6f", delimiter='\t')
            if filedir == openPath:
                pass
            else:
                modifyJson("userPath", filedir, self.confPath)
        else:
            self.createTopRightInfoBar('warning','Warning', 'Please scan first or wait for the scan to complete(>_<)')

    def loadResult(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                  "Text Files(*.txt)")
        if fileName == '':
            pass
        else:
            Sig = np.loadtxt(fileName, delimiter=" ")
            self.canvas.ax1.clear()
            self.canvas.ax1.plot(Sig[0], Sig[1])
            # self.canvas.fig.suptitle("T-Domain")
            # self.canvas.fig.supxlabel("Time (ps)")
            # self.canvas.fig.supylabel("Voltage (V)")
            self.canvas.fig.tight_layout()
            self.canvas.draw()

            self.canvas1.ax1.clear()
            self.canvas1.ax1.plot(Sig[2][0:np.argwhere(Sig[2] == 0)[1][0]],
                                  Sig[3][0:np.argwhere(Sig[3] == 0)[0][0]])
            # self.canvas.fig.suptitle("T-Domain")
            # self.canvas.fig.supxlabel("Time (ps)")
            # self.canvas.fig.supylabel("Voltage (V)")
            self.canvas1.fig.tight_layout()
            self.canvas1.draw()

    def ipChange(self):
        self.delay = self.comboDelay.currentText()
        self.motion = self.comboMotion.currentText()
        self.device = self.comboDevice.currentText()
        self.channel = self.comboChannel.currentIndex() + 1
        print(self.delay)
        print(self.motion)
        print(self.device)
    def clockEnable(self):
        if self.togbtnClock.isChecked():
            self.IsOpenExtClock = True
        else:
            self.IsOpenExtClock = False
    def lengthAssert(self):
        self.dspinLength.setRange(0, 400 - self.dspinOffset.value())
        self.length = self.dspinLength.value()

    def offsetAssert(self):
        self.dspinLength.setRange(0, 400 - self.dspinOffset.value())
        self.offset = self.dspinOffset.value()

    def iterAssert(self):
        self.iter = self.spinIter.value()

    def aveAssert(self):
        self.ave = self.spinAve.value()

    def magUnitAssert(self):
        if self.swMag.isChecked():
            pass
        else:
            pass

    def phaUnitAssert(self):
        if self.swPha.isChecked():
            pass
        else:
            pass

    def NForFFAssert(self):
        if self.swFForNF.isChecked():
            self.spinXstart.setRange(-15,15)
            self.spinXend.setRange(-15,15)
            self.spinYstart.setRange(-15,15)
            self.spinYend.setRange(-15,15)
            self.dspinAbsPos1.setRange(-15,15)
            self.dspinAbsPos2.setRange(-15,15)
        else:
            self.spinXstart.setRange(-99,99)
            self.spinXend.setRange(-99,99)
            self.spinYstart.setRange(-99,99)
            self.spinYend.setRange(-99,99)
            self.dspinAbsPos1.setRange(-99,99)
            self.dspinAbsPos2.setRange(-99,99)


    def XstartAssert(self):
        self.x_start = self.spinXstart.value()
    def XendAssert(self):
        self.x_end = self.spinXend.value()
    def XstepAssert(self):
        self.x_step = self.spinXstep.value()
    def YstartAssert(self):
        self.y_start = self.spinYstart.value()
    def YendAssert(self):
        self.y_end = self.spinYend.value()
    def YstepAssert(self):
        self.y_step = self.spinYstep.value()
    def XspeedAssert(self):
        try:
            self.x_speed = self.dspinXspeed.value()
            self.axis[0].speed = self.dspinXspeed.value()
        except:
            QMessageBox.information(self, 'Error', 'Please check the connection of the device')
        else:
            print(self.axis[0].speed)
    def YspeedAssert(self):
        try:
            self.y_speed = self.dspinYspeed.value()
            self.axis[1].speed = self.dspinYspeed.value()
        except:
            QMessageBox.information(self, 'Error', 'Please check the connection of the device')
        else:
            print(self.axis[1].speed)
    def FreqAssert(self):
        self.f0 = self.dspinFreq.value()

    def OpenPath(self):
        # self.bakPath = self.bakPath.replace('/', '\\')
        # os.system('copy ' + os.path.abspath('.') + '\\.temp ' + self.bakPath)
        os.startfile(self.bakPath)

    def SelectPath(self):
        self.bakPath = QFileDialog.getExistingDirectory(self, "选择自动备份目录", os.getcwd())
        self.linePath.setText(self.bakPath)

    def AutoBakEnable(self):
        if self.togbtnAutoBak.isChecked():
            self.ISAutoBak = True
            self.linePath.setEnabled(True)
            self.btnSelectPath.setEnabled(True)
            self.btnOpenPath.setEnabled(True)
        else:
            self.linePath.setEnabled(False)
            self.btnSelectPath.setEnabled(False)
            self.btnOpenPath.setEnabled(False)

    def showSBRFlyout(self):
        view = FlyoutView(
            title='杰洛·齐贝林',
            content="触网而起的网球会落到哪一侧，谁也无法知晓。\n如果那种时刻到来，我希望「女神」是存在的。\n这样的话，不管网球落到哪一边，我都会坦然接受的吧。\n表达敬意吧，表达出敬意，然后迈向回旋的另一个全新阶段！",
            image='resource/SBR.jpg',
            isClosable=True
            # image='resource/yiku.gif',
        )

        # add button to view
        button = PushButton('Action')
        button.setFixedWidth(120)
        view.addWidget(button, align=Qt.AlignRight)

        # adjust layout (optional)
        view.widgetLayout.insertSpacing(1, 5)
        view.widgetLayout.addSpacing(5)

        # show view
        w = Flyout.make(view, self.btnReset, self)
        view.closed.connect(w.close)

    def on_press(self, event):
        # axtemp = event.inaxes
        if event.inaxes:  # 判断鼠标是否在axes内
            if event.button == 1:  # 判断按下的是否为鼠标左键1（右键是3）
                self.press = True
                self.lastx = event.xdata  # 获取鼠标按下时的坐标X
                self.lasty = event.ydata  # 获取鼠标按下时的坐标Y
            # if event.button == 2:
            #     axtemp.set_xlim(1, 2)
            #     # axtemp.set_ylim(-10, 0)
            #     self.canvas.draw_idle()  # 绘图动作实时反映在图像上
    def on_move(self, event):
        axtemp = event.inaxes
        if axtemp:
            if self.press:  # 按下状态
                # 计算新的坐标原点并移动
                # 获取当前最新鼠标坐标与按下时坐标的差值
                x = event.xdata - self.lastx
                y = event.ydata - self.lasty
                # 获取当前原点和最大点的4个位置
                x_min, x_max = axtemp.get_xlim()
                y_min, y_max = axtemp.get_ylim()

                x_min = x_min - x
                x_max = x_max - x
                y_min = y_min - y
                y_max = y_max - y

                axtemp.set_xlim(x_min, x_max)
                axtemp.set_ylim(y_min, y_max)
                self.canvas.draw_idle()  # 绘图动作实时反映在图像上
    def on_release(self, event):
        if self.press:
            self.press = False  # 鼠标松开，结束移
    def call_back(self, event):
        axtemp = event.inaxes
        x_min, x_max = axtemp.get_xlim()
        y_min, y_max = axtemp.get_ylim()
        xfanwei = (x_max - x_min) / 10
        yfanwei = (y_max - y_min) / 10
        if event.button == 'up':
            axtemp.set(xlim=(x_min + xfanwei, x_max - xfanwei))
            axtemp.set(ylim=(y_min + yfanwei, y_max - yfanwei))
        elif event.button == 'down':
            axtemp.set(xlim=(x_min - xfanwei, x_max + xfanwei))
            axtemp.set(ylim=(y_min - yfanwei, y_max + yfanwei))
        self.canvas.draw_idle()  # 绘图动作实时反映在图像上
    def on_press1(self, event):
        if event.inaxes:  # 判断鼠标是否在axes内
            if event.button == 1:  # 判断按下的是否为鼠标左键1（右键是3）
                self.press = True
                self.lastx = event.xdata  # 获取鼠标按下时的坐标X
                self.lasty = event.ydata  # 获取鼠标按下时的坐标Y
    def on_move1(self, event):
        axtemp = event.inaxes
        if axtemp:
            if self.press:  # 按下状态
                # 计算新的坐标原点并移动
                # 获取当前最新鼠标坐标与按下时坐标的差值
                x = event.xdata - self.lastx
                y = event.ydata - self.lasty
                # 获取当前原点和最大点的4个位置
                x_min, x_max = axtemp.get_xlim()
                y_min, y_max = axtemp.get_ylim()

                x_min = x_min - x
                x_max = x_max - x
                y_min = y_min - y
                y_max = y_max - y

                axtemp.set_xlim(x_min, x_max)
                axtemp.set_ylim(y_min, y_max)
                self.canvas1.draw_idle()  # 绘图动作实时反映在图像上
    def on_release1(self, event):
        if self.press:
            self.press = False  # 鼠标松开，结束移
    def call_back1(self, event):
        axtemp = event.inaxes
        x_min, x_max = axtemp.get_xlim()
        y_min, y_max = axtemp.get_ylim()
        xfanwei = (x_max - x_min) / 10
        yfanwei = (y_max - y_min) / 10
        if event.button == 'up':
            axtemp.set(xlim=(x_min + xfanwei, x_max - xfanwei))
            axtemp.set(ylim=(y_min + yfanwei, y_max - yfanwei))
        elif event.button == 'down':
            axtemp.set(xlim=(x_min - xfanwei, x_max + xfanwei))
            axtemp.set(ylim=(y_min - yfanwei, y_max + yfanwei))
        self.canvas1.draw_idle()  # 绘图动作实时反映在图像上
    def on_press2(self, event):
        if event.inaxes:  # 判断鼠标是否在axes内
            if event.button == 1:  # 判断按下的是否为鼠标左键1（右键是3）
                self.press = True
                self.lastx = event.xdata  # 获取鼠标按下时的坐标X
                self.lasty = event.ydata  # 获取鼠标按下时的坐标Y
    def on_move2(self, event):
        axtemp = event.inaxes
        if axtemp:
            if self.press:  # 按下状态
                # 计算新的坐标原点并移动
                # 获取当前最新鼠标坐标与按下时坐标的差值
                x = event.xdata - self.lastx
                y = event.ydata - self.lasty
                # 获取当前原点和最大点的4个位置
                x_min, x_max = axtemp.get_xlim()
                y_min, y_max = axtemp.get_ylim()

                x_min = x_min - x
                x_max = x_max - x
                y_min = y_min - y
                y_max = y_max - y

                axtemp.set_xlim(x_min, x_max)
                axtemp.set_ylim(y_min, y_max)
                self.canvas2.draw_idle()  # 绘图动作实时反映在图像上
    def on_release2(self, event):
        if self.press:
            self.press = False  # 鼠标松开，结束移
    def call_back2(self, event):
        axtemp = event.inaxes
        x_min, x_max = axtemp.get_xlim()
        y_min, y_max = axtemp.get_ylim()
        xfanwei = (x_max - x_min) / 10
        yfanwei = (y_max - y_min) / 10
        if event.button == 'up':
            axtemp.set(xlim=(x_min + xfanwei, x_max - xfanwei))
            axtemp.set(ylim=(y_min + yfanwei, y_max - yfanwei))
        elif event.button == 'down':
            axtemp.set(xlim=(x_min - xfanwei, x_max + xfanwei))
            axtemp.set(ylim=(y_min - yfanwei, y_max + yfanwei))
        self.canvas2.draw_idle()  # 绘图动作实时反映在图像上
    def axesChange(self):
        if self.comboFig.currentIndex() == 0:
            # if self.dspinXmin.value() > self.dspinXmax.value():
            #     self.dspinXmax.setValue(self.dspinXmin.value() + 10)
            # if self.dspinYmin.value() > self.dspinYmax.value():
            #     self.dspinYmax.setValue(self.dspinYmin.value() + 10)
            self.canvas.ax1.set_xlim(self.dspinXmin.value(),self.dspinXmax.value())
            self.canvas.ax1.set_ylim(self.dspinYmin.value(),self.dspinYmax.value())
            self.canvas.draw_idle()  # 绘图动作实时反映在图像上
        elif self.comboFig.currentIndex() == 1:
            # if self.dspinXmin.value() > self.dspinXmax.value():
            #     self.dspinXmax.setValue(self.dspinXmin.value() + 10)
            # if self.dspinYmin.value() > self.dspinYmax.value():
            #     self.dspinYmax.setValue(self.dspinYmin.value() + 10)
            self.canvas1.ax1.set_xlim(self.dspinXmin.value(),self.dspinXmax.value())
            self.canvas1.ax1.set_ylim(self.dspinYmin.value(),self.dspinYmax.value())
            self.canvas1.draw_idle()  # 绘图动作实时反映在图像上
        elif self.comboFig.currentIndex() == 2:
            # if self.dspinXmin.value() > self.dspinXmax.value():
            #     self.dspinXmax.setValue(self.dspinXmin.value() + 10)
            # if self.dspinYmin.value() > self.dspinYmax.value():
            #     self.dspinYmax.setValue(self.dspinYmin.value() + 10)
            self.canvas2.ax1.set_xlim(self.dspinXmin.value(),self.dspinXmax.value())
            self.canvas2.ax1.set_ylim(self.dspinYmin.value(),self.dspinYmax.value())
            self.canvas2.draw_idle()  # 绘图动作实时反映在图像上
    def axesReset(self):
        try:
            self.xylim
        except:
            pass
        else:
            if self.comboFig.currentIndex() == 0:
                self.dspinXmin.setValue(self.xylim[0][0])
                self.dspinXmax.setValue(self.xylim[0][1])
                self.dspinYmin.setValue(self.xylim[1][0])
                self.dspinYmax.setValue(self.xylim[1][1])
            elif self.comboFig.currentIndex() == 1:
                self.dspinXmin.setValue(self.xylim1[0][0])
                self.dspinXmax.setValue(self.xylim1[0][1])
                self.dspinYmin.setValue(self.xylim1[1][0])
                self.dspinYmax.setValue(self.xylim1[1][1])
            elif self.comboFig.currentIndex() == 2:
                self.dspinXmin.setValue(self.xylim2[0][0])
                self.dspinXmax.setValue(self.xylim2[0][1])
                self.dspinYmin.setValue(self.xylim2[1][0])
                self.dspinYmax.setValue(self.xylim2[1][1])
            self.canvas.ax1.set_xlim(self.xylim[0][0], self.xylim[0][1])
            self.canvas.ax1.set_ylim(self.xylim[1][0], self.xylim[1][1])
            self.canvas.draw_idle()  # 绘图动作实时反映在图像上
            self.canvas1.ax1.set_xlim(self.xylim1[0][0], self.xylim1[0][1])
            self.canvas1.ax1.set_ylim(self.xylim1[1][0], self.xylim1[1][1])
            self.canvas1.draw_idle()  # 绘图动作实时反映在图像上
            self.canvas2.ax1.set_xlim(self.xylim2[0][0], self.xylim2[0][1])
            self.canvas2.ax1.set_ylim(self.xylim2[1][0], self.xylim2[1][1])
            self.canvas2.draw_idle()  # 绘图动作实时反映在图像上


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    render_ave = pyqtSignal(object)
    render_iter = pyqtSignal(object)
    progress = pyqtSignal(int)
    progress2 = pyqtSignal(int)
    stop = pyqtSignal()
    youCanStop = pyqtSignal()

    axIdle  =   pyqtSignal(int,int)


class Worker(QRunnable):
    @property
    def progress_total(self):
        return int((self.x_end + self.x_step - self.x_start) / self.x_step) * int((self.y_end + self.y_step - self.y_start) / self.y_step)

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.iter = args[0]
        self.ave = args[1]
        self.length = args[2]
        self.offset = args[3]
        self.delay = args[4]
        self.motion = args[5]
        self.IsOpenExtClock = args[6]
        self.f0 = args[7]
        self.x_start = args[8]
        self.x_end = args[9]
        self.x_step = args[10]
        self.y_start = args[11]
        self.y_end = args[12]
        self.y_step = args[13]
        self.xspeed = args[14]
        self.yspeed = args[15]
        self.device = args[16]
        self.axisGroup = args[17]
        self.channel = args[18]
        self.read_count = 1
        self.data = DataPlot
        self.data_buffer = []
        self.result = DataPlot
        self.progress_count = 0
        self.axIndex= [0,0]
        self.axBusyIndex= [0,0]
        # self.progress_total = 0
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        global STOP
        control = Zmotion(self.motion)
        axis = [Axis(control.handle, i) for i in self.axisGroup]
        if self.delay == "127.0.0.1":
            delay = DelayControl(self.delay, 5002)
        else:
            delay = DelayControl(self.delay)
        acquisition = DataCollection(self.device)
        print('dev')
        # Delay line set
        delay.offset = self.offset  # Sampling Offset (ps)
        delay.length = self.length  # Sampling Length (ps)
        delay.interval = 0.02  # Sampling Interval (ps)
        delay.iteration = self.ave  # Iteration Average
        f0 = self.f0
        x_start = self.x_start
        x_end =self.x_end
        x_step =self.x_step
        y_start = self.y_start
        y_end =self.y_end
        y_step =self.y_step
        axis[0].speed = self.xspeed
        axis[1].speed = self.yspeed

        x_sequence = np.arange(self.x_start, self.x_end + self.x_step, self.x_step)
        y_sequence = np.arange(self.y_start, self.y_end + self.y_step, self.y_step)
        y_sequence2 = np.arange(self.y_end, self.y_start - self.y_step, -self.y_step)

        # Begin scan plane
        axis[0].move(x_start)
        axis[1].move(y_start)
        axis[1].step(-y_step)

        self.data = DataPlot(delay.interval, n=2 ** math.ceil(math.log2(self.length / 0.02)))
        self.data.t = self.length
        self.data.f = 10

        print('init')
        for j in range(len(y_sequence)):
            self.signals.progress2.emit(self.progress_total)
            axis[1].step(y_step)
            axis[0].move(x_start)
            for i in range(len(x_sequence)):
                time.sleep(0.2)
                if STOP is not True:
                    while not all([ax.idle for ax in axis]):
                        if STOP is not True:
                            time.sleep(1)
                        else:
                            break
                    if STOP is not True:
                        self.signals.youCanStop.emit()
                        self.axIndex = [i,j]
                        print('single')
                        self.data_buffer = main_task(delay, acquisition, self.IsOpenExtClock, self.channel)
                        self.signals.axIdle.emit(self.axIndex[0],self.axIndex[1])
                        self.data.mat.append(self.data_buffer)
                        self.data.fft()
                        self.signals.render_iter.emit(self.data)
                        self.signals.progress.emit(self.progress_count)
                        self.progress_count += 1

                        # self.result = [scan.data.t, scan.data.mat[-1][0:len(scan.data.t)],
                        #                scan.data.f, scan.data.amp[-1][0:len(scan.data.f)]]
                        # self.signals.result.emit(self.result)
                        axis[0].step(x_step)
                else:
                    break
        if STOP is not True:
            self.result=self.data
            self.signals.result.emit(self.result)
            print('DONE')
        else:
            self.signals.stop.emit()

        # for n in range(0, self.iter):
        #     self.signals.progress2.emit(self.progress_total)
        #     self.signals.youCanStop.emit()
        #     if STOP is not True:
        #         self.data_buffer = main_task(delay, acquisition)
        #         self.signals.render_ave.emit(self.data_buffer)
        #         self.signals.progress.emit(self.progress_count)
        #         if self.progress_total > 100 and self.progress_count % 10 == 0:
        #             np.savetxt(os.path.abspath('.') + '\\.temp' + f"/{self.progress_count / 10}.txt",
        #                        self.data_buffer,
        #                        fmt="%.6f")
        #         self.progress_count += self.ave
        #     else:
        #         break
        #     if STOP is not True:
        #         # scan.data.mat.append(np.mean(np.array(self.data_buffer), axis=0))
        #         # scan.data.fft()
        #         # self.data = scan.data
        #         # self.signals.render_iter.emit(self.data)
        #         # self.result = [scan.data.t, scan.data.mat[-1][0:len(scan.data.t)],
        #         #                scan.data.f, scan.data.amp[-1][0:len(scan.data.f)]]
        #         # self.signals.result.emit(self.result)
        #         self.read_count = 1
        #         # self.data_buffer = []
        #     else:
        #         break
        # if STOP is True:
        #     self.read_count = 1
        #     self.data_buffer = []
        #     self.signals.stop.emit()


async def task_init(delay: DelayControl, acquisition: DataCollection, IsOpenExtClock, channel):

    acquisition.channel = channel
    if IsOpenExtClock:
        acquisition.terminal = 3
    acquisition.edge = Edge.RISING
    acquisition.mode = AcquisitionType.FINITE
    acquisition.coupling = TerminalConfiguration.DEFAULT
    await delay.update()


async def task_exec(delay: DelayControl, acquisition: DataCollection):

    del acquisition.buffer
    num_of_sample = int(delay.length / delay.interval)
    acquisition.config(num_of_sample * delay.iteration, num_of_sample)
    await delay.init()
    print("<Info> Task Initialized.")
    await delay.start()
    acquisition.start()
    print("<Info> Task Started.")
    await delay.run()
    for _ in range(delay.iteration):
        acquisition.read(num_of_sample)
    acquisition.stop()
    print("<Info> Task Stopped.")
    acquisition.close()
    delay.close()
    print("<Info> Task Completed.")


def main_task(delay, acquisition, IsOpenExtClock, channel):
    import asyncio
    asyncio.run(task_init(delay, acquisition, IsOpenExtClock, channel))
    asyncio.run(task_exec(delay, acquisition))
    return np.mean(acquisition.buffer, axis=0)

def readJson(key_name, json_path):
    # 检查文件是否存在
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"文件 {json_path} 不存在。")

        # 尝试读取JSON文件
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)  # 解析JSON文件为Python字典

            # 检查键名是否存在
            if key_name in data:
                return data[key_name]  # 返回键对应的值
            else:
                raise KeyError(f"键 {key_name} 在JSON文件中不存在。")

    except json.JSONDecodeError:
        raise ValueError(f"文件 {json_path} 不是有效的JSON文件。")

    except IOError:
        raise IOError(f"读取文件 {json_path} 时发生错误。")

def modifyJson(key_name, new_value, json_path):
    # 检查文件是否存在
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"文件 {json_path} 不存在。")

        # 尝试读取JSON文件
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)  # 解析JSON文件为Python字典

        # 检查键名是否存在，如果不存在则可以选择添加或抛出异常
        if key_name in data:
            data[key_name] = new_value  # 修改键对应的值
        else:
            # 如果你想在键不存在时添加它，可以取消下一行的注释
            # data[key_name] = new_value
            raise KeyError(f"键 {key_name} 在JSON文件中不存在。")

            # 将修改后的字典写回JSON文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"文件 {json_path} 修改成功。")

    except json.JSONDecodeError:
        raise ValueError(f"文件 {json_path} 不是有效的JSON文件。")

    except IOError:
        raise IOError(f"读取或写入文件 {json_path} 时发生错误。")
