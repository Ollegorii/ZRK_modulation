import os
import numpy as np
import yaml
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QPen, QPainter, QPixmap, QIcon, QBrush, QFont
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QPushButton, QListWidget, QComboBox,
                             QDialog, QGraphicsScene, QGraphicsTextItem,
                             QMessageBox, QSlider, QStatusBar, QGraphicsEllipseItem, QGraphicsView)

from UI.Enums import ObjectType
from UI.MapGraphicsView import MapGraphicsView
from UI.MapObject import MapObject
from UI.ObjectDialog import ObjectDialog
from main import run_simulation_from_config
from modules.Manager import Manager
from modules.Messages import CPPDrawerObjectsMessage
from modules.constants import MessageType


class PolygonEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = Manager()
        self.scene_objects = {}  # {obj_id: MapObject}

        self.setWindowTitle("Редактор полигона")
        self.setGeometry(100, 100, 1600, 1000)

        # Иконки объектов
        self.icons = {
            ObjectType.AIR_PLANE: self.load_icon("images/aircraft_icon.png", "🛩️", 60),
            ObjectType.HELICOPTER: self.load_icon("images/helicopter.png", "🚁", 60),
            ObjectType.ANOTHER: self.load_icon("unknown.png", "❓", 60),
            ObjectType.MISSILE_LAUNCHER: self.load_icon("images/missile_launcher_icon.png", "🚀", 60),
            ObjectType.RADAR: self.load_icon("images/radar_icon.png", "📡", 60),
            ObjectType.MISSILE: self.load_icon("images/GM.png", "*", 30)
        }

        # Конфигурация по умолчанию
        self.default_config = {
            "simulation": {
                "time_step": 1,
                "duration": 60
            },
            "air_environment": {
                "id": 999,
                "position": [0.0, 0.0, 0.0],
                "targets": []
            },
            "combat_control_point": {
                "id": 0,
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

        # Настройка сцены с белым фоном
        self.scene.setSceneRect(-15000, -15000, 30000, 30000)
        self.scene.setBackgroundBrush(Qt.white)  # Белый фон


        # Рисуем сетку сразу при инициализации
        self.draw_grid()

        self.view = MapGraphicsView(self.scene, self)
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

            # Проверяем уникальность ID
            if not self.is_id_unique(obj_data["id"]):
                QMessageBox.warning(self, "Ошибка",
                                    f"Объект с ID {obj_data['id']} уже существует. Пожалуйста, выберите другой ID.")
                return  # Не добавляем объект

            # Увеличиваем счетчик только если ID уникален
            self.next_ids[self.current_object_type] = max(
                self.next_ids[self.current_object_type],
                int(obj_data["id"]) + 1)

            # Добавляем объект в конфиг
            if self.current_object_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER, ObjectType.ANOTHER]:
                self.config["air_environment"]["targets"].append(obj_data)
            elif self.current_object_type == ObjectType.MISSILE_LAUNCHER:
                self.config["missile_launchers"].append(obj_data)
                self.config["combat_control_point"]["missile_launcher_ids"].append(obj_data["id"])
                obj_data["missiles"] = [
                    {
                        "id": obj_data["id"]* 1000 + i,
                        "position": obj_data["position"],  # Позиция ракеты = позиции установки
                        "velocity": obj_data["missile_velocity"],
                        "explosion_radius": obj_data["missile_radius"],
                        "life_time": obj_data["missile_life_time"],
                    }
                    for i in range(1, obj_data.get("max_missiles", 1) + 1)
                ]
            elif self.current_object_type == ObjectType.RADAR:
                self.config["radars"].append(obj_data)
                self.config["combat_control_point"]["radar_ids"].append(obj_data["id"])

            self.update_scene()
            self.update_objects_list()

    def draw_grid(self):
        """Рисует яркую координатную сетку на сцене"""
        # Яркие оси координат
        axis_pen = QPen(QColor(180, 180, 180), 2, Qt.SolidLine)
        self.scene.addLine(-15000, 0, 15000, 0, axis_pen)  # Ось X
        self.scene.addLine(0, -15000, 0, 15000, axis_pen)  # Ось Y

        # Яркая основная сетка
        main_grid_pen = QPen(QColor(200, 200, 200), 1, Qt.SolidLine)

        # Вспомогательная сетка (более частая)
        secondary_grid_pen = QPen(QColor(230, 230, 230), 1, Qt.DotLine)

        # Основные линии (каждые 1000 единиц)
        for x in range(-15000, 15001, 1000):
            if x != 0:  # Не рисуем поверх осей
                self.scene.addLine(x, -15000, x, 15000, main_grid_pen)

        for y in range(-15000, 15001, 1000):
            if y != 0:  # Не рисуем поверх осей
                self.scene.addLine(-15000, y, 15000, y, main_grid_pen)

        # Вспомогательные линии (каждые 250 единиц)
        for x in range(-15000, 15001, 250):
            if x % 1000 != 0:  # Не рисуем поверх основных линий
                self.scene.addLine(x, -15000, x, 15000, secondary_grid_pen)

        for y in range(-15000, 15001, 250):
            if y % 1000 != 0:  # Не рисуем поверх основных линий
                self.scene.addLine(-15000, y, 15000, y, secondary_grid_pen)

        # Яркие подписи осей
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)

        # Подписи оси X
        for x in range(-14000, 15000, 2000):
            text = self.scene.addText(str(x // 1000), font)
            text.setPos(x - 20, 20)
            text.setDefaultTextColor(QColor(120, 120, 120))
            text.setZValue(-999)

        # Подписи оси Y
        for y in range(-14000, 15000, 2000):
            if y != 0:
                text = self.scene.addText(str(y // 1000), font)
                text.setPos(20, y - 10)
                text.setDefaultTextColor(QColor(120, 120, 120))
                text.setZValue(-999)

        # Центральный перекресток осей
        cross_pen = QPen(QColor(150, 150, 150), 3)
        self.scene.addLine(-50, 0, 50, 0, cross_pen)
        self.scene.addLine(0, -50, 0, 50, cross_pen)

    def update_scene(self):
        # Очищаем все объекты
        for obj_id, obj in list(self.scene_objects.items()):
            self.scene.removeItem(obj)
        self.scene_objects.clear()

        # Рисуем объекты заново
        for target in self.config["air_environment"]["targets"]:
            self.draw_map_object(target["position"], target["type"], target.get("id", ""))

        for launcher in self.config["missile_launchers"]:
            self.draw_map_object(launcher["position"], "MISSILE_LAUNCHER", launcher.get("id", ""))

            # Рисуем ракеты этой установки
            for missile in launcher.get("missiles", []):
                self.draw_map_object(launcher["position"], "MISSILE", missile["id"])

        for radar in self.config["radars"]:
            self.draw_map_object(radar["position"], "RADAR", radar.get("id", ""))

    def draw_map_object(self, position, obj_type, obj_id):
        enum_type = ObjectType[obj_type] if isinstance(obj_type, str) else obj_type
        icon = self.icons.get(enum_type, self.icons[ObjectType.ANOTHER])

        # Создаем или получаем объект
        if str(obj_id) in self.scene_objects:
            obj = self.scene_objects[str(obj_id)]
            obj.setPos(position[0] - icon.width() / 2, position[1] - icon.height() / 2)
        else:
            obj = MapObject(icon, enum_type, obj_id)
            obj.setPos(position[0] - icon.width() / 2, position[1] - icon.height() / 2)
            self.scene.addItem(obj)
            self.scene_objects[str(obj_id)] = obj
            obj.trajectory_points = []  # Инициализируем список точек траектории

        # Для движущихся объектов добавляем точку траектории
        if enum_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER, ObjectType.MISSILE]:
            # Добавляем новую точку
            point = self.scene.addEllipse(
                position[0] - 2, position[1] - 2, 4, 4,
                QPen(Qt.NoPen),
                QBrush(QColor(255, 165, 0, 200))  # Оранжевый цвет
            )
            point.setZValue(-1)
            obj.trajectory_points.append(point)

            # Ограничиваем количество точек (например, последние 50)
            if len(obj.trajectory_points) > 50:
                old_point = obj.trajectory_points.pop(0)
                self.scene.removeItem(old_point)

        # Для радара рисуем зону действия (как в предыдущей реализации)
        elif enum_type == ObjectType.RADAR and str(obj_id) not in self.scene_objects:
            radar_config = next((r for r in self.config["radars"] if str(r["id"]) == str(obj_id)), None)
            if radar_config:
                radius = radar_config.get("max_distance", 10000)
                radar_range = self.scene.addEllipse(
                    position[0] - radius,
                    position[1] - radius,
                    radius * 2,
                    radius * 2,
                    QPen(QColor(0, 200, 0, 80), 1, Qt.DashDotLine)
                )
                radar_range.setZValue(-2)
                radar_range.setParentItem(obj)
                obj.radar_range = radar_range


    def update_objects_list(self):
        self.objects_list.clear()

        for target in self.config["air_environment"]["targets"]:
            display_name = ObjectType.get_display_name(ObjectType[target["type"]])
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
            display_name = ObjectType.get_display_name(ObjectType[target["type"]])
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
        self.view.zoom(0.9)

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
                    "targets": [
                        {
                            "id": target["id"],
                            "type": target["type"],
                            "position": target["position"],
                            "velocity": target["velocity"]
                        }
                        for target in self.config["air_environment"]["targets"]
                    ]
                },
                "combat_control_point": {
                    "id": self.config["combat_control_point"]["id"],
                    "missile_launcher_ids": self.config["combat_control_point"]["missile_launcher_ids"],
                    "radar_ids": self.config["combat_control_point"]["radar_ids"]
                },
                "missile_launchers": [
                    {
                        "id": launcher["id"],
                        "position": launcher["position"],
                        "max_missiles": launcher["max_missiles"],
                        "missiles": launcher.get("missiles", [])
                    }
                    for launcher in self.config["missile_launchers"]
                ],
                "radars": [
                    {
                        "id": radar["id"],
                        "position": radar["position"],
                        "azimuth_start": radar["azimuth_start"],
                        "elevation_start": radar["elevation_start"],
                        "max_distance": radar["max_distance"],
                        "azimuth_range": radar["azimuth_range"],
                        "elevation_range": radar["elevation_range"],
                        "azimuth_speed": radar["azimuth_speed"],
                        "elevation_speed": radar["elevation_speed"],
                        "scan_mode": radar["scan_mode"]
                    }
                    for radar in self.config["radars"]
                ]
            }

            # Сохраняем в файл
            with open(self.default_config_path, 'w', encoding='utf-8') as file:
                yaml.dump(output_config, file, allow_unicode=True, sort_keys=False)

            QMessageBox.information(self, "Успех",
                                    f"Конфигурация сохранена в файл:\n{os.path.abspath(self.default_config_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить конфигурацию:\n{str(e)}")

    def run_simulation(self):
        # Сохраняем конфиг перед запуском
        self.save_config()

        # Запускаем моделирование
        self.manager = run_simulation_from_config('simulation_config.yaml')

        # Получаем все временные метки
        time_steps = sorted(self.manager.messages.keys())

        # Собираем все ID ракет из конфигурации
        missile_ids = set()
        for launcher in self.config["missile_launchers"]:
            for missile in launcher.get("missiles", []):
                missile_ids.add(str(missile["id"]))

        print(f"Known missile IDs: {missile_ids}")  # Отладочный вывод

        # Инициализация таймера
        self.simulation_timer = QTimer()
        self.current_step = 0
        self.max_step = len(time_steps)

        def update_simulation():
            if self.current_step >= self.max_step:
                self.simulation_timer.stop()
                QMessageBox.information(self, "Моделирование", "Моделирование завершено")
                return

            current_time = time_steps[self.current_step]
            messages = self.manager.give_messages_by_type(
                msg_type=MessageType.DRAW_OBJECTS,
                step_time=current_time
            )

            # Обрабатываем все сообщения для текущего времени
            for msg in messages:
                if not isinstance(msg, CPPDrawerObjectsMessage):
                    continue

                obj_id = str(msg.obj_id)
                x, y, _ = msg.coordinates

                # Если это ракета (по ID) и её нет на сцене - создаем
                if obj_id in missile_ids and obj_id not in self.scene_objects:
                    missile_type = ObjectType.MISSILE
                    icon = self.icons.get(missile_type)
                    if icon:
                        obj = MapObject(icon, missile_type, obj_id)
                        obj.setPos(x - icon.width() / 2, y - icon.height() / 2)
                        self.scene.addItem(obj)
                        self.scene_objects[obj_id] = obj
                        obj.trajectory_points = []
                        print(f"Created missile {obj_id} at ({x}, {y})")

                # Обновляем позицию для всех объектов (включая ракеты)
                if obj_id in self.scene_objects:
                    obj = self.scene_objects[obj_id]

                    # Обновляем позицию
                    current_pos = obj.pos()
                    new_x = x - obj.pixmap().width() / 2
                    new_y = y - obj.pixmap().height() / 2
                    obj.setPos(new_x, new_y)

                    print(f"Object {obj_id} visible: {obj.isVisible()} at ({new_x}, {new_y})")

                    # Для ВСЕХ движущихся объектов (включая ракеты) добавляем траекторию
                    if obj.obj_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER, ObjectType.MISSILE]:
                        # Создаем новую точку
                        point_size = 6
                        point = self.scene.addEllipse(
                            x - point_size / 2,
                            y - point_size / 2,
                            point_size,
                            point_size,
                            QPen(Qt.NoPen),
                            QBrush(QColor(255, 100, 0, 220))
                        )
                        point.setZValue(10)

                        # Инициализация структур данных для траектории
                        if not hasattr(obj, 'trajectory_points'):
                            obj.trajectory_points = []  # Будет хранить только точки
                            obj.trajectory_lines = []  # Будет хранить линии
                            obj.last_position = (x, y)  # Добавляем запись последней позиции

                        # Сохраняем текущую позицию
                        current_pos = (x, y)

                        # Если есть предыдущая точка - рисуем линию
                        if hasattr(obj, 'last_position'):
                            prev_x, prev_y = obj.last_position
                            line = self.scene.addLine(
                                prev_x, prev_y, x, y,
                                QPen(QColor(255, 150, 0, 180), 2))
                            line.setZValue(9)
                            obj.trajectory_lines.append(line)

                            # Добавляем точку и обновляем последнюю позицию
                            obj.trajectory_points.append(point)
                            obj.last_position = current_pos

                            # Ограничиваем количество элементов траектории
                            if len(obj.trajectory_points) > 100:
                                old_point = obj.trajectory_points.pop(0)
                            self.scene.removeItem(old_point)

                            if len(obj.trajectory_lines) > 0:
                                old_line = obj.trajectory_lines.pop(0)
                            self.scene.removeItem(old_line)

            self.status_bar.showMessage(
                f"Шаг: {self.current_step + 1}/{self.max_step} Время: {current_time}"
            )
            self.current_step += 1

        # Настраиваем таймер (обновление каждые 500 мс)
        self.simulation_timer.timeout.connect(update_simulation)
        self.simulation_timer.start(500)

        QMessageBox.information(self, "Моделирование", "Моделирование запущено")

    def initialize_scene_objects(self):
        """Инициализирует словарь scene_objects на основе текущей сцены"""
        self.scene_objects.clear()
        label_positions = {}

        for item in self.scene.items():
            if isinstance(item, QGraphicsTextItem):
                label_positions[(item.x(), item.y())] = item

        for item in self.scene.items():
            if isinstance(item, MapObject):
                obj_center_x = item.x() + item.pixmap().width() / 2
                expected_label_y = item.y() - 30
                expected_label_x = obj_center_x

                label = None
                for (x, y), lbl in label_positions.items():
                    if (abs(x - expected_label_x) < 50 and
                            abs(y - expected_label_y) < 50 and
                            str(item.obj_id) in lbl.toPlainText()):
                        label = lbl
                        break

                self.scene_objects[item.obj_id] = {
                    'object': item,
                    'label': label
                }

                if label is not None:
                    label.setParentItem(item)

    def is_id_unique(self, obj_id, obj_type=None):
        # Проверяем ID во всех типах объектов
        for target in self.config["air_environment"]["targets"]:
            if str(target.get("id", "")) == str(obj_id):
                return False

        for launcher in self.config["missile_launchers"]:
            if str(launcher.get("id", "")) == str(obj_id):
                return False

        for radar in self.config["radars"]:
            if str(radar.get("id", "")) == str(obj_id):
                return False

        return True