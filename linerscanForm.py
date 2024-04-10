# coding:utf-8
import os
import time

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
from PyQt5.QtCore import QRunnable, Qt, QThreadPool, QObject, pyqtSignal, pyqtSlot
import numpy as np
from dataplot import DataPlot

STOP = False

class linerscan(QWidget, Ui_Form1):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.f0 = 0.75
        self.x_start = -5
        self.x_end = 5
        self.x_step = 5
        self.y_start = 0
        self.y_end = 5
        self.y_step = 5
        self.x_speed = 2.0
        self.y_speed = 2.0
        self.axisGroup = [3,4]

        self.length = 70
        self.offset = 0
        self.iter = 1
        self.ave = 10
        self.delay = "10.168.1.16"
        self.motion = "10.168.1.11"
        self.device = "Dev2"
        self.magunit = 0
        self.phaunit = 0
        self.IsOpenExtClock = False
        self.ISAutoBak = False
        self.result = []
        self.bakPath = os.path.abspath('.') + '\\.temp'
        if not os.path.exists(self.bakPath):
            os.makedirs(self.bakPath)

        self.togbtnClock.setChecked(False)
        self.comboDelay.addItems(["127.0.0.1", "10.168.1.16"])
        self.comboMotion.addItems(["127.0.0.1", "10.168.1.11"])
        self.comboDevice.addItems(["Dev1", "Dev2", "Dev3", "Dev4"])
        self.comboDelay.setCurrentIndex(1)
        self.comboMotion.setCurrentIndex(1)
        self.comboDevice.setCurrentIndex(1)
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
        self.dspinFreq.setValue(self.f0)
        self.threadpool = QThreadPool()

        self.ProgressBar.setVisible(True)
        self.ProgressRing.setVisible(False)
        self.IndeterminateProgressBar.setVisible(False)
        self.linePath.setEnabled(False)
        self.btnSelectPath.setEnabled(False)
        self.btnOpenPath.setEnabled(False)

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

        self.segSetting = PivotItem('Setting')
        self.segOperation = PivotItem('Operation')
        self.segAxis = PivotItem('Axis')
        self.segDev = PivotItem('Dev')
        self.SegmentedWidget.insertWidget(0, 'Setting', self.segSetting, onClick=self.pageSetting)
        self.SegmentedWidget.insertWidget(1, 'Operation', self.segOperation, onClick=self.pageOperation)
        self.SegmentedWidget.insertWidget(3, 'Axis', self.segAxis, onClick=self.pageAxis)
        self.SegmentedWidget.insertWidget(2, 'Dev', self.segDev, onClick=self.pageDev)
        self.SegmentedWidget.setItemFontSize(12)
        self.SegmentedWidget.setCurrentItem('Setting')
        self.stackedWidget.setCurrentIndex(0)

        self.segScan = PivotItem('Outline')
        self.segRuntime = PivotItem('Runtime')
        self.segFigure = PivotItem('Figure')
        self.SegmentedWidget_2.insertWidget(0, 'Outline', self.segScan, onClick=lambda: self.stackedWidget_2.setCurrentIndex(1))
        self.SegmentedWidget_2.insertWidget(2, 'Runtime', self.segFigure, onClick=lambda: self.stackedWidget_2.setCurrentIndex(2))
        self.SegmentedWidget_2.insertWidget(1, 'Figure', self.segRuntime, onClick=lambda: self.stackedWidget_2.setCurrentIndex(0))
        self.SegmentedWidget_2.setItemFontSize(12)
        self.SegmentedWidget_2.setCurrentItem('Outline')
        self.stackedWidget_2.setCurrentIndex(1)

        self.qpxpos.valueChanged.connect(lambda: self.axis[0].move(self.qpxpos.value()))
        self.qpypos.valueChanged.connect(lambda: self.axis[1].move(self.qpypos.value()))

        self.btnLink.clicked.connect(self.linkStart)
        self.btnStart.clicked.connect(self.oh_no)
        self.btnStart.clicked.connect(lambda: self.btnHome.setEnabled(False))
        # self.btnStart.clicked.connect(self.qpdebug)
        self.btnStart.clicked.connect(self.progress_busy)
        self.btnStart.clicked.connect(self.startScan)
        self.btnStop.clicked.connect(self.stopThread)
        self.btnSave.clicked.connect(self.saveResult)
        self.btnLoad.clicked.connect(self.loadResult)
        self.btnHome.clicked.connect(self.home)
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

        # self.ui.btnExit.clicked.connect(lambda: sys.exit(app.exec()))
        self.togbtnClock.clicked.connect(self.clockEnable)
        self.SwitchButton.checkedChanged.connect(self.themeChange)

        self.btnStart.setIcon(FIF.POWER_BUTTON)

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

    def linkStart(self):
        try:
            self.control = Zmotion(self.motion)
            self.axis = [Axis(self.control.handle, i) for i in self.axisGroup]
            # if self.delay == "127.0.0.1":
            #     delay = DelayControl(self.delay, 5002)
            # else:
            #     delay = DelayControl(self.delay)
            # acquisition = DataCollection(self.device)
        except:
            self.createTopRightInfoBar('error','Error', 'Please check the connection of the device')
        else:
            # delay.close()
            # acquisition.close()
            self.btnLink.setEnabled(False)
            self.createTopRightInfoBar('success',"Info", "Link Start")

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
        self.canvas3.ax1.clear()
        print('d')
        result = np.load('result.npy')
        X, Y = np.meshgrid(self.x_sequence,self.y_sequence2)
        f_seq_array = np.array(result.amp)
        # print(data.f[np.where((data.f-self.f0) == min(abs(data.f-self.f0)))],np.where((data.f-self.f0) == -min(abs(data.f-self.f0))))
        fN=123
        f0_seq = (f_seq_array[:, fN])
        f0_plane = f0_seq.reshape(len(self.y_sequence), len(self.x_sequence))

        self.canvas3.ax1.pcolor(abs(f0_plane))
        self.canvas3.fig.tight_layout()
        self.canvas3.draw()

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
                        self.axisGroup
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
        worker.signals.axIdle.connect(lambda: self.spotCtrl(worker.axIndex[0], worker.axIndex[1]))
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
        self.canvas3.ax1.clear()
        np.save('result1.npy', result.amp)
        X, Y = np.meshgrid(self.x_sequence,self.y_sequence2)
        f_seq_array = 10 ** (result.amp[:,0:len(result.f)] / 20)
        temp1 = np.where((result.f-self.f0) == min(abs(result.f-self.f0)))
        temp2 = np.where((result.f-self.f0) == -min(abs(result.f-self.f0)))
        if temp1:
            fN=temp1[0][0]
        elif temp2:
            fN=temp2[0][0]
        f0_seq = (f_seq_array[:, fN])
        f0_plane = f0_seq.reshape(len(self.y_sequence), len(self.x_sequence))
        self.canvas3.ax1.pcolor(X, Y, abs(f0_plane))
        self.canvas3.fig.tight_layout()
        self.canvas3.draw()
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
        if self.SwitchButton.isChecked():
            self.canvas.ax1.patch.set_facecolor('#323232')
            self.canvas1.ax1.patch.set_facecolor('#323232')
            self.canvas2.ax1.patch.set_facecolor('#323232')

        self.canvas.ax1.plot(data.t, data.mat[-1])
        self.canvas.fig.suptitle('[Peak to Peak: %.2f Vpp]' % (np.max(data.mat[-1]) - np.min(data.mat[-1])))

        if self.swMag.isChecked():
            self.canvas1.ax1.plot(data.f, 10 ** (data.amp[-1][0:len(data.f)] / 20))
            self.canvas1.ax1.xaxis.set_ticks(np.arange(0, 11, 5))
        else:
            self.canvas1.ax1.plot(data.f, data.amp[-1][0:len(data.f)])
            self.canvas1.ax1.xaxis.set_ticks(np.arange(0, 11, 5))

        if self.swPha.isChecked():
            self.canvas2.ax1.plot(data.f, data.pha[-1][0:len(data.f)] / 180 * np.pi)
        else:
            self.canvas2.ax1.plot(data.f, data.pha[-1][0:len(data.f)])


        # self.canvas1.fig.suptitle("F-Domain")
        # self.canvas1.fig.supxlabel("Frequency (THz)")
        # self.canvas1.fig.supylabel("Magnitude (dB)")
        self.canvas.fig.tight_layout()
        self.canvas.draw()
        self.canvas1.fig.tight_layout()
        self.canvas1.draw()
        self.canvas2.fig.tight_layout()
        self.canvas2.draw()

    def pageSetting(self):
        self.stackedWidget.setCurrentIndex(0)

    def pageOperation(self):
        self.stackedWidget.setCurrentIndex(1)

    def pageAxis(self):
        self.stackedWidget.setCurrentIndex(3)

    def pageDev(self):
        self.stackedWidget.setCurrentIndex(2)

    def stopThread(self):
        global STOP
        STOP = True

    def stopThreadAfter(self):
        global STOP
        self.axis[0].cancel()
        self.axis[1].cancel()
        self.ProgressBar.setValue(0)
        self.home()
        STOP = False
        self.canvas.ax1.clear()
        self.canvas1.ax1.clear()
        self.canvas2.ax1.clear()
        if self.SwitchButton.isChecked():
            self.canvas.ax1.patch.set_facecolor('#323232')
            self.canvas1.ax1.patch.set_facecolor('#323232')
            self.canvas2.ax1.patch.set_facecolor('#323232')
        self.canvas.draw()
        self.canvas1.draw()
        self.canvas2.draw()
        self.btnStop.setEnabled(False)

    def saveResult(self):
        if self.result:
            t = self.result[0]
            ts = self.result[1]
            f = self.result[2]
            fs = self.result[3]
            fp = [0 for i in range(len(t))]
            fsp = [0 for i in range(len(t))]
            fp[0:len(f)] = f
            fsp[0:len(fs)] = fs

            Sig = np.array([t, ts, fp, fsp])
            filedir = QFileDialog.getExistingDirectory(self, "选择输出目录文件", os.getcwd())
            np.savetxt(filedir + '/yourResult.txt', Sig, fmt='%.6f', delimiter=' ')
        else:
            QMessageBox.information(self, "提示", "请先执行扫描" + "\r\n"
                                    + "(>_<)" + "\r\n"
                                    + "请等待扫描完成")

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
        print(self.delay)
        print(self.motion)
        print(self.device)
    def clockEnable(self):
        if self.togbtnClock.isChecked():
            self.IsOpenExtClock = True
        else:
            self.IsOpenExtClock = False

    def home(self):
        self.axis[0].move(0)
        self.axis[1].move(0)
        self.ProgressBar.setValue(0)
        self.CardWidget_2.deleteLater()
        self.CardWidget_2 = CardWidget(self.page_10)
        self.CardWidget_2.setObjectName("CardWidget_2")
        self.verticalLayout_12.addWidget(self.CardWidget_2)
        self.canvas.ax1.clear()
        self.canvas1.ax1.clear()
        self.canvas2.ax1.clear()
        self.canvas3.ax1.clear()
        if self.SwitchButton.isChecked():
            self.canvas.ax1.patch.set_facecolor('#323232')
            self.canvas1.ax1.patch.set_facecolor('#323232')
            self.canvas2.ax1.patch.set_facecolor('#323232')
            self.canvas3.ax1.patch.set_facecolor('#323232')
        self.canvas.draw()
        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()
        self.btnHome.setEnabled(False)

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
            self.axisGroup = [1, 2]
            print(self.axisGroup)
        else:
            self.axisGroup = [3, 4]
            print(self.axisGroup)
        pass

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
        self.bakPath = self.bakPath.replace('/', '\\')
        os.system('copy ' + os.path.abspath('.') + '\\.temp ' + self.bakPath)
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

    # def renderEchart(self, x, y):
    #     c = (
    #         Line(
    #             init_opts=opts.InitOpts(
    #                 animation_opts=opts.AnimationOpts(
    #                     animation=False,
    #                     animation_delay=1000, animation_easing="elasticOut"
    #                 )
    #             )
    #         )
    #         .add_xaxis(x)
    #         .add_yaxis("A", y, is_symbol_show=False)
    #         # .set_global_opts(title_opts=opts.TitleOpts(title="Bar-动画配置", subtitle="AnimationOpts"))
    #         .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    #         .render("animation.html")
    #     )
    #     self.browser.load(QUrl("D:/FinancialMedia/CodeCraft/PYCHARM/NeoTHz/animation.html"))

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

        self.data = DataPlot(delay.interval, n=8192)
        self.data.t = self.length
        self.data.f = 10

        print('init')
        for j in range(len(y_sequence)):
            self.signals.progress2.emit(self.progress_total)
            axis[1].step(y_step)
            axis[0].move(x_start)
            for i in range(len(x_sequence)):
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
                        self.data_buffer = main_task(delay, acquisition, self.IsOpenExtClock)
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


async def task_init(delay: DelayControl, acquisition: DataCollection, IsOpenExtClock):

    acquisition.channel = 1
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


def main_task(delay, acquisition, IsOpenExtClock):
    import asyncio
    asyncio.run(task_init(delay, acquisition, IsOpenExtClock))
    asyncio.run(task_exec(delay, acquisition))
    return np.mean(acquisition.buffer, axis=0)


