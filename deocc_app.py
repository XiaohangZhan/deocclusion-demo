import numpy as np
from PyQt5.QtWidgets import (QAction, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QImage, QPixmap)
import utils

import time

class Application(QWidget):

    def __init__(self, parent, dims):
        super().__init__(parent)
        swidth, sheight = dims
        self.main_width, self.main_height = swidth * 0.9, sheight * 0.9

        self.imageLabel = QLabel()
        picLayout = QVBoxLayout()
        picLayout.addWidget(self.imageLabel, Qt.AlignCenter)
        self.setLayout(picLayout)
        self.imageLabel.mousePressEvent = self.mousePressEventPic
        self.imageLabel.mouseMoveEvent = self.mouseMoveEventPic

        # 
        self.canvas = None
        self.mask = None
        self.canvas_show = QImage()

        # status
        self.deocc_flag = False

    def init_image(self, image_ori):
        self.image_ori = image_ori
        self.image_height = self.image_ori.shape[0]
        self.image_width = self.image_ori.shape[1]
        self.canvas = self.image_ori.copy()
        self.mask = np.zeros((self.image_height, self.image_width), dtype=np.int)
        self.showCanvas()

    def reset(self):
        self.objects = [o.copy() for o in self.objects_ori]
        self.shift = [[0, 0] for o in self.objects_ori]
        self.scale = [1. for o in self.objects_ori]
        self.center = [utils.compute_center(o) for o in self.objects_ori]
        self.order = np.arange(len(self.objects))
        self.paste_all()

    def init_components(self, bkg, objs):
        self.bkg = bkg
        self.objects_ori = objs
        self.deocc_flag = True
        self.reset()

    def paste_all(self):
        self.paste(self.bkg)
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
        if event.button() == Qt.LeftButton:
            if not self.deocc_flag:
                return
            x, y = event.pos().x(), event.pos().y()
            if x >= self.pixmap_scope[0] or y >= self.pixmap_scope[1]:
                return
            self.this_obj = self.getObject((x, y))
            if self.this_obj == 0:
                return
            self.this_pos = (x, y)
            self.window().updateStatus("{}, {}, {}".format(x, y, self.this_obj))

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
      
    def contextMenuEvent(self, event):
        if not self.deocc_flag:
            return
        x, y = event.pos().x(), event.pos().y()
        self.this_obj = self.getObject((x, y))

        menu = QMenu()
        self.window().updateStatus("right obj: {}".format(self.this_obj))
        fwAction = QAction("Bring forward", self)
        fwAction.triggered.connect(self.objectForward)
        bwAction = QAction("Send backward", self)
        bwAction.triggered.connect(self.objectBackward)
        frtAction = QAction("Bring to front", self)
        frtAction.triggered.connect(self.objectFront)
        btmAction = QAction("Send to bottom", self)
        btmAction.triggered.connect(self.objectBottom)

        menu.addAction(fwAction)
        menu.addAction(bwAction)
        menu.addAction(frtAction)
        menu.addAction(btmAction)
        menu.exec_(self.mapToGlobal(event.pos()))
        
    def moveObject(self, image, move_x, move_y):
        bbox = [-move_x, -move_y, image.shape[1], image.shape[0]]
        return utils.crop_padding(image, bbox, pad_value=(0,0,0,0))

    def resizeObject(self, image, ratio):
        if ratio == 1:
            return image
        else:
            return utils.resize_with_center(image, self.center[self.this_obj - 1], ratio)

    def mouseMoveEventPic(self, event):
        if not self.deocc_flag:
            return
        x, y = event.pos().x(), event.pos().y()
        move_x = (x - self.this_pos[0]) / self.ratio
        move_y = (y - self.this_pos[1]) / self.ratio
        self.this_pos = (x, y)
        self.shift[self.this_obj - 1][0] += move_x
        self.shift[self.this_obj - 1][1] += move_y
        self.center[self.this_obj - 1][0] += move_x
        self.center[self.this_obj - 1][1] += move_y
        self.manipulate()

    def keyPressEvent(self, event):
        self.window().updateStatus(str(event.key()))
        if event.key() == Qt.Key_Left and self.scale[self.this_obj - 1] > 0.2:
            self.scale[self.this_obj - 1] -= 0.05
        elif event.key() == Qt.Key_Right:
            self.scale[self.this_obj - 1] += 0.05
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

    def showCanvas(self):
        if self.canvas is not None:
            self.canvas_show = QImage(
                self.canvas.data, self.image_width, self.image_height,
                3 * self.image_width, QImage.Format_RGB888)
        else:
            self.canvas_show = QImage()
            self.window().updateStatus("invalid image")
        pixmap = QPixmap.fromImage(self.canvas_show)
        pixmap = pixmap.scaled(self.main_width, self.main_height, Qt.KeepAspectRatio)
        self.pixmap_scope = (pixmap.size().width(), pixmap.size().height())
        self.ratio = pixmap.size().height() / float(self.image_height)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.show()
