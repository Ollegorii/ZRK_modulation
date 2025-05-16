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
from PyQt5.QtGui import QColor, QPen, QBrush, QPainter, QPixmap, QIcon, QCursor, QTransform


class MapGraphicsView(QGraphicsView):
    zoomChanged = pyqtSignal(float)

    def __init__(self, scene=None, parent=None):
        super().__init__(scene, parent)
        self.parent_window = parent  # Сохраняем ссылку на родительское окно
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setInteractive(True)
        self.scale_factor = 0.05
        self.setTransform(QTransform().scale(self.scale_factor, self.scale_factor))
        self.min_scale = 0.001
        self.max_scale = 1.0

    def wheelEvent(self, event):
        zoom_factor = 1.2
        if event.angleDelta().y() < 0:
            zoom_factor = 1.0 / zoom_factor

        new_scale = self.scale_factor * zoom_factor
        if self.min_scale <= new_scale <= self.max_scale:
            self.scale(zoom_factor, zoom_factor)
            self.scale_factor = new_scale
            self.zoomChanged.emit(self.scale_factor)

    def zoom(self, factor):
        new_scale = self.scale_factor * factor
        if self.min_scale <= new_scale <= self.max_scale:
            self.scale(factor, factor)
            self.scale_factor = new_scale
            self.zoomChanged.emit(self.scale_factor)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_window.add_object(self.mapToScene(event.pos()))
        else:
            super().mouseDoubleClickEvent(event)
