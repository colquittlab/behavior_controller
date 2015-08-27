import sys
from PyQt4.QtGui import QApplication,QDialog
from PyQt4 import QtCore, QtGui
from qt.liveaudio import Ui_LiveAudio

# def MainWindow(QtGui.QMainWindow):
#     QtGui.QMainWindow.__init__(self)

#     def closeEvent(self, event):

def main(argv):
    app = QApplication(sys.argv)
    window = QtGui.QMainWindow()
#    window = MainWindow()
    if len(argv) > 1:
        ui = Ui_LiveAudio(argv[1])
    else:
        ui = Ui_LiveAudio(None)
    ui.setupUi(window)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main(sys.argv)
