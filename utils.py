import numpy as np

from PyQt5 import QtGui

def image_to_pixmap(img):
    h,w,channel = img.shape
    cv2.cvtColor(img, cv2.cv.CV_BGR2RGB, img)
    qimg = QtGui.QImage(img.data, w, h, channel * w, QtGui.QImage.Format_RGB888)
    pixmap = QtGui.QPixmap.fromImage(qimg)
    return pixmap
