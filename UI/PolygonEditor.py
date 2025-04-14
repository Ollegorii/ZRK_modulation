import os

import yaml
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QPen, QPainter, QPixmap, QIcon
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QPushButton, QListWidget, QComboBox,
                             QDialog, QGraphicsScene, QGraphicsTextItem,
                             QMessageBox, QSlider, QStatusBar)

from UI.Enums import ObjectType
from UI.MapGraphicsView import MapGraphicsView
from UI.MapObject import MapObject
from UI.ObjectDialog import ObjectDialog


class PolygonEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Редактор полигона")
        self.setGeometry(100, 100, 1600, 1000)

        # Иконки объектов
        self.icons = {
            ObjectType.AIR_PLANE: self.load_icon("airplane.png", "🛩️", 60),
            ObjectType.HELICOPTER: self.load_icon("helicopter.png", "🚁", 60),
            ObjectType.ANOTHER: self.load_icon("unknown.png", "❓", 60),
            ObjectType.MISSILE_LAUNCHER: self.load_icon("launcher.png", "🚀", 60),
            ObjectType.RADAR: self.load_icon("radar.png", "📡", 60)
        }

        # Конфигурация по умолчанию
        self.default_config = {
            "simulation": {
                "time_step": 1,
                "duration": 10
            },
            "air_environment": {
                "id": 1,
                "position": [0.0, 0.0, 0.0],
                "targets": []
            },
            "combat_control_point": {
                "id": 2,
                "missile_launcher_ids": [],
                "radar_ids": []
            },
            "missile_launchers": [],
            "radars": []
        }

        self.config = self.default_config.copy()
        self.next_ids = {
            ObjectType.AIR_PLANE: 1,
            ObjectType.HELICOPTER: 1,
            ObjectType.ANOTHER: 1,
            ObjectType.MISSILE_LAUNCHER: 3,
            ObjectType.RADAR: 5
        }
        self.default_config_path = "simulation_config.yaml"
        self.init_ui()

    def load_icon(self, filename, fallback, size):
        if os.path.exists(filename):
            pixmap = QPixmap(filename)
            return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setFont(self.font())
            painter.drawText(pixmap.rect(), Qt.AlignCenter, fallback)
            painter.end()
            return pixmap

    def init_ui(self):
        self.setWindowIcon(QIcon(self.icons[ObjectType.AIR_PLANE]))

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Левая панель - управление
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)

        # Выбор типа объекта
        self.object_type_combo = QComboBox()
        self.object_type_combo.setIconSize(QSize(48, 48))
        for obj_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER, ObjectType.ANOTHER,
                         ObjectType.MISSILE_LAUNCHER, ObjectType.RADAR]:
            self.object_type_combo.addItem(
                QIcon(self.icons[obj_type]),
                ObjectType.get_display_name(obj_type),
                obj_type
            )

        self.object_type_combo.currentIndexChanged.connect(self.set_object_type)
        self.current_object_type = ObjectType.AIR_PLANE


        left_layout.addWidget(QLabel("Тип объекта:"))
        left_layout.addWidget(self.object_type_combo)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_btn.clicked.connect(self.delete_object)

        self.save_btn = QPushButton("Сохранить конфиг")
        self.save_btn.setIcon(QIcon.fromTheme("document-save"))
        self.save_btn.clicked.connect(self.save_config)

        self.run_btn = QPushButton("Запуск моделирования")
        self.run_btn.setIcon(QIcon.fromTheme("media-playback-start"))
        self.run_btn.clicked.connect(self.run_simulation)

        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.run_btn)
        left_layout.addLayout(btn_layout)

        # Масштабирование
        zoom_layout = QHBoxLayout()
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 300)
        self.zoom_slider.setValue(20)
        self.zoom_slider.valueChanged.connect(self.zoom_slider_changed)
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)

        zoom_layout.addWidget(self.zoom_out_btn)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_in_btn)
        left_layout.addLayout(zoom_layout)

        # Список объектов
        self.objects_list = QListWidget()
        self.objects_list.itemSelectionChanged.connect(self.select_object)
        left_layout.addWidget(QLabel("Объекты на полигоне:"))
        left_layout.addWidget(self.objects_list)

        # Правая панель - карта
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Сцена и вид
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-15000, -15000, 30000, 30000)

        self.view = MapGraphicsView(self.scene, self)  # Передаем self как parent
        self.view.setMinimumSize(800, 800)
        self.view.zoomChanged.connect(self.update_zoom_slider)
        right_layout.addWidget(self.view)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Инициализация
        self.draw_grid()
        self.update_status()

    def set_object_type(self, index):
        self.current_object_type = self.object_type_combo.itemData(index)
        self.status_bar.showMessage(f"Выбран тип: {ObjectType.get_display_name(self.current_object_type)}", 2000)

    def add_object(self, position):
        default_id = self.next_ids[self.current_object_type]
        dialog = ObjectDialog(self.current_object_type, position, default_id, self)
        if dialog.exec_() == QDialog.Accepted:
            obj_data = dialog.get_object_data()
            self.next_ids[self.current_object_type] += 1

            # Добавляем объект в конфиг
            if self.current_object_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER, ObjectType.ANOTHER]:
                self.config["air_environment"]["targets"].append(obj_data)
            elif self.current_object_type == ObjectType.MISSILE_LAUNCHER:
                self.config["missile_launchers"].append(obj_data)
                self.config["combat_control_point"]["missile_launcher_ids"].append(obj_data["id"])
            elif self.current_object_type == ObjectType.RADAR:
                self.config["radars"].append(obj_data)
                self.config["combat_control_point"]["radar_ids"].append(obj_data["id"])

            self.update_scene()
            self.update_objects_list()

    def draw_grid(self):
        # Оси
        pen = QPen(QColor(100, 100, 255, 150), 2)
        self.scene.addLine(-15000, 0, 15000, 0, pen)
        self.scene.addLine(0, -15000, 0, 15000, pen)

        # Сетка
        pen = QPen(QColor(200, 200, 200, 100), 1)
        for i in range(-15000, 15001, 1000):
            if i != 0:
                self.scene.addLine(i, -15000, i, 15000, pen)
                self.scene.addLine(-15000, i, 15000, i, pen)

    def update_scene(self):
        # Очищаем только объекты
        for item in self.scene.items():
            if isinstance(item, (MapObject, QGraphicsTextItem)):
                self.scene.removeItem(item)

        # Рисуем объекты
        for target in self.config["air_environment"]["targets"]:
            self.draw_map_object(target["position"], target["type"], target.get("id", ""))

        for launcher in self.config["missile_launchers"]:
            self.draw_map_object(launcher["position"], "MISSILE_LAUNCHER", launcher.get("id", ""))

        for radar in self.config["radars"]:
            self.draw_map_object(radar["position"], "RADAR", radar.get("id", ""))

    def draw_map_object(self, position, obj_type, obj_id):
        enum_type = ObjectType(obj_type) if isinstance(obj_type, str) else obj_type
        icon = self.icons.get(enum_type, self.icons[ObjectType.AIR_PLANE])
        obj = MapObject(icon, enum_type, obj_id)
        obj.setPos(position[0] - icon.width() / 2, position[1] - icon.height() / 2)
        self.scene.addItem(obj)

        # Подпись
        label = QGraphicsTextItem(f"{ObjectType.get_display_name(enum_type)} {obj_id}")
        label.setPos(position[0] - label.boundingRect().width() / 2,
                     position[1] - icon.height() / 2 - 30)
        self.scene.addItem(label)

    def update_objects_list(self):
        self.objects_list.clear()

        for target in self.config["air_environment"]["targets"]:
            display_name = ObjectType.get_display_name(ObjectType(target["type"]))
            self.objects_list.addItem(f"{display_name} {target.get('id', '')}")

        for launcher in self.config["missile_launchers"]:
            display_name = ObjectType.get_display_name(ObjectType.MISSILE_LAUNCHER)
            self.objects_list.addItem(f"{display_name} {launcher.get('id', '')}")

        for radar in self.config["radars"]:
            display_name = ObjectType.get_display_name(ObjectType.RADAR)
            self.objects_list.addItem(f"{display_name} {radar.get('id', '')}")

        self.update_status()

    def select_object(self):
        selected = self.objects_list.currentItem()
        if selected:
            for item in self.scene.items():
                if isinstance(item, MapObject):
                    display_name = ObjectType.get_display_name(item.obj_type)
                    if f"{display_name} {item.obj_id}" == selected.text():
                        self.view.centerOn(item)
                        break

    def delete_object(self):
        selected = self.objects_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Не выбран объект для удаления")
            return

        item_text = selected.text()

        # Удаляем из конфига
        for target in self.config["air_environment"]["targets"]:
            display_name = ObjectType.get_display_name(ObjectType(target["type"]))
            if f"{display_name} {target.get('id', '')}" == item_text:
                self.config["air_environment"]["targets"].remove(target)
                self.update_scene()
                self.update_objects_list()
                return

        for launcher in self.config["missile_launchers"]:
            display_name = ObjectType.get_display_name(ObjectType.MISSILE_LAUNCHER)
            if f"{display_name} {launcher.get('id', '')}" == item_text:
                self.config["missile_launchers"].remove(launcher)
                if launcher["id"] in self.config["combat_control_point"]["missile_launcher_ids"]:
                    self.config["combat_control_point"]["missile_launcher_ids"].remove(launcher["id"])
                self.update_scene()
                self.update_objects_list()
                return

        for radar in self.config["radars"]:
            display_name = ObjectType.get_display_name(ObjectType.RADAR)
            if f"{display_name} {radar.get('id', '')}" == item_text:
                self.config["radars"].remove(radar)
                if radar["id"] in self.config["combat_control_point"]["radar_ids"]:
                    self.config["combat_control_point"]["radar_ids"].remove(radar["id"])
                self.update_scene()
                self.update_objects_list()
                return

    def zoom_in(self):
        self.view.zoom(1.25)

    def zoom_out(self):
        self.view.zoom(0.8)

    def zoom_slider_changed(self, value):
        scale = value / 100.0
        self.view.resetTransform()
        self.view.scale(scale, scale)
        self.view.scale_factor = scale

    def update_zoom_slider(self, scale):
        self.zoom_slider.setValue(int(scale * 100))

    def update_status(self):
        count = (len(self.config["air_environment"]["targets"]) +
                 len(self.config["missile_launchers"]) +
                 len(self.config["radars"]))
        self.status_bar.showMessage(f"Объектов: {count} | Масштаб: {int(self.view.scale_factor * 100)}%")

    def save_config(self):
        try:
            # Формируем конфиг с реальными данными
            output_config = {
                "simulation": {
                    "time_step": self.config["simulation"]["time_step"],
                    "duration": self.config["simulation"]["duration"]
                },
                "air_environment": {
                    "id": self.config["air_environment"]["id"],
                    "position": self.config["air_environment"]["position"],
                    "targets": self.config["air_environment"]["targets"]
                },
                "combat_control_point": {
                    "id": self.config["combat_control_point"]["id"],
                    "missile_launcher_ids": self.config["combat_control_point"]["missile_launcher_ids"],
                    "radar_ids": self.config["combat_control_point"]["radar_ids"]
                },
                "missile_launchers": self.config["missile_launchers"],
                "radars": self.config["radars"]
            }

            # Сохраняем в файл с комментариями
            with open(self.default_config_path, 'w', encoding='utf-8') as file:
                file.write("# Конфигурация моделирования\n")
                yaml.dump({"simulation": output_config["simulation"]}, file, allow_unicode=True, sort_keys=False)

                file.write("\n# Конфигурация воздушной обстановки\n")
                yaml.dump({"air_environment": output_config["air_environment"]}, file, allow_unicode=True,
                          sort_keys=False)

                file.write("\n# Пункт боевого управления\n")
                yaml.dump({"combat_control_point": output_config["combat_control_point"]}, file, allow_unicode=True,
                          sort_keys=False)

                file.write("\n# Пусковые установки\n")
                yaml.dump({"missile_launchers": output_config["missile_launchers"]}, file, allow_unicode=True,
                          sort_keys=False)

                file.write("\n# Радары\n")
                yaml.dump({"radars": output_config["radars"]}, file, allow_unicode=True, sort_keys=False)

            QMessageBox.information(self, "Успех",
                                    f"Конфигурация сохранена в файл:\n{os.path.abspath(self.default_config_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить конфигурацию:\n{str(e)}")

    def run_simulation(self):
        QMessageBox.information(self, "Моделирование", "Моделирование запущено с текущей конфигурацией")
