# coding:utf-8
import os
import time
import json
import math
import pandas as pd

import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QVBoxLayout, QStackedWidget, QLabel, \
    QFileDialog, QMessageBox
from qfluentwidgets import FluentIcon as FIF, Pivot, qrouter, SegmentedWidget, PivotItem, PushButton, setTheme, Theme, \
    FlyoutView, Flyout, InfoBar, InfoBarPosition

from dataplot import DataPlot
from ui_submain import Ui_Form

from thzsys.acquisition import AcquisitionType, TerminalConfiguration, Edge
from thzsys.acquisition import DataCollection
from thzsys.delayline import DelayControl
from thzsys.zmotion import Zmotion, Axis

# from thzsignal import SignalCollection, SingleScan, LinearScan
# from delayline import DelayType
from PyQt5.QtCore import QRunnable, Qt, QThreadPool, QObject, pyqtSignal, pyqtSlot
import numpy as np

STOP = False


class submain(QWidget, Ui_Form):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.lastx = 0  # 获取鼠标按下时的坐标X
        self.lasty = 0  # 获取鼠标按下时的坐标Y
        self.press = False

        self.length = 70
        self.offset = 0
        self.iter = 1
        self.ave = 10
        self.delay = "10.168.1.16"
        self.motion = "10.168.1.11"
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
        self.channel = 1

        self.togbtnClock.setChecked(False)
        self.comboPort.addItems(["127.0.0.1", "10.168.1.16"])
        self.comboDev.addItems(["127.0.0.1", "10.168.1.11"])
        self.comboFig.addItems(["Time","Mag","Pha"])
        self.comboChannel.addItems(["Channel1","Channel2"])
        self.comboPort.setCurrentIndex(1)
        self.comboDev.setCurrentIndex(1)
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
        self.btnLoad.setVisible(False)
        self.btnExit.setVisible(False)
        self.togbtnClock.setChecked(True)
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

        self.segSetting = PivotItem('Setting')
        self.segOperation = PivotItem('Operation')
        self.segDev = PivotItem('Dev')
        self.SegmentedWidget.insertWidget(0, 'Setting', self.segSetting, onClick=self.pageSetting)
        # self.SegmentedWidget.insertWidget(1, 'Operation', self.segOperation, onClick=self.pageOperation)
        # self.SegmentedWidget.insertWidget(2, 'Dev', self.segDev, onClick=self.pageDev)
        self.SegmentedWidget.setItemFontSize(12)
        self.SegmentedWidget.setCurrentItem('Setting')
        self.stackedWidget.setCurrentIndex(0)

        self.btnStart.clicked.connect(self.oh_no)
        self.btnStart.clicked.connect(self.progress_busy)
        self.btnStop.clicked.connect(self.stopThread)
        self.btnSave.clicked.connect(self.saveResult)
        self.btnLoad.clicked.connect(self.loadResult)
        self.btnReset.clicked.connect(self.reset)
        self.dspinLength.valueChanged.connect(self.lengthAssert)
        self.dspinOffset.valueChanged.connect(self.offsetAssert)
        self.spinIter.valueChanged.connect(self.iterAssert)
        self.spinAve.valueChanged.connect(self.aveAssert)
        self.swMag.checkedChanged.connect(self.magUnitAssert)
        self.swPha.checkedChanged.connect(self.phaUnitAssert)
        self.btnOpenPath.clicked.connect(self.OpenPath)
        self.btnSelectPath.clicked.connect(self.SelectPath)
        self.togbtnAutoBak.clicked.connect(self.AutoBakEnable)
        self.dspinXmin.valueChanged.connect(self.axesChange)
        self.dspinXmax.valueChanged.connect(self.axesChange)
        self.dspinYmin.valueChanged.connect(self.axesChange)
        self.dspinYmax.valueChanged.connect(self.axesChange)
        self.btnVanilla.clicked.connect(self.axesReset)


        # self.ui.btnExit.clicked.connect(lambda: sys.exit(app.exec()))
        self.comboPort.currentIndexChanged.connect(self.ipChange)
        self.comboDev.currentIndexChanged.connect(self.ipChange)
        self.comboChannel.currentIndexChanged.connect(self.ipChange)
        self.togbtnClock.clicked.connect(self.clockEnable)
        self.SwitchButton.checkedChanged.connect(self.themeChange)

        self.btnStart.setIcon(FIF.POWER_BUTTON)

    def oh_no(self):
        worker = Worker(self.execute_this_fn, self.iter,
                        self.ave,
                        self.length,
                        self.offset,
                        self.delay,
                        self.motion,
                        self.IsOpenExtClock,
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

    def getResult(self, result):
        self.result = result

    def execute_this_fn(self):
        pass

    def progress_busy(self):
        self.ProgressBar.setVisible(False)
        self.IndeterminateProgressBar.setVisible(True)

    def progress_ding(self, progress_count):
        # self.ui.lineEditScanNo.setText(str(progress_count))
        self.ProgressBar.setVisible(True)
        self.ProgressRing.setVisible(True)
        self.ProgressRing.setTextVisible(True)

        self.IndeterminateProgressBar.setVisible(False)
        self.ProgressBar.setValue(progress_count)
        self.ProgressRing.setValue(progress_count)

    def progress_ding_2(self, progress_total):
        self.ProgressBar.setRange(0, progress_total)
        self.ProgressRing.setRange(0, progress_total)

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

        self.canvas.ax1.xaxis.grid()
        self.canvas.ax1.yaxis.grid()
        self.canvas1.ax1.xaxis.grid()
        self.canvas1.ax1.yaxis.grid()
        self.canvas2.ax1.xaxis.grid()
        self.canvas2.ax1.yaxis.grid()
        self.canvas.fig.tight_layout()
        self.canvas.draw()
        self.canvas1.fig.tight_layout()
        self.canvas1.draw()
        self.canvas2.fig.tight_layout()
        self.canvas2.draw()

        self.xylim = [self.canvas.ax1.get_xlim(),self.canvas.ax1.get_ylim()]
        self.xylim1 = [self.canvas1.ax1.get_xlim(),self.canvas1.ax1.get_ylim()]
        self.xylim2 = [self.canvas2.ax1.get_xlim(),self.canvas2.ax1.get_ylim()]

        if self.iter == len(data.mat):
            self.result = [data.mat, data.f, 10 ** (data.amp[-1][0:len(data.f)] / 20), np.unwrap(data.pha[-1][0:len(data.f)], period = 360) / 180 * np.pi]
            self.filename = time.strftime("%Y%m%d_%H%M", time.localtime()) + ".txt"
            np.savetxt(
                os.path.abspath('.') + '\\.temp' + '/' + self.filename,
                data.mat,
                fmt="%.6f", delimiter='\t')

    def pageSetting(self):
        self.stackedWidget.setCurrentIndex(0)

    def pageOperation(self):
        self.stackedWidget.setCurrentIndex(1)

    def pageDev(self):
        self.stackedWidget.setCurrentIndex(2)

    def stopThread(self):
        global STOP
        STOP = True

    def stopThreadAfter(self):
        global STOP
        STOP = False
        # self.lineEditScanNo.setText("0")
        self.ProgressBar.setValue(0)
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
            openPath = readJson('userPath', self.confPath)
            if os.path.exists(openPath):
                pass
            else:
                openPath = self.bakPath
            Sig = np.array(self.result[0])
            f = self.result[1][np.newaxis, :]
            Mag = self.result[2][np.newaxis, :]
            Pha = self.result[3][np.newaxis, :]
            t = np.arange(0, self.length, 0.02).reshape([1, Sig.shape[1]])
            # f = np.arange(0, 10, 1 / 0.02 / (2 ** math.ceil(math.log2(self.length / 0.02))))
            Sig = np.concatenate((t, Sig), axis=0)
            Mag = np.concatenate((f, Mag), axis=0)
            Pha = np.concatenate((f, Pha), axis=0)
            filedir, _ = QFileDialog.getSaveFileName(self, "请键入文件名", "", "All Files (*)", openPath)
            if filedir:
                labelMag = ['f'] + ['Mag(a.u)']
                df = pd.DataFrame(Mag.T, columns=labelMag)
                df.to_csv(filedir + '-M.txt', sep='\t', index=False, float_format='%.6f')
                labelPha = ['f'] + ['Pha(rad)']
                df = pd.DataFrame(Mag.T, columns=labelPha)
                df.to_csv(filedir + '-P.txt', sep='\t', index=False, float_format='%.6f')
                header = 'ts' +'\t'+ '\t'.join(['Iter{}'.format(i + 1) for i in range(Sig.shape[0] - 1)]) + '\n'
                with open(filedir + '-T.txt', 'w') as f:
                    f.write(header)
                    np.savetxt(f, Sig.T, fmt="%.6f", delimiter='\t')
                if filedir == openPath:
                    pass
                else:
                    modifyJson("userPath", os.path.dirname(filedir), 'config.json')
        else:
            self.createTopRightInfoBar('warning','Warning', 'Please scan first or wait for the scan to complete(>_<)')

    def loadResult(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                  "Text Files(*.txt)")
        if fileName == '':
            pass
        else:
            Sig = np.loadtxt(fileName, delimiter='\t')

            # data = DataPlot(0.02, n=8192)
            # data.t = self.length
            # data.f = 10
            # data.mat = Sig.tolist()
            # data.fft()
            # print("d")
            # self.canvas.ax1.clear()
            # self.canvas.ax1.plot(data.t, Sig[-1])
            # # self.canvas.fig.suptitle("T-Domain")
            # # self.canvas.fig.supxlabel("Time (ps)")
            # # self.canvas.fig.supylabel("Voltage (V)")
            # self.canvas.fig.tight_layout()
            # self.canvas.draw()

            # self.canvas1.ax1.clear()
            # self.canvas1.ax1.plot(Sig[2][0:np.argwhere(Sig[2] == 0)[1][0]],
            #                       Sig[3][0:np.argwhere(Sig[3] == 0)[0][0]])
            # # self.canvas.fig.suptitle("T-Domain")
            # # self.canvas.fig.supxlabel("Time (ps)")
            # # self.canvas.fig.supylabel("Voltage (V)")
            # self.canvas1.fig.tight_layout()
            # self.canvas1.draw()

    def ipChange(self):
        self.delay = self.comboPort.currentText()
        self.motion = self.comboDev.currentText()
        self.channel = self.comboChannel.currentIndex() + 1
        print(self.delay)
        print(self.motion)
        print(self.channel)

    def clockEnable(self):
        if self.togbtnClock.isChecked():
            self.IsOpenExtClock = True
            print(self.IsOpenExtClock)
        else:
            self.IsOpenExtClock = False
            print(self.IsOpenExtClock)

    def reset(self):
        self.length = 100
        self.offset = 100
        self.iter = 2
        self.ave = 2
        self.delay = "127.0.0.1"
        self.motion = "127.0.0.1"
        self.magunit = 0
        self.phaunit = 0
        self.IsOpenExtClock = False
        self.result = []

        self.togbtnClock.setChecked(False)
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
        self.ProgressRing.setValue(0)
        self.btnStop.setEnabled(False)

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
        if event.inaxes:  # 判断鼠标是否在axes内
            if event.button == 1:  # 判断按下的是否为鼠标左键1（右键是3）
                self.press = True
                self.lastx = event.xdata  # 获取鼠标按下时的坐标X
                self.lasty = event.ydata  # 获取鼠标按下时的坐标Y
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


class Worker(QRunnable):
    @property
    def progress_total(self):
        return self.iter * self.ave

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
        self.channel = args[7]
        self.read_count = 1
        self.data = DataPlot
        self.data_buffer = []
        self.result = DataPlot
        self.progress_count = 0
        # self.progress_total = 0
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        global STOP
        if self.delay == "127.0.0.1":
            delay = DelayControl(self.delay, 5002)
            acquisition = DataCollection("Dev1")
        else:
            delay = DelayControl(self.delay)
            acquisition = DataCollection("Dev1")
        delay.offset = self.offset  # Sampling Offset (ps)
        delay.length = self.length  # Sampling Length (ps)
        delay.interval = 0.02  # Sampling Interval (ps)
        delay.iteration = self.ave  # Iteration Average

        self.data = DataPlot(delay.interval, n=2 ** math.ceil(math.log2(self.length / 0.02)))
        self.data.t = self.length
        self.data.f = 10

        for n in range(0, self.iter):
            self.signals.progress2.emit(self.progress_total)
            self.signals.youCanStop.emit()
            if STOP is not True:

                time.sleep(0.2+ self.length / 2000)
                # print(self.data.mat)
                self.data_buffer = main_task(delay, acquisition, self.IsOpenExtClock, self.channel)
                self.data.mat.append(self.data_buffer)
                self.data.fft()

                self.signals.render_iter.emit(self.data)
                self.signals.progress.emit(self.progress_count)

                self.progress_count += self.ave
            else:
                break
            if STOP is not True:
                # scan.data.mat.append(np.mean(np.array(self.data_buffer), axis=0))
                # scan.data.fft()
                # self.data = scan.data
                # self.signals.render_iter.emit(self.data)
                # self.result = [scan.data.t, scan.data.mat[-1][0:len(scan.data.t)],
                #                scan.data.f, scan.data.amp[-1][0:len(scan.data.f)]]
                # self.result.append(self.data_buffer)
                # self.signals.result.emit(self.result)
                self.read_count = 1
                # self.data_buffer = []
            else:
                break
        if STOP is True:
            self.read_count = 1
            self.data_buffer = []
            self.signals.stop.emit()

        # scan = SingleScan(self.delay, self.motion, "Dev1")
        # scan.channel = 1  # Signal Channel
        # if self.clock:
        #     scan.terminal = 3  # Trigger Terminal
        # scan.delay.length = self.length  # Delay Length
        # scan.delay.offset = self.offset  # Delay Offset
        # scan.range = [-5.0, 5.0]  # Voltage Range
        # scan.config(DelayType.HighResolution, average=self.ave)
        # for n in range(0, self.iter):
        #     self.signals.progress2.emit(self.progress_total)
        #     scan.qptaskstart()
        #     self.signals.youCanStop.emit()
        #     for i in range(0, scan.delay.iteration):
        #         if ISSTOP is not True:
        #             self.progress_count += 1
        #             self.data_buffer.append(scan.qpreaddata())
        #             self.signals.render_ave.emit(self.data_buffer)
        #             self.signals.progress.emit(self.progress_count)
        #             if self.progress_total > 100 and self.progress_count % 10 == 0:
        #                 np.savetxt(os.path.abspath('.') + '\\.temp' + f"/{self.progress_count / 10}.txt",
        #                            np.mean(self.data_buffer, axis=0),
        #                            fmt="%.6f")
        #             time.sleep(0.2)
        #         else:
        #             break
        #     if ISSTOP is not True:
        #         scan.qptaskstop()
        #         scan.data.mat.append(np.mean(np.array(self.data_buffer), axis=0))
        #         scan.data.fft()
        #         self.data = scan.data
        #         self.signals.render_iter.emit(self.data)
        #         self.result = [scan.data.t, scan.data.mat[-1][0:len(scan.data.t)],
        #                        scan.data.f, scan.data.amp[-1][0:len(scan.data.f)]]
        #         self.signals.result.emit(self.result)
        #         self.read_count = 1
        #         self.data_buffer = []
        #     else:
        #         break
        # if ISSTOP is True:
        #     scan.qptaskstop()
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
