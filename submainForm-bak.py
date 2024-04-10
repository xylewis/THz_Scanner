# coding:utf-8
import os
import time

import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QVBoxLayout, QStackedWidget, QLabel, \
    QFileDialog, QMessageBox
from qfluentwidgets import FluentIcon as FIF, Pivot, qrouter, SegmentedWidget, PivotItem, PushButton, setTheme, Theme, \
    FlyoutView, Flyout

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

        self.length = 70
        self.offset = 0
        self.iter = 1
        self.ave = 10
        self.delay = "127.0.0.1"
        self.motion = "127.0.0.1"
        self.magunit = 0
        self.phaunit = 0
        self.IsOpenExtClock = False
        self.ISAutoBak = False
        self.result = []
        self.bakPath = os.path.abspath('.') + '\\.temp'
        if not os.path.exists(self.bakPath):
            os.makedirs(self.bakPath)

        self.togbtnClock.setChecked(False)
        self.comboPort.addItems(["127.0.0.1", "10.168.1.16"])
        self.comboDev.addItems(["127.0.0.1", "10.168.1.11"])
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

        self.segSetting = PivotItem('Setting')
        self.segOperation = PivotItem('Operation')
        self.segDev = PivotItem('Dev')
        self.SegmentedWidget.insertWidget(0, 'Setting', self.segSetting, onClick=self.pageSetting)
        self.SegmentedWidget.insertWidget(1, 'Operation', self.segOperation, onClick=self.pageOperation)
        self.SegmentedWidget.insertWidget(2, 'Dev', self.segDev, onClick=self.pageDev)
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

        # self.ui.btnExit.clicked.connect(lambda: sys.exit(app.exec()))
        self.comboPort.currentIndexChanged.connect(self.ipChange)
        self.comboDev.currentIndexChanged.connect(self.ipChange)
        self.togbtnClock.clicked.connect(self.clockEnable)
        self.SwitchButton.checkedChanged.connect(self.themeChange)

        # self.browser = QWebEngineView()
        # self.horizontalLayout_2.addWidget(self.browser)
        # self.verticalLayout_3.addWidget(PivotInterface(self))

        self.btnStart.setIcon(FIF.POWER_BUTTON)

    def oh_no(self):
        worker = Worker(self.execute_this_fn, self.iter,
                        self.ave,
                        self.length,
                        self.offset,
                        self.delay,
                        self.motion,
                        self.IsOpenExtClock
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
        self.delay = self.comboPort.currentText()
        self.motion = self.comboDev.currentText()
        print(self.delay)
        print(self.motion)

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
            acquisition = DataCollection("Dev2")
        else:
            delay = DelayControl(self.delay)
            acquisition = DataCollection("Dev3")
        delay.offset = self.offset  # Sampling Offset (ps)
        delay.length = self.length  # Sampling Length (ps)
        delay.interval = 0.02  # Sampling Interval (ps)
        delay.iteration = self.ave  # Iteration Average

        self.data = DataPlot(delay.interval, n=8192)
        self.data.t = self.length
        self.data.f = 10


        for n in range(0, self.iter):
            self.signals.progress2.emit(self.progress_total)
            self.signals.youCanStop.emit()
            if STOP is not True:
                self.data_buffer = main_task(delay, acquisition, self.IsOpenExtClock)
                self.data.mat.append(self.data_buffer)
                self.data.fft()

                self.signals.render_iter.emit(self.data)
                self.signals.progress.emit(self.progress_count)
                # if self.progress_total > 100 and self.progress_count % 10 == 0:
                #     np.savetxt(os.path.abspath('.') + '\\.temp' + f"/{self.progress_count / 10}.txt",
                #                self.data_buffer,
                #                fmt="%.6f")
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
