import os
import numpy as np
import yaml
from PyQt5.QtCore import Qt, QSize, QTimer, QPointF
from PyQt5.QtGui import QColor, QPen, QPainter, QPixmap, QIcon, QBrush
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QPushButton, QListWidget, QComboBox,
                             QDialog, QGraphicsScene, QGraphicsTextItem,
                             QMessageBox, QSlider, QStatusBar, QGraphicsEllipseItem, QFileDialog, QGroupBox,
                             QFormLayout, QSpinBox)

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

        self.y_inverted = True
        self.y_coeff = -1 if self.y_inverted else 1

        self.setWindowTitle("Редактор полигона")
        self.setGeometry(100, 100, 1600, 1800)


        self.scene_size = 3_000_000  # Размер сцены в метрах (радиус от центра)
        self.grid_step = 2000

        # Иконки объектов
        self.icons = {
            ObjectType.AIR_PLANE: self.load_icon("UI/images/aircraft_icon.png", "🛩️", 300),
            ObjectType.HELICOPTER: self.load_icon("UI/images/helicopter.png", "🚁", 300),
            ObjectType.MISSILE_LAUNCHER: self.load_icon("UI/images/missile_launcher_icon.png", "🚀", 300),
            ObjectType.MISSILE: self.load_icon("UI/images/GM.png", "*", 200),
            ObjectType.RADAR: self.load_icon("UI/images/radar_icon.png", "📡", 300),
            ObjectType.AIR_PLANE_RED: self.load_icon("UI/images/aircraft_icon_red.png", "*", 300),
            ObjectType.HELICOPTER_RED: self.load_icon("UI/images/helicopter_red.png", "*", 300),
        }

            # Конфигурация по умолчанию
        self.default_config = {
            "simulation": {
                "time_step": 200,
                "duration": 40000
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
            # ObjectType.ANOTHER: 1,
            ObjectType.MISSILE_LAUNCHER: 3,
            ObjectType.RADAR: 5
        }
        self.default_config_path = "simulation_config.yaml"
        self.init_ui()

    def convert_coordinates(self, x, y):
        """Преобразует координаты с учетом инверсии Y"""
        return x, self.y_coeff * y

    def load_icon(self, filename, fallback, size, color=None):
        if os.path.exists(filename):
            pixmap = QPixmap(filename)
            if color:
                # Применяем цветовой фильтр, если указан цвет
                painter = QPainter(pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), color)
                painter.end()
            return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setFont(self.font())
            if color:
                painter.setPen(color)
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
        left_panel.setMaximumWidth(400)  # Увеличим ширину панели
        left_layout = QVBoxLayout(left_panel)

        # Добавляем настройки симуляции в начало
        left_layout.addWidget(self.init_simulation_settings_ui())

        # Выбор типа объекта
        self.object_type_combo = QComboBox()
        self.object_type_combo.setIconSize(QSize(48, 48))
        for obj_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER,
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

        # Кнопки управления - теперь в два ряда
        btn_layout1 = QHBoxLayout()
        btn_layout2 = QHBoxLayout()

        # Первый ряд кнопок
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_btn.clicked.connect(self.delete_object)
        self.delete_btn.setMinimumWidth(120)  # Фиксированная ширина

        # Добавляем кнопку загрузки конфига
        self.load_btn = QPushButton("Загрузить конфиг")
        self.load_btn.setIcon(QIcon.fromTheme("document-open"))
        self.load_btn.clicked.connect(self.load_config)


        btn_layout1.addWidget(self.delete_btn)
        btn_layout1.addWidget(self.load_btn)


        # Второй ряд кнопок
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setIcon(QIcon.fromTheme("document-save"))
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setMinimumWidth(120)

        self.run_btn = QPushButton("Запуск")
        self.run_btn.setIcon(QIcon.fromTheme("media-playback-start"))
        self.run_btn.clicked.connect(self.run_simulation)
        self.run_btn.setMinimumWidth(120)

        self.reset_btn = QPushButton("Сбросить")
        self.reset_btn.setIcon(QIcon.fromTheme("edit-clear"))
        self.reset_btn.clicked.connect(self.reset_experiment)
        self.reset_btn.setMinimumWidth(120)



        btn_layout2.addWidget(self.save_btn)
        btn_layout2.addWidget(self.run_btn)
        btn_layout2.addWidget(self.reset_btn)


        left_layout.addLayout(btn_layout1)
        left_layout.addLayout(btn_layout2)

        # Масштабирование
        zoom_layout = QHBoxLayout()
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.setFixedWidth(30)  # Фиксированный размер кнопок +/-

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(1, 1000)
        self.zoom_slider.setValue(50)
        self.zoom_slider.valueChanged.connect(self.zoom_slider_changed)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.setFixedWidth(30)

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
        scene_rect = -self.scene_size, -self.scene_size, 2 * self.scene_size, 2 * self.scene_size
        self.scene.setSceneRect(*scene_rect)

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
        x, y = self.convert_coordinates(position.x(), position.y())
        adjusted_position = QPointF(x, y)  # Z-координата остается 0

        default_id = self.next_ids[self.current_object_type]
        dialog = ObjectDialog(self.current_object_type, adjusted_position, default_id, self)

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
            if self.current_object_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER]:
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
        """Рисует сетку с увеличенными размерами"""
        # Оси координат
        pen = QPen(QColor(100, 100, 255, 150), 2)
        self.scene.addLine(-self.scene_size, 0, self.scene_size, 0, pen)  # Ось X
        self.scene.addLine(0, self.scene_size, 0, -self.scene_size, pen)  # Ось Y

        # Подписи осей
        font = self.font()
        font.setPointSize(200)

        # Подпись оси X
        x_label = self.scene.addText("X")
        x_label.setFont(font)
        x_label.setPos(self.scene_size - 2000, 50)

        # Подпись оси Y
        y_label = self.scene.addText("Y")
        y_label.setFont(font)
        y_label.setPos(-300, -self.scene_size + 2000)

        # Сетка с увеличенным шагом
        pen = QPen(QColor(200, 200, 200, 100), 1)
        for i in range(-self.scene_size, self.scene_size + 1, self.grid_step):
            if i != 0:
                # Вертикальные линии
                self.scene.addLine(i, -self.scene_size, i, self.scene_size, pen)
                # Горизонтальные линии
                self.scene.addLine(-self.scene_size, i, self.scene_size, i, pen)

        # Подписи координат
        font.setPointSize(100)
        for i in range(-self.scene_size, self.scene_size + 1, self.grid_step):
            if i != 0:
                # Подписи по оси X
                x_text = self.scene.addText(f"{i / 1000:.0f}км")
                x_text.setFont(font)
                x_text.setPos(i - 50, 50)

                # Подписи по оси Y
                y_text = self.scene.addText(f"{-i / 1000:.0f}км" if self.y_inverted else f"{i / 1000:.0f}км")
                y_text.setFont(font)
                y_text.setPos(-50, i - 100)

    def update_scene(self):
        """Обновляет сцену на основе текущей конфигурации"""
        # Полностью очищаем сцену перед обновлением
        self.clear_scene_completely()
        self.draw_grid()

        # Рисуем объекты заново
        for target in self.config["air_environment"]["targets"]:
            self.draw_map_object(target["position"], target["type"], target.get("id", ""))

        for launcher in self.config["missile_launchers"]:
            self.draw_map_object(launcher["position"], "MISSILE_LAUNCHER", launcher.get("id", ""))
            for missile in launcher.get("missiles", []):
                self.draw_map_object(launcher["position"], "MISSILE", missile["id"])

        for radar in self.config["radars"]:
            self.draw_map_object(radar["position"], "RADAR", radar.get("id", ""))

    def draw_map_object(self, position, obj_type, obj_id):
        enum_type = ObjectType[obj_type] if isinstance(obj_type, str) else obj_type
        icon = self.icons.get(enum_type, self.icons[ObjectType.AIR_PLANE])

        # Преобразуем координаты для отображения
        x, y = self.convert_coordinates(position[0], position[1])

        # Создаем или получаем объект
        if str(obj_id) in self.scene_objects:
            obj = self.scene_objects[str(obj_id)]
            obj.setPos(x - icon.width()/2, y - icon.height()/2)
        else:
            obj = MapObject(icon, enum_type, obj_id)
            obj.setPos(x - icon.width()/2, y - icon.height()/2)
            self.scene.addItem(obj)
            self.scene_objects[str(obj_id)] = obj
            obj.trajectory_points = []

        # Для движущихся объектов добавляем точку траектории
        if enum_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER, ObjectType.MISSILE]:
            point = self.scene.addEllipse(
                x - 2, y - 2, 4, 4,
                QPen(Qt.NoPen),
                QBrush(QColor(255, 165, 0, 200))
            )
            point.setZValue(-1)
            obj.trajectory_points.append(point)

            if len(obj.trajectory_points) > 50:
                old_point = obj.trajectory_points.pop(0)
                self.scene.removeItem(old_point)

        # Для радара рисуем зону действия
        elif enum_type == ObjectType.RADAR:
            radar_config = None
            for radar in self.config["radars"]:
                if str(radar["id"]) == str(obj_id):
                    radar_config = radar
                    break

            if radar_config:
                radius = radar_config.get("max_distance", 10000)
                if hasattr(obj, 'radar_range'):
                    self.scene.removeItem(obj.radar_range)

                radar_range = self.scene.addEllipse(
                    x - radius,
                    y - radius,
                    radius * 2,
                    radius * 2,
                    QPen(QColor(0, 200, 0, 80)),
                    QBrush(QColor(0, 200, 0, 30))
                )
                radar_range.setZValue(-2)
                obj.radar_range = radar_range

        self.scene_objects[str(obj_id)] = obj

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
        current_scale = self.view.scale_factor
        new_scale = current_scale * 1.1
        if new_scale <= self.view.max_scale:
            self.view.scale(1.1, 1.1)
            self.view.scale_factor = new_scale
            self.update_zoom_slider(new_scale)

    def zoom_out(self):
        current_scale = self.view.scale_factor
        new_scale = current_scale * 0.9
        if new_scale >= self.view.min_scale:
            self.view.scale(0.9, 0.9)
            self.view.scale_factor = new_scale
            self.update_zoom_slider(new_scale)

    def zoom_out(self):
        current_scale = self.view.scale_factor
        new_scale = current_scale * 0.9
        min_scale = 0.001  # Минимальный масштаб уменьшения

        # Рассчитываем минимальный допустимый масштаб на основе размера сцены
        view_size = min(self.view.width(), self.view.height())
        scene_size = 2 * self.scene_size
        absolute_min_scale = view_size / scene_size * 0.9

        if new_scale >= max(min_scale, absolute_min_scale):
            self.view.scale(0.9, 0.9)
            self.view.scale_factor = new_scale
            self.update_zoom_slider(new_scale)

    def zoom_slider_changed(self, value):
        # Преобразуем значение слайдера (1-1000) в масштаб (0.001-10)
        min_scale = 0.001
        max_scale = 1.0
        scale = min_scale + (max_scale - min_scale) * (value / 1000.0)

        self.view.resetTransform()
        self.view.scale(scale, scale)
        self.view.scale_factor = scale

    def update_zoom_slider(self, scale):
        # Преобразуем масштаб (0.001-10) в значение слайдера (1-1000)
        min_scale = 0.001
        max_scale = 1.0
        value = int(((scale - min_scale) / (max_scale - min_scale)) * 1000)
        self.zoom_slider.setValue(value)

    def update_status(self):
        count = (len(self.config["air_environment"]["targets"]) +
                 len(self.config["missile_launchers"]) +
                 len(self.config["radars"]))
        self.status_bar.showMessage(f"Объектов: {count} | Масштаб: {int(self.view.scale_factor * 100)}%")

    def save_config(self, source = False):
        try:
            self.update_simulation_settings()

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

            if source == False:
                # Открываем диалог выбора файла для сохранения
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Сохранить конфигурацию",
                    self.default_config_path,  # Начальный путь
                    "YAML Files (*.yaml *.yml);;All Files (*)"
                )
            else:
                file_path = self.default_config_path

            # Если пользователь отменил выбор
            if not file_path:
                return

            # Сохраняем в выбранный файл
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(output_config, file, allow_unicode=True, sort_keys=False)


            QMessageBox.information(self, "Успех",
                                    f"Конфигурация сохранена в файл:\n{os.path.abspath(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить конфигурацию:\n{str(e)}")

    def run_simulation(self):
        # Перед запуском симуляции полностью очищаем сцену
        # self.clear_scene_completely()
        # self.draw_grid()  # Восстанавливаем сетку

        # Сохраняем конфиг перед запуском
        self.save_config(source = True)

        # Запускаем моделирование
        self.manager = run_simulation_from_config('simulation_config.yaml')

        time_steps = sorted(self.manager.messages.keys())

        # Собираем все ID ракет из конфигурации
        missile_ids = set()
        for launcher in self.config["missile_launchers"]:
            for missile in launcher.get("missiles", []):
                missile_ids.add(str(missile["id"]))

        #print(f"Known missile IDs: {missile_ids}")  # Отладочный вывод

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
                x, y = self.convert_coordinates(x, y)

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
                        #print(f"Created missile {obj_id} at ({x}, {y})")

                obj_type = None

                # Обновляем позицию для всех объектов (включая ракеты)
                if obj_id in self.scene_objects:
                    obj = self.scene_objects[obj_id]
                    obj_type = self.scene_objects[obj_id].obj_type

                    # Для самолетов и вертолетов меняем иконку в зависимости от видимости
                    if obj_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER]:
                        if msg.is_visible_by_radar:
                            # Используем красную иконку
                            if obj_type == ObjectType.AIR_PLANE:
                                new_icon = self.icons[ObjectType.AIR_PLANE_RED]
                            else:
                                new_icon = self.icons[ObjectType.HELICOPTER_RED]
                        else:
                            # Используем обычную иконку
                            new_icon = self.icons[obj_type]

                        obj.setPixmap(new_icon)

                    new_x = x - obj.pixmap().width() / 2
                    new_y = y - obj.pixmap().height() / 2
                    obj.setPos(new_x, new_y)

                    #print(f"Object {obj_id} visible: {obj.isVisible()} at ({new_x}, {new_y})")

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
                            if obj.obj_type == ObjectType.MISSILE:
                                color = QPen(QColor(0, 0, 255, 180), 10)
                            else:
                                color = QPen(QColor(255, 150, 0, 180), 10)

                            if obj.last_position != None:
                                prev_x, prev_y = obj.last_position
                                line = self.scene.addLine(
                                    prev_x, prev_y, x, y,
                                    color)
                                line.setZValue(9)

                            # Добавляем точку и обновляем последнюю позицию
                            obj.last_position = current_pos

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


    def clear_scene_completely(self):
        """Полностью очищает сцену, включая все графические элементы"""
        # Удаляем все элементы со сцены
        self.scene.clear()

        # Очищаем словарь объектов
        self.scene_objects.clear()

        # Восстанавливаем стандартные настройки сцены
        self.scene.setSceneRect(-15000, -15000, 30000, 30000)

    def reset_experiment(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Сброс эксперимента")
        msg_box.setText("Вы уверены, что хотите сбросить эксперимент? Все объекты и траектории будут удалены.")

        # Создаем кнопки с русским текстом
        button_yes = msg_box.addButton("Да", QMessageBox.YesRole)
        button_no = msg_box.addButton("Нет", QMessageBox.NoRole)

        # Показываем диалог и ждем ответа
        msg_box.exec()

        if msg_box.clickedButton() == button_yes:
            # Останавливаем таймер симуляции, если он активен
            if hasattr(self, 'simulation_timer') and self.simulation_timer.isActive():
                self.simulation_timer.stop()

            # Полностью очищаем сцену
            self.clear_scene_completely()

            # Сбрасываем конфигурацию
            self.config = {
                "simulation": {
                    "time_step": 200,
                    "duration": 40000
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
            self.save_config(source=True)

            # Сбрасываем счетчики ID
            self.next_ids = {
                ObjectType.AIR_PLANE: 1,
                ObjectType.HELICOPTER: 1,
                ObjectType.MISSILE_LAUNCHER: 3,
                ObjectType.RADAR: 5
            }

            # Очищаем список объектов
            self.objects_list.clear()

            # Восстанавливаем сетку
            self.draw_grid()

            # Обновляем статус
            self.update_status()

            QMessageBox.information(self, "Сброс", "Эксперимент полностью сброшен, все объекты и траектории удалены.")

    def load_config(self):
        # Открываем диалог выбора файла
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл конфигурации",
            "",
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )

        if not file_path:
            return  # Пользователь отменил выбор

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                loaded_config = yaml.safe_load(file)

            # Валидация загруженного конфига
            if not self.validate_config(loaded_config):
                QMessageBox.warning(self, "Ошибка", "Некорректный формат конфигурационного файла")
                return

            # Обновляем текущую конфигурацию
            self.config = loaded_config

            # Обновляем UI настроек симуляции
            self.time_step_edit.setValue(self.config["simulation"]["time_step"])
            self.duration_edit.setValue(self.config["simulation"]["duration"])

            # Обновляем счетчики ID
            self.update_id_counters()

            # Обновляем сцену
            self.update_scene()
            self.update_objects_list()

            QMessageBox.information(self, "Успех", "Конфигурация успешно загружена")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить конфигурацию:\n{str(e)}")

    def validate_config(self, config):
        """Проверяет основные поля конфигурации"""
        required_sections = [
            'simulation',
            'air_environment',
            'combat_control_point',
            'missile_launchers',
            'radars'
        ]

        for section in required_sections:
            if section not in config:
                return False

        return True

    def update_id_counters(self):
        """Обновляет счетчики ID на основе загруженной конфигурации"""
        # Для воздушных целей
        if self.config["air_environment"]["targets"]:
            max_id = max(t["id"] for t in self.config["air_environment"]["targets"])
            self.next_ids[ObjectType.AIR_PLANE] = max_id + 1
            self.next_ids[ObjectType.HELICOPTER] = max_id + 1

        # Для пусковых установок
        if self.config["missile_launchers"]:
            max_id = max(m["id"] for m in self.config["missile_launchers"])
            self.next_ids[ObjectType.MISSILE_LAUNCHER] = max_id + 1

        # Для радаров
        if self.config["radars"]:
            max_id = max(r["id"] for r in self.config["radars"])
            self.next_ids[ObjectType.RADAR] = max_id + 1

    def init_simulation_settings_ui(self):
        """Инициализирует UI для настроек симуляции"""
        self.simulation_settings_group = QGroupBox("Настройки симуляции")
        layout = QFormLayout()

        # Поле для time_step
        self.time_step_edit = QSpinBox()
        self.time_step_edit.setRange(0, 1000)  # Минимальный и максимальный шаг (мс)
        self.time_step_edit.setValue(self.config["simulation"]["time_step"])
        self.time_step_edit.setSuffix(" мс")
        self.time_step_edit.valueChanged.connect(self.update_simulation_settings)

        # Поле для duration
        self.duration_edit = QSpinBox()
        self.duration_edit.setRange(0, 100000)  # Минимальная и максимальная длительность (мс)
        self.duration_edit.setValue(self.config["simulation"]["duration"])
        self.duration_edit.setSuffix(" мс")
        self.duration_edit.valueChanged.connect(self.update_simulation_settings)

        layout.addRow("Шаг симуляции:", self.time_step_edit)
        layout.addRow("Длительность:", self.duration_edit)

        self.simulation_settings_group.setLayout(layout)
        return self.simulation_settings_group

    def update_simulation_settings(self):
        """Обновляет параметры симуляции при изменении значений"""
        self.config["simulation"]["time_step"] = self.time_step_edit.value()
        self.config["simulation"]["duration"] = self.duration_edit.value()