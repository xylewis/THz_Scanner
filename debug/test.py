# # coding:utf-8
# import os
# import time
#
# import numpy as np
# from PyQt5.QtCore import Qt, pyqtSignal, QUrl
# from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QVBoxLayout, QStackedWidget, QLabel, \
#     QFileDialog, QMessageBox
# from qfluentwidgets import FluentIcon as FIF, Pivot, qrouter, SegmentedWidget, PivotItem, PushButton, setTheme, Theme, \
#     FlyoutView, Flyout
#
# from ui_submain import Ui_Form
#
# from thzsys.acquisition import AcquisitionType, TerminalConfiguration, Edge
# from thzsys.acquisition import DataCollection
# from thzsys.delayline import DelayControl
# from thzsys.zmotion import Zmotion, Axis
#
# # from thzsignal import SignalCollection, SingleScan, LinearScan
# # from delayline import DelayType
# from PyQt5.QtCore import QRunnable, Qt, QThreadPool, QObject, pyqtSignal, pyqtSlot
# import numpy as np
#
# port =  "10.168.1.16"
# dev = "10.168.1.11"
# #
# # delay = DelayControl(port, 5002)
# # acquisition = DataCollection("Dev3")
#
# control = Zmotion(dev)
# axis = [Axis(control.handle, i) for i in [1,2]]
# delay = DelayControl(port)
# print('dev')
# acquisition = DataCollection("Dev3")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

Z = np.array([[0.05613096, 0.05426862],
 [0.0525325 , 0.05458079],
 [0.05465072, 0.0558866]])
Z1 = np.array([[0.05613096, 0.05426862],
 [0.0525325 , 0.05458079],
 [0.05465072, 0]])

fig, (ax0, ax1) = plt.subplots(2, 1)

c = ax0.pcolor(Z)
ax0.set_title('No edge image')
c = ax1.pcolor(Z1)
ax0.set_title('No edge image')

fig.tight_layout()
plt.show()