from PyQt5.QtWidgets import (QGraphicsPixmapItem)
from PyQt5.QtCore import Qt


class MapObject(QGraphicsPixmapItem):
    def __init__(self, pixmap, obj_type, obj_id, parent=None):
        super().__init__(pixmap, parent)
        self.obj_type = obj_type
        self.obj_id = obj_id
        self.trajectory = None  # Ссылка на линию траектории
        self.setTransformationMode(Qt.SmoothTransformation)
        self.setCursor(Qt.ArrowCursor)