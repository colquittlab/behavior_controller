import sys

from multiprocessing import Process
from collections import deque
from PyQt4.QtGui import QApplication,QDialog
from PyQt4 import QtCore, QtGui
from qt.liveaudio import Ui_LiveAudio
import lib.audiorecord as ar
import pyqtgraph as pg
import numpy as np

#from AudioRecorderFunctions import *
#import GlobalVars

# class MainWindow(QtGui.QMainWindow):
#     def __init__(self, window, ui):
#         #super(MainWindow, self).__init__()
#         #self.recorder = ar.AudioRecord()
#         self.recorder.set_sound_card('3') #FIXME
#         self.recorder.test_config()
#         self.window = window
#         self.ui = ui
#         #self.ui.audioplot = pg.PlotWidget(self.ui.verticalLayoutWidget)
#         #self.ui.audioplot = pg.PlotWidget(self.ui.verticalLayoutWidget)
#         self.audio_data = self.ui.audio_plot.plot(x=range(10, 100), y=range(10,100))#(10000, 1E3, pen='y')
#
#         self.ui.audio_plot.setXRange(0, int(0.5 * (44100/256)))
#         self.ui.audio_plot.setYRange(0, 1E4)

#         self.plot_params = {}
#         self.plot_params['xrange'] = range(0, int(0.5* (44100/256)))

#         self.condition = "recording_off"

#     def stop_recording(self):
#         self.recorder.stop()
#         self.condition = "recording_off"



# class AudioThread(QThread):
#     def __init__(self, parent = None):
#         QThread.__init__(self, parent)
#         self.exiting = False
#         self.parent = parent

#         #self.size = QSize(0, 0)
#         #self.stars = 0

#     def __del__(self):
#         self.exiting = True
#         self.wait()

#     def update(self, data):
#         #try:
#             #self.sound_acquisiton_process = Process(acquire_data)
#             #data = recorder.recording_queue.get()
#         self.audio_data.setData(x=self.plot_params['xrange'], y=data)
#             #self.ui.PlotWidget.plot(self.plot_params['xrange'], data)
#         #except:
#         #    print "Exception plotting from recorder"

#     def run(self):
#         parent.recorder.start_return_data()
#         #t = QtCore.QTimer()
#         #t.timeout.connect(self.updateData)
#         #t.start(50)
#         #print "here"
#         #self.condition = "recording_on"
#         #data = deque(maxlen=len(self.plot_params['xrange']))
#         data = np.zeros(len(parent.plot_params['xrange']))
#         samples = 0
#         while not self.exiting:
#             #try:
#             data[samples] = parent.recorder.recording_queue.get()
#             samples += 1
#             if samples == len(parent.plot_params['xrange']):
#                 print data
#                 self.update(data)
#                 samples = 0
#             #except:
#             #    print "Exception getting data from recorder"

# class WorkThread(QtCore.QThread):
#  def __init__(self):
#   QtCore.QThread.__init__(self)

#  def __del__(self):
#   self.wait()

#  def run(self):
#   for i in range(6):
#    time.sleep(0.3) # artificial time delay
#    self.emit( QtCore.SIGNAL('update(QString)'), "from work thread " + str(i) )

#   self.terminate()

app = QApplication(sys.argv)
window = QtGui.QMainWindow()
#window = QDialog()
#window = pg.GraphicsWindow(title="Basic plotting examples")
#window.resize(1000, 600)
ui = Ui_LiveAudio()
ui.setupUi(window)

#inter = Interface(window, ui)

#ui.start_recording_button.connect(ui.start_recording_button,
#                                        QtCore.SIGNAL(("clicked()")),
#                                        inter.start_recording)

#ui.stop_recording_button.connect(ui.stop_recording_button,
#                                        QtCore.SIGNAL(("clicked()")),
#                                        inter.stop_recording)



window.show()
sys.exit(app.exec_())
