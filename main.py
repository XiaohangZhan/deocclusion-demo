import sys
import os
import time
from glob import glob
import cv2

from PIL import Image
import numpy as np

from PyQt5.QtWidgets import (QAction, QApplication, QDockWidget, QFileDialog, QMainWindow, QLabel, QDesktopWidget, QListWidget)
from PyQt5.QtGui import (QImage, QImageWriter, QKeySequence, QPixmap)
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

import deocc_app

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.debug = False
        screen = QDesktopWidget().screenGeometry()
        #self.swidth, self.sheight = screen.width(), screen.height()
        self.swidth, self.sheight = 800, 560
        self.setGeometry(0, 0, self.swidth, self.sheight)

        # UI
        self.filename = None
        self.addMainApp()

        # log
        if self.debug:
            logDockWidget =QDockWidget('Log', self)
            logDockWidget.setObjectName('LogDockWidget')
            logDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
            self.listWidget = QListWidget()
            logDockWidget.setWidget(self.listWidget)
            self.addDockWidget(Qt.RightDockWidgetArea, logDockWidget)

        # action
        fileOpenAction = self.createAction(
            '&Open...', slot=self.fileOpen, shortcut=QKeySequence.Open,
            tip='open an existing image file')
        #fileSaveAction = self.createAction(
        #    '&Save...', slot=self.fileSave, shortcut=QKeySequence.Save,
        #    tip='save image file')
        fileSaveAsAction = self.createAction(
            'Save &As...', slot=self.fileSaveAs, shortcut=QKeySequence.SaveAs,
            tip='save image file using a new name')
        fileQuitAction = self.createAction(
            '&Quit...', slot=self.close, shortcut='Ctrl + Q',
            tip='Close the Application')

        editDeoccAction = self.createAction(
            'Deocclusion', slot=self.editDeocc, shortcut='Ctrl+E', tip='perform de-occlusion')
        editResetAction = self.createAction(
            'Reset', slot=self.mainApp.reset, shortcut='Ctrl+R', tip='reset image')

        # menu
        self.fileMenu = self.menuBar().addMenu('&File')
        self.fileMenu.addAction(fileOpenAction)
        #self.fileMenu.addAction(fileSaveAction)
        self.fileMenu.addAction(fileSaveAsAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(fileQuitAction)

        self.editMenu = self.menuBar().addMenu('&Edit')
        self.editMenu.addAction(editDeoccAction)
        self.editMenu.addAction(editResetAction)

        self.setWindowTitle('De-Occlusion')
        #self.showMaximized()
        self.show()

    def addMainApp(self):
        self.mainApp = deocc_app.Application(self, (self.swidth, self.sheight), self.debug)
        self.setCentralWidget(self.mainApp)
        self.keyPressEvent = self.mainApp.keyPressEvent
        
    def createAction(self, text, slot=None, shortcut=None, tip=None, checkable=False, signal='triggered'):
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action

    def editDeocc(self):
        file_dir = self.filename[:-4]
        obj_fns = sorted(glob("{}/obj_*.png".format(file_dir)))[::-1]
        #obj_list = os.path.join(file_dir, "objects.txt")
        #with open(obj_list, 'r') as f:
        #    lines = f.readlines()
        #obj_fns = [os.path.join(file_dir, l.strip()) for l in lines]
        bkg = np.array(Image.open(os.path.join(file_dir, "bkg.png")))
        objects = [np.array(Image.open(fn)) for fn in obj_fns]
        self.mainApp.init_components(bkg, objects)

    def insertObject(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Select an object: ', '.', filter='*.png')
        if filename is None:
            return
        new_object = np.array(Image.open(filename)) # RGBA
        self.mainApp.insert_object(new_object)

    def fileOpen(self):
        self.filename, _ = QFileDialog.getOpenFileName(self, 'Select an image file: ', filter='*.jpg *.png')
        if self.filename is None or len(self.filename) == 0:
            return
        image_ori = np.array(Image.open(self.filename).convert('RGB'))
        self.mainApp.init_image(image_ori)

    def fileSave(self):
        if self.mainApp.canvas_show.isNull():
            return
        if self.filename is None:
            self.fileSaveAs()
        else:
            self.mainApp.canvas_show.save(self.filename, None)

    def fileSaveAs(self):
        if self.mainApp.canvas_show.isNull():
            return
        fname = self.filename if self.filename else '.'
        formats = ['{0}'.format(str(format).lower()) for format in QImageWriter.supportedImageFormats()]
        formats = ['*.{0}'.format(format[2:5]) for format in formats]
        fname, _ = QFileDialog.getSaveFileName(self, 'De-occlusion - Save Image', fname, 'Image files ({0})'.format(' '.join(formats)))
        if fname:
            if '.' not in fname:
                fname += '.png'
            self.filename = fname
            self.fileSave()

    def objectSaveAs(self, obj):
        formats = ['{0}'.format(str(format).lower()) for format in QImageWriter.supportedImageFormats()]
        formats = ['*.{0}'.format(format[2:5]) for format in formats]
        fname, _ = QFileDialog.getSaveFileName(self, 'De-occlusion - Save object', '.', 'Image files ({0})'.format(' '.join(formats)))
        if fname:
            if '.' not in fname:
                fname += '.png'
            obj = np.concatenate([obj[:,:,:3][:,:,::-1], obj[:,:,3:4]], axis=2)
            cv2.imwrite(fname, obj)

    def updateStatus(self, message):
        self.statusBar().showMessage(message, 5000)
        self.listWidget.addItem(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("De-Occlusion")
    form = MainWindow()
    sys.exit(app.exec_())
