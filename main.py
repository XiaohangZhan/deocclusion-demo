import sys
import os
import time

from PIL import Image
import numpy as np

from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QMainWindow, QLabel, QDesktopWidget)
from PyQt5.QtGui import (QImage, QImageWriter, QKeySequence, QPixmap)
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        screen = QDesktopWidget().screenGeometry()
        self.swidth, self.sheight = screen.width(), screen.height()
        self.setGeometry(0, 0, self.swidth, self.sheight)

        # UI
        self.canvas = None
        self.canvas_show = QImage()
        self.filename = None
        self.main_width, self.main_height = self.swidth * 0.9, self.sheight * 0.9
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.imageLabel)

        # action
        fileOpenAction = self.createAction(
            '&Open...', slot=self.fileOpen, shortcut=QKeySequence.Open,
            tip='open an existing image file')
        fileSaveAction = self.createAction(
            '&Save...', slot=self.fileSave, shortcut=QKeySequence.Save,
            tip='save image file')
        fileSaveAsAction = self.createAction(
            'Save &As...', slot=self.fileSaveAs, shortcut=QKeySequence.SaveAs,
            tip='save image file using a new name')
        fileQuitAction = self.createAction(
            '&Quit...', slot=self.close, shortcut='Ctrl + Q',
            tip='Close the Application')

        editDeoccAction = self.createAction(
            'Deocclusion', slot=self.editDeocc, shortcut='Ctrl+E', tip='perform de-occlusion')
        editResetAction = self.createAction(
            'Reset', slot=self.reset, shortcut='Ctrl+R', tip='reset image')

        # menu
        self.fileMenu = self.menuBar().addMenu('&File')
        self.fileMenu.addAction(fileOpenAction)
        self.fileMenu.addAction(fileSaveAction)
        self.fileMenu.addAction(fileSaveAsAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(fileQuitAction)

        self.editMenu = self.menuBar().addMenu('&Edit')
        self.editMenu.addAction(editDeoccAction)
        self.editMenu.addAction(editResetAction)
        
        self.setWindowTitle('De-Occlusion')
        self.showMaximized()

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
        obj_list = os.path.join(file_dir, "objects.txt")
        with open(obj_list, 'r') as f:
            lines = f.readlines()
        obj_fns = [os.path.join(file_dir, l.strip()) for l in lines]
        self.bkg = np.array(Image.open(os.path.join(file_dir, "bkg.png")))
        self.objects = [np.array(Image.open(fn)) for fn in obj_fns]
        self.paste(self.bkg)
        QTest.qWait(1000)
        for o in self.objects:
            self.paste(o)
            self.show()
            QTest.qWait(1000)
        self.show()

    def reset(self):
        self.canvas =  self.image_ori.copy()
        self.show()

    def paste(self, image):
        if image.shape[2] == 4:
            region = np.where(image[:,:,3])
            self.canvas[region[0], region[1], :] = image[region[0], region[1], :3]
        else:
            self.canvas[...] = image.copy()

    def fileOpen(self):
        print("call fileOpen")
        self.filename, _ = QFileDialog.getOpenFileName(self, 'Select an image file: ', filter='*.jpg')
        if self.filename is None:
            return
        self.image_ori = np.array(Image.open(self.filename).convert('RGB'))
        self.image_height = self.image_ori.shape[0]
        self.image_width = self.image_ori.shape[1]
        self.canvas = self.image_ori.copy()
        self.show()

    def fileSave(self):
        if self.canvas_show.isNull():
            return
        if self.filename is None:
            self.fileSaveAs()
        else:
            self.canvas_show.save(self.filename, None)

    def fileSaveAs(self):
        if self.canvas_show.isNull():
            return
        fname = self.filename if self.filename else '.'
        formats = ['{0}'.format(str(format).lower()) for format in QImageWriter.supportedImageFormats()]
        formats = ['*.{0}'.format(format[2:5]) for format in formats]
        fname,_ = QFileDialog.getSaveFileName(self, 'Image Editor - Save Image', fname, 'Image files ({0})'.format(' '.join(formats)))
        if fname:
            if '.' not in fname:
                fname += '.png'
            self.filename = fname
            self.fileSave()

    def show(self):
        if self.canvas is not None:
            self.canvas_show = QImage(
                self.canvas.data, self.image_width, self.image_height,
                3 * self.image_width, QImage.Format_RGB888)
        else:
            self.canvas_show = QImage()
        pixmap = QPixmap.fromImage(self.canvas_show)
        pixmap = pixmap.scaled(self.main_width, self.main_height, Qt.KeepAspectRatio)
        self.imageLabel.setPixmap(pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("De-Occlusion")
    form = MainWindow()
    form.show()
    app.exec_()
