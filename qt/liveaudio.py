# -*- coding: utf-8 -*-

import sys
import time
import pylab
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import lib.audiorecording_tools as ar
import numpy as np
from collections import deque


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class AudioPlotWidget(pg.PlotWidget):
    def __init__(self, layout, recorder):
        super(AudioPlotWidget, self).__init__(layout)
        self.plot_params = {}
        self.plot_params['xrange'] = range(0, round(recorder.params['rate'] / recorder.params['chunk']))


class AudioThread(QtCore.QThread):
    def __init__(self, parent):
        QtCore.QThread.__init__(self, parent = None)
        self.exiting = False
        self.parent = parent
        self.plot_params = self.parent.parent.audio_plot.plot_params

    def __del__(self):
        self.exiting = True
        self.wait()

    def run(self):
        maxlen = len(self.plot_params['xrange'])
        data = deque(maxlen=maxlen)

        # preload deque
        while len(data) < maxlen:
            data.append(0)

        while not self.exiting:
            data.append(ar.get_audio_power(self.parent.parent.recorder.recording_queue.get()))
            self.emit( QtCore.SIGNAL( "gotData( PyQt_PyObject )" ), list(data) )

    def stop(self):
        self.exiting = True
        self.quit()

class SpecThread(QtCore.QThread):
    def __init__(self, parent):
        QtCore.QThread.__init__(self, parent = None)
        self.exiting = False
        self.parent = parent

    def __del__(self):
        self.exiting = True
        self.wait()

    def run(self):
        data = np.zeros(256)
        while not self.exiting:
            data = np.append(data, np.fromstring(self.parent.parent.recorder.recording_queue.get(),
                                                 dtype=np.int16))
            if len(data) > 256*64:
                self.emit(QtCore.SIGNAL("gotData( PyQt_PyObject )"), data)
                data = np.zeros(256)

    def stop(self):
        self.exiting = True
        self.quit()

class AudioManager:
    def __init__(self, parent):
        self.parent = parent
        self.plot_params = self.parent.audio_plot.plot_params
        self.initial = True
        self.writing = False

    def setup(self):
        self.thread = AudioThread(self)
        QtCore.QObject.connect(self.thread,
                               QtCore.SIGNAL("gotData( PyQt_PyObject )"),
                               self.update,
                               QtCore.Qt.QueuedConnection)

        rel = self.parent.recorder.params['rate'] / self.parent.recorder.params['chunk']
        self.parent.audio_plot.setXRange(0, rel)
        self.audio_data = self.parent.audio_plot.plot()
        self.audio_data.setPen((200,100,100))

    def update(self, y):
        if self.initial:
            self.parent.audio_plot.setYRange(0, max(y) * 2)
            self.initial = False
        self.audio_data.setData(x=self.plot_params['xrange'], y=y)

    def start(self):
        self.setup()
        self.thread.start()

    def stop(self):
        self.thread.stop()

    def start_write_to_file(self):
        self.parent.recorder.start_write_to_file()
        self.writing = True

    def stop_write_to_file(self):
        self.parent.recorder.stop_write_to_file()
        self.writing = False




class SpecManager:
    def __init__(self, parent):
        self.parent = parent
        self.plot_params = self.parent.audio_plot.plot_params

    def setup(self):
        self.thread = SpecThread(self)
        QtCore.QObject.connect(self.thread, QtCore.SIGNAL( "gotData( PyQt_PyObject )" ), self.update, QtCore.Qt.QueuedConnection )
        self.spec_data = self.parent.spectrogram.plot()
        self.spec_data.setPen((100,200,100))
        self.data_mean_max = 0

    def update(self, data):
        sdata = pylab.specgram(data, Fs=44100)
        data_mean = np.mean(sdata[0], 1)
        curr_max = max(data_mean)
        if (curr_max > self.data_mean_max):
            self.data_mean_max = curr_max
            self.parent.spectrogram.setYRange(0, self.data_mean_max)
        xr = (len(sdata[1])/2)
        self.spec_data.setData(sdata[1][0:xr], data_mean[0:xr])

    def start(self):
        self.setup()
        self.thread.start()

    def stop(self):
        self.thread.stop()

class SoundCardBox(QtWidgets.QSpinBox):
    def __init__(self, parent, recorder):
        super(SoundCardBox, self).__init__(parent)
        soundcard_names = recorder.list_sound_cards()
        self.setStrings(soundcard_names)

    def strings(self):
        return self._strings

    def setStrings(self, strings):
        self._strings = tuple(strings)
        self._values = dict(zip(strings, range(len(strings))))
        self.setRange(0, len(strings) - 1)

    def textFromValue(self, value):
        return self._strings[value]

    def valueFromText(self, text):
        return self._values[text]

class ChannelBox(QtWidgets.QSpinBox):
    def __init__(self, parent, recorder):
        super(ChannelBox, self).__init__(parent)
        #channel_names = map(str, cnames)
        channel_names = map(str, range(1,5))
        self.setStrings(channel_names)

    def strings(self):
        return self._strings

    def setStrings(self, strings):
        self._strings = tuple(strings)
        self._values = dict(zip(strings, map(int, strings)))
        self.setRange(0, len(strings) - 1)

    def textFromValue(self, value):
        print("value", value)
        print("string",  self._strings[value])
        return self._strings[value]

    def valueFromText(self, text):
        print("vt")
        return self._values[text]

class Ui_LiveAudio(object):
    def __del__(self):
        self.recorder.stop()

    def __init__(self, config):
        super(Ui_LiveAudio, self).__init__()
        self.config = config
        self.audio_recording = False

    def setupUi(self, LiveAudio):
        LiveAudio.setObjectName(_fromUtf8("LiveAudio"))
        LiveAudio.resize(765, 354)
        self.cancel_button = QtWidgets.QPushButton(LiveAudio)
        self.cancel_button.setGeometry(QtCore.QRect(660, 270, 99, 27))
        self.cancel_button.setObjectName(_fromUtf8("cancel_button"))
        self.start_recording_button = QtWidgets.QPushButton(LiveAudio)
        self.start_recording_button.setGeometry(QtCore.QRect(10, 270, 141, 27))
        self.start_recording_button.setObjectName(_fromUtf8("start_recording_button"))
        self.stop_recording_button = QtWidgets.QPushButton(LiveAudio)
        self.stop_recording_button.setGeometry(QtCore.QRect(150, 270, 141, 27))
        self.stop_recording_button.setObjectName(_fromUtf8("stop_recording_button"))
        self.write_to_file = QtWidgets.QPushButton(LiveAudio)
        self.write_to_file.setGeometry(QtCore.QRect(290, 270, 101, 27))
        self.write_to_file.setObjectName(_fromUtf8("write_to_file"))
        self.write_to_file.setCheckable(True)

        #-------- Message box --------#
        self.message_box = QtWidgets.QTextEdit(LiveAudio)
        self.message_box.setGeometry(QtCore.QRect(10, 240, 521, 21))
        self.message_box.setObjectName(_fromUtf8("message_box"))
        self.message_box.setReadOnly(True)

        self.setup_audio_recorder()

        #-------- Soundcard selection --------#
        self.label = QtWidgets.QLabel(LiveAudio)
        self.label.setGeometry(QtCore.QRect(400, 270, 81, 17))
        self.label.setObjectName(_fromUtf8("label"))
        self.soundcard_idx = SoundCardBox(LiveAudio, self.recorder)
        self.soundcard_idx.setGeometry(QtCore.QRect(480, 270, 71, 27))
        self.soundcard_idx.setObjectName(_fromUtf8("soundcard_idx"))

        #-------- Threshold selection --------#
        self.threshold_spinBox = QtWidgets.QSpinBox(LiveAudio)
        self.threshold_spinBox.setGeometry(QtCore.QRect(480, 300, 71, 27))
        self.threshold_spinBox.setObjectName(_fromUtf8("threshold_spinBox"))
        self.threshold_spinBox.setMaximum(100000)
        self.threshold_label = QtWidgets.QLabel(LiveAudio)
        self.threshold_label.setGeometry(QtCore.QRect(400, 300, 71, 20))
        self.threshold_label.setObjectName(_fromUtf8("threshold_label"))

        #-------- Graphing Widgets --------#
        self.audio_plot = AudioPlotWidget(LiveAudio, self.recorder)
        self.audio_plot.setGeometry(QtCore.QRect(10, 20, 381, 211))
        self.audio_plot.setObjectName(_fromUtf8("graphicsView"))
        self.spectrogram = pg.PlotWidget(LiveAudio)
        self.spectrogram.setGeometry(QtCore.QRect(395, 20, 361, 211))
        self.spectrogram.setObjectName(_fromUtf8("spectrogram"))

        self.audio_manager = AudioManager(self)
        self.spec_manager = SpecManager(self)

        #-------- Connections --------#
#        self.clicked=QtCore.Qt.SIGNAL("clicked()")
#        self.start_recording_button.clicked.connect(self.start_recording_button, QtCore.SIGNAL("clicked()"), self.start_recording)
        self.start_recording_button.clicked.connect(self.start_recording)
        #self.stop_recording_button.connect(self.stop_recording_button, QtCore.SIGNAL("clicked()"), self.stop_recording)
        self.stop_recording_button.clicked.connect(self.stop_recording)
        #self.cancel_button.connect(self.cancel_button, QtCore.SIGNAL("clicked()"), self.quit_program)
        self.cancel_button.clicked.connect(self.quit_program)

        self.write_to_file.toggled.connect(self.write_to_file_clicked)

        #self.soundcard_idx.connect(self.soundcard_idx, QtCore.SIGNAL("valueChanged(int)"), self.update_selected_soundcard)
        self.soundcard_idx.valueChanged.connect(self.update_selected_soundcard)
        self.threshold_spinBox.valueChanged.connect(self.update_threshold)

        self.retranslateUi(LiveAudio)
        QtCore.QMetaObject.connectSlotsByName(LiveAudio)


    def retranslateUi(self, LiveAudio):
        LiveAudio.setWindowTitle(_translate("LiveAudio", "LiveAudio", None))
        self.cancel_button.setText(_translate("LiveAudio", "Cancel", None))
        self.start_recording_button.setText(_translate("LiveAudio", "Start recording", None))
        self.stop_recording_button.setText(_translate("LiveAudio", "Stop recording", None))
        self.label.setText(_translate("LiveAudio", "Soundcard", None))
        self.write_to_file.setText(_translate("LiveAudio", "Write to file", None))
        self.threshold_label.setText(_translate("LiveAudio", "Threshold", None))

    def setup_audio_recorder(self):
        self.recorder = ar.AudioRecord()
        self.recorder.init_config(self.config)

    def start_recording(self):
        try:
            self.recorder.start_return_data()
        except:
            self.message_box.setText(QtCore.QString("Error starting recording. Try another soundcard."))
            return
        self.message_box.setText(QtCore.QString("Recording..."))
        self.audio_recording = True
        self.audio_manager.start()
        self.spec_manager.start()

    def stop_recording(self):
        self.recorder.stop()
        self.message_box.setText(QtCore.QString("Mic off."))
        self.audio_manager.stop()
        self.spec_manager.stop()

    #@QtCore.pyqtSlot(bool)  #<<== the missing link
    def write_to_file_clicked(self, checked):
        if checked:
            if not self.audio_manager.writing:
                print("start")
                self.audio_manager.start_write_to_file()
        else:
            if self.audio_manager.writing:
                print("stop")
                self.audio_manager.stop_write_to_file()

    def updateUi(self):
        self.start_recording_button.setEnabled(True)
        self.cancel_button.setEnabled(True)

    def update_selected_soundcard(self, i):
        print(i)
        self.recorder.set_sound_card(i)

    def update_threshold(self, i):
        self.recorder.params['threshold'] = i

    def quit_program(self):
        if self.audio_recording:
            self.stop_recording()
        sys.exit()
