from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox)

from UI.Enums import ObjectType


class ObjectDialog(QDialog):
    def __init__(self, obj_type, position, default_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Добавить {ObjectType.get_display_name(obj_type)}")
        self.obj_type = obj_type
        self.position = position

        layout = QFormLayout(self)

        # Основные параметры
        self.id_edit = QLineEdit(str(default_id))
        self.x_edit = QLineEdit(str(round(position.x())))
        self.y_edit = QLineEdit(str(round(position.y())))
        self.z_edit = QLineEdit("0")

        layout.addRow("ID:", self.id_edit)
        layout.addRow("X координата:", self.x_edit)
        layout.addRow("Y координата:", self.y_edit)
        layout.addRow("Высота (Z):", self.z_edit)
        self.id_edit.setValidator(QIntValidator(1, 999999, self))

        # Параметры для разных типов объектов
        if obj_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER, ObjectType.ANOTHER]:
            default_vx = "100" if obj_type == ObjectType.AIR_PLANE else "50" if obj_type == ObjectType.HELICOPTER else "80"
            default_vy = "0" if obj_type == ObjectType.AIR_PLANE else "-20" if obj_type == ObjectType.HELICOPTER else "30"
            default_vz = "0" if obj_type != ObjectType.ANOTHER else "-10"

            self.velocity_x = QLineEdit(default_vx)
            self.velocity_y = QLineEdit(default_vy)
            self.velocity_z = QLineEdit(default_vz)
            layout.addRow("Скорость X:", self.velocity_x)
            layout.addRow("Скорость Y:", self.velocity_y)
            layout.addRow("Скорость Z:", self.velocity_z)
        elif obj_type == ObjectType.MISSILE_LAUNCHER:
            self.max_missiles = QLineEdit("5")
            self.missile_velocity = QLineEdit("1000")
            self.missile_life_time = QLineEdit("60")
            self.missile_radius = QLineEdit("50")

            layout.addRow("Макс. ракет:", self.max_missiles)
            layout.addRow("Скорость ракеты:", self.missile_velocity)
            layout.addRow("Время жизни ракеты:", self.missile_life_time)
            layout.addRow("Радиус поражения:", self.missile_radius)
        elif obj_type == ObjectType.RADAR:
            self.max_distance = QLineEdit("20000")
            self.azimuth_range = QLineEdit("360")
            self.elevation_range = QLineEdit("90")
            self.azimuth_speed = QLineEdit("10")
            self.elevation_speed = QLineEdit("5")
            self.scan_mode = QComboBox()
            self.scan_mode.addItems(["horizontal", "vertical"])

            layout.addRow("Дальность:", self.max_distance)
            layout.addRow("Азимут:", self.azimuth_range)
            layout.addRow("Угол места:", self.elevation_range)
            layout.addRow("Скорость азимута:", self.azimuth_speed)
            layout.addRow("Скорость угла места:", self.elevation_speed)
            layout.addRow("Режим сканирования:", self.scan_mode)

        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_object_data(self):
        try:
            obj_id = int(self.id_edit.text())
            if obj_id <= 0:
                raise ValueError("ID должен быть положительным числом")

            data = {
                "type": self.obj_type.value,
                "id": obj_id,
                "position": [
                    float(self.x_edit.text()),
                    float(self.y_edit.text()),
                    float(self.z_edit.text())
                ]
            }

            if self.obj_type in [ObjectType.AIR_PLANE, ObjectType.HELICOPTER, ObjectType.ANOTHER]:
                data["velocity"] = [
                    float(self.velocity_x.text()),
                    float(self.velocity_y.text()),
                    float(self.velocity_z.text())
                ]
            elif self.obj_type == ObjectType.MISSILE_LAUNCHER:
                data["max_missiles"] = int(self.max_missiles.text())
                data["missile_velocity"] = int(self.missile_velocity.text())
                data["missile_radius"] = int(self.missile_radius.text())
                data["missile_life_time"] = int(self.missile_life_time.text())

            elif self.obj_type == ObjectType.RADAR:
                data.update({
                    "azimuth_start": 0.0,
                    "elevation_start": 0.0,
                    "max_distance": float(self.max_distance.text()),
                    "azimuth_range": 360, #float(self.azimuth_range.text()), - Хардкод Богдана
                    "elevation_range": 180,#float(self.elevation_range.text()), - Хардкод Богдана
                    "azimuth_speed": 0,#float(self.azimuth_speed.text()),
                    "elevation_speed": 0,#float(self.elevation_speed.text()),
                    "scan_mode": self.scan_mode.currentText()
                })

            return data

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректный ID: {str(e)}")
            return None

