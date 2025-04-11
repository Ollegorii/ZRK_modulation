import sys
import yaml
import os
from enum import Enum
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QPushButton, QListWidget, QComboBox,
                             QDialog, QDialogButtonBox, QFormLayout, QGraphicsView,
                             QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem,
                             QMessageBox, QSlider, QToolBar, QStatusBar, QLineEdit)
from PyQt5.QtCore import Qt, QPointF, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QPen, QBrush, QPainter, QPixmap, QIcon, QCursor



class MapGraphicsView(QGraphicsView):
    zoomChanged = pyqtSignal(float)

    def __init__(self, scene=None, parent=None):
        super().__init__(scene, parent)
        self.parent_window = parent  # Сохраняем ссылку на родительское окно
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setInteractive(True)
        self.scale_factor = 0.2
        self.min_scale = 0.1
        self.max_scale = 3.0

    def wheelEvent(self, event):
        zoom_in = event.angleDelta().y() > 0
        zoom_factor = 1.25 if zoom_in else 0.8
        self.zoom(zoom_factor)

    def zoom(self, factor):
        new_scale = self.scale_factor * factor
        if new_scale < self.min_scale:
            factor = self.min_scale / self.scale_factor
        elif new_scale > self.max_scale:
            factor = self.max_scale / self.scale_factor

        self.scale(factor, factor)
        self.scale_factor *= factor
        self.zoomChanged.emit(self.scale_factor)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_window.add_object(self.mapToScene(event.pos()))
        else:
            super().mouseDoubleClickEvent(event)