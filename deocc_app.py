import numpy as np
from PyQt5.QtWidgets import (QAction, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QMenu, QPushButton, QGridLayout, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QImage, QPixmap)
from PyQt5.QtTest import QTest

import utils

import time

class Application(QWidget):

    def __init__(self, parent, dims, debug=False):
        super().__init__(parent)
        swidth, sheight = dims
        self.main_width, self.main_height = swidth * 0.9, sheight * 0.9
        self.debug = debug

        self.imageLabel = QLabel(self)

        # buttons
        btnsWidth = 120
        self.btnGrid = QGridLayout()
        self.openBtn = QPushButton("Open")
        self.openBtn.setFixedWidth(btnsWidth)
        self.openBtn.clicked.connect(self.window().fileOpen)
        self.deoccBtn = QPushButton("De-occlusion")
        self.deoccBtn.setFixedWidth(btnsWidth)
        self.deoccBtn.clicked.connect(self.window().editDeocc)
        self.showBtn = QPushButton("Show Objects")
        self.showBtn.setFixedWidth(btnsWidth)
        self.showBtn.clicked.connect(self.paste_isolated)
        self.insertBtn = QPushButton("Insert")
        self.insertBtn.setFixedWidth(btnsWidth)
        self.insertBtn.clicked.connect(self.window().insertObject)
        self.resetBtn = QPushButton("Reset")
        self.resetBtn.setFixedWidth(btnsWidth)
        self.resetBtn.clicked.connect(self.reset)
        self.saveasBtn = QPushButton("Save As")
        self.saveasBtn.setFixedWidth(btnsWidth)
        self.saveasBtn.clicked.connect(self.window().fileSaveAs)
        self.btnGrid.addWidget(self.openBtn, 0, 0, Qt.AlignRight)
        self.btnGrid.addWidget(self.deoccBtn, 1, 0, Qt.AlignRight)
        self.btnGrid.addWidget(self.showBtn, 2, 0, Qt.AlignRight)
        self.btnGrid.addWidget(self.resetBtn, 3, 0, Qt.AlignRight)
        self.btnGrid.addWidget(self.insertBtn, 4, 0, Qt.AlignRight)
        self.btnGrid.addWidget(self.saveasBtn, 5, 0, Qt.AlignRight)

        picLayout = QHBoxLayout()
        picLayout.addWidget(self.imageLabel, Qt.AlignCenter)
        picLayout.addLayout(self.btnGrid, Qt.AlignLeft)
        self.setLayout(picLayout)
        self.imageLabel.mousePressEvent = self.mousePressEventPic
        self.imageLabel.mouseMoveEvent = self.mouseMoveEventPic
        self.imageLabel.mouseReleaseEvent = self.mouseReleaseEventPic
        self.imageLabel.contextMenuEvent = self.contextMenuEventPic

        #self.imageLabel.setMouseTracking(True)

        # 
        self.canvas = None
        self.mask = None
        self.canvas_show = QImage()

        # status
        self.deocc_flag = False

    def init_image(self, image_ori):
        self.deocc_flag = False
        self.image_ori = image_ori
        self.image_height = self.image_ori.shape[0]
        self.image_width = self.image_ori.shape[1]
        self.canvas = self.image_ori.copy()
        self.mask = np.zeros((self.image_height, self.image_width), dtype=np.int)
        self.showCanvas()
        QApplication.setOverrideCursor(Qt.ArrowCursor)

    def reset(self):
        self.objects = [o.copy() for o in self.objects_ori]
        self.shift = [[0, 0] for o in self.objects_ori]
        self.scale = [1. for o in self.objects_ori]
        self.degree = [0. for o in self.objects_ori]
        self.center = [utils.compute_center(o) for o in self.objects_ori]
        self.order = np.arange(len(self.objects))
        self.paste_all()

    def paste_isolated(self):
        self.paste(self.bkg)
        QTest.qWait(1000)
        for i in range(len(self.objects)):
            ind = self.order[i]
            self.paste(self.bkg)
            self.paste(self.objects[ind], ind + 1)
            self.showCanvas()
            QTest.qWait(1000)
        self.paste_all()

    def init_components(self, bkg, objs):
        self.bkg = bkg
        self.objects_ori = objs
        self.deocc_flag = True
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QTest.qWait(500)
        self.reset()
        QApplication.setOverrideCursor(Qt.OpenHandCursor)

    def pad(self, obj):
        h, w = obj.shape[:2]
        obj_canvas = np.zeros((self.image_height, self.image_width, 4), dtype=np.uint8)
        offy = (self.image_height - h) // 2
        offx = (self.image_width - w) // 2
        obj_canvas[offy : offy + h, offx : offx + w, :] = obj
        return obj_canvas

    def insert_object(self, obj):
        if not self.deocc_flag:
            return
        obj = self.pad(obj)
        self.objects_ori.append(obj)
        self.objects.append(obj.copy())
        self.shift.append([0, 0])
        self.scale.append(1.)
        self.degree.append(0.)
        self.center.append(utils.compute_center(obj))
        self.order = np.array(self.order.tolist() + [len(self.objects) - 1])
        self.paste_all()

    def paste_all(self):
        self.paste(self.bkg, 0)
        for i in range(len(self.objects)):
            ind = self.order[i]
            self.paste(self.objects[ind], ind + 1) # ind=0 is background
        self.showCanvas()

    def getObject(self, coord):
        x, y = coord
        x /= self.ratio
        y /= self.ratio
        return self.mask[int(y), int(x)]

    def mousePressEventPic(self, event):
        x, y = event.pos().x(), event.pos().y()
        if event.button() == Qt.LeftButton:
            QApplication.setOverrideCursor(Qt.ClosedHandCursor)
            if not self.deocc_flag:
                return
            if x >= self.pixmap_scope[0] or y >= self.pixmap_scope[1]:
                return
            this_obj = self.getObject((x, y))
            if self.debug:
                self.window().updateStatus("left: {}, {}, {}".format(x, y, this_obj))
            self.this_obj = this_obj
            self.this_pos = (x, y)

    def mouseMoveEventPic(self, event):
        x, y = event.pos().x(), event.pos().y()
        if event.buttons() == Qt.LeftButton:
            if not self.deocc_flag or self.this_obj == 0:
                return
            QApplication.setOverrideCursor(Qt.ClosedHandCursor)
            move_x = (x - self.this_pos[0]) / self.ratio
            move_y = (y - self.this_pos[1]) / self.ratio
            self.this_pos = (x, y)
            self.shift[self.this_obj - 1][0] += move_x
            self.shift[self.this_obj - 1][1] += move_y
            self.center[self.this_obj - 1][0] += move_x
            self.center[self.this_obj - 1][1] += move_y
            self.manipulate()
        #elif event.buttons() == Qt.NoButton:
        #    if x >= self.pixmap_scope[0] or y >= self.pixmap_scope[1]:
        #        QApplication.restoreOverrideCursor()
        #    else:
        #        tmp_obj = self.getObject((x, y))
        #        if tmp_obj == 0:
        #            QApplication.restoreOverrideCursor()
        #        else:
        #            QApplication.setOverrideCursor(Qt.OpenHandCursor)

    def mouseReleaseEventPic(self, event):
        QApplication.setOverrideCursor(Qt.OpenHandCursor)

    def objectForward(self):
        pos = np.where(self.order == self.this_obj - 1)[0].item()
        if pos < self.order.shape[0] - 1:
            tmp = self.order[pos + 1]
            self.order[pos + 1] = self.this_obj - 1
            self.order[pos] = tmp
            self.paste_all()

    def objectBackward(self):
        pos = np.where(self.order == self.this_obj - 1)[0].item()
        if pos > 0:
            tmp = self.order[pos - 1]
            self.order[pos - 1] = self.this_obj - 1
            self.order[pos] = tmp
            self.paste_all()
 
    def objectFront(self):
        pos = np.where(self.order == self.this_obj - 1)[0].item()
        if pos < self.order.shape[0] - 1:
            self.order = np.concatenate(
                [self.order[:pos], self.order[pos + 1:],
                np.array([self.this_obj - 1], dtype=np.int64)])
            self.paste_all()

    def objectBottom(self):
        pos = np.where(self.order == self.this_obj - 1)[0].item()
        if pos > 0:
            self.order = np.concatenate(
                [np.array([self.this_obj - 1], dtype=np.int64),
                self.order[:pos], self.order[pos + 1:]])
            self.paste_all()

    def objectSave(self):
        obj = self.objects[self.this_obj - 1]
        crop_obj = utils.crop_padding(
            obj, utils.mask_to_bbox(obj[:,:,3]), pad_value=(0,0,0,0))
        self.window().objectSaveAs(crop_obj)

    def contextMenuEventPic(self, event):
        if not self.deocc_flag:
            return
        x, y = event.pos().x(), event.pos().y()
        this_obj = self.getObject((x, y))
        if self.debug:
            self.window().updateStatus("right: {}, {}, {}".format(x, y, this_obj))
        if this_obj == 0:
            return
        self.this_obj = this_obj

        menu = QMenu()
        fwAction = QAction("Bring forward", self)
        fwAction.triggered.connect(self.objectForward)
        bwAction = QAction("Send backward", self)
        bwAction.triggered.connect(self.objectBackward)
        frtAction = QAction("Bring to front", self)
        frtAction.triggered.connect(self.objectFront)
        btmAction = QAction("Send to bottom", self)
        btmAction.triggered.connect(self.objectBottom)
        saveAction = QAction("Save object", self)
        saveAction.triggered.connect(self.objectSave)

        menu.addAction(fwAction)
        menu.addAction(bwAction)
        menu.addAction(frtAction)
        menu.addAction(btmAction)
        menu.addAction(saveAction)
        menu.exec_(self.mapToGlobal(event.pos()))
        
    def moveObject(self, image, move_x, move_y):
        bbox = [-move_x, -move_y, image.shape[1], image.shape[0]]
        return utils.crop_padding(image, bbox, pad_value=(0,0,0,0))

    def resizeObject(self, image, ratio):
        if ratio == 1:
            return image
        else:
            return utils.resize_with_center(image, self.center[self.this_obj - 1], ratio)

    def rotateObject(self, image, degree):
        if degree == 0:
            return image
        else:
            return utils.rotate_with_center(image, self.center[self.this_obj - 1], degree)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up and self.scale[self.this_obj - 1] > 0.2:
            self.scale[self.this_obj - 1] -= 0.05
        elif event.key() == Qt.Key_Down:
            self.scale[self.this_obj - 1] += 0.05
        elif event.key() == Qt.Key_Left:
            self.degree[self.this_obj - 1] += 3
        elif event.key() == Qt.Key_Right:
            self.degree[self.this_obj - 1] -= 3
        else:
            return
        self.manipulate()

    def manipulate(self):
        # move
        self.objects[self.this_obj - 1] = self.moveObject(
            self.objects_ori[self.this_obj - 1],
            self.shift[self.this_obj - 1][0], self.shift[self.this_obj - 1][1])
        # resize
        self.objects[self.this_obj - 1] = self.resizeObject(
            self.objects[self.this_obj - 1], self.scale[self.this_obj - 1])
        # rotate
        self.objects[self.this_obj - 1] = self.rotateObject(
            self.objects[self.this_obj - 1], self.degree[self.this_obj - 1])

        self.paste_all()

    def paste(self, image, ind=None):
        if image.shape[2] == 4:
            alpha = image[:,:,3:4].astype(np.float32) / 255
            region = np.where(image[:,:,3] > 0)
            self.canvas[region[0], region[1], :] = \
                self.canvas[region[0], region[1], :] * (1 - alpha[region[0], region[1], :]) + \
                image[region[0], region[1], :3] * alpha[region[0], region[1], :]
            self.mask[region[0], region[1]] = ind
        else:
            self.canvas[...] = image.copy()
            self.mask.fill(0)

    def showCanvas(self):
        if self.canvas is not None:
            self.canvas_show = QImage(
                self.canvas.data, self.image_width, self.image_height,
                3 * self.image_width, QImage.Format_RGB888)
        else:
            self.canvas_show = QImage()
        pixmap = QPixmap.fromImage(self.canvas_show)
        #pixmap = pixmap.scaled(self.main_width, self.main_height, Qt.KeepAspectRatio)
        self.pixmap_scope = (pixmap.size().width(), pixmap.size().height())
        self.ratio = pixmap.size().height() / float(self.image_height)
        self.imageLabel.setFixedHeight(pixmap.size().height())
        self.imageLabel.setFixedWidth(pixmap.size().width())
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.show()
