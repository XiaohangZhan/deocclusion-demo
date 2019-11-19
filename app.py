# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore, QtTest
import data_io, action_io
import platform
import json
import os
import sys
import cv2
import numpy as np
from datetime import datetime
OS = platform.system()

class Application(QtGui.QWidget):

    def __init__(self, ):
        super(Application, self).__init__()

    def init_gui(self):
        self.image_label = QLabel

    def mouse_move_event(self):
        x, y = event.pos().x(), event.pos().y()

    def show(self):
        self.
