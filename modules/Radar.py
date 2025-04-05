import numpy as np
from typing import List, Tuple

class SectorRadar:
    def __init__(
        self,
        position: np.ndarray,
        id: int,
        azimuth_start: float,
        elevation_start: float,
        max_distance: float,
        azimuth_range: float,
        elevation_range: float,
        azimuth_speed: float,
        elevation_speed: float,
        scan_mode: str = "horizontal"
    ):
        """
        Класс радара с секторным обзором.

        :param position: Позиция радара в глобальной системе координат (x, y, z).
        :param azimuth_start: Начальный угол азимута (в градусах).
        :param elevation_start: Начальный угол наклона (в градусах).
        :param max_distance: Максимальная дальность обнаружения.
        :param azimuth_range: Угол раскрыва сектора по азимуту (в градусах).
        :param elevation_range: Угол раскрыва сектора по углу наклона (в градусах).
        :param azimuth_speed: Скорость сканирования по азимуту (градусов в секунду).
        :param elevation_speed: Скорость сканирования по углу наклона (градусов в секунду).
        :param scan_mode: Режим сканирования ("horizontal" или "vertical").
        """
        self.position = position
        self.id = id
        self.azimuth_start = azimuth_start
        self.elevation_start = elevation_start
        self.max_distance = max_distance
        self.azimuth_range = azimuth_range
        self.elevation_range = elevation_range
        self.azimuth_speed = azimuth_speed
        self.elevation_speed = elevation_speed
        self.scan_mode = scan_mode

        # Текущие углы сканирования
        self.current_azimuth = azimuth_start
        self.current_elevation = elevation_start

    def find_visible_objects(self, objects: List[np.ndarray]) -> List[Tuple[np.ndarray, float]]:
        """
        Поиск объектов, видимых радаром в текущем секторе.

        :param objects: Список объектов, каждый из которых представлен координатами (x, y, z).
        :return: Список видимых объектов и их расстояний до радара.
        """
        visible_objects = []

        for obj in objects:
            # Вычисляем расстояние до объекта
            distance = np.linalg.norm(obj - self.position)
            if distance > self.max_distance:
                continue

            # Вычисляем углы азимута и наклона до объекта
            delta = obj - self.position
            azimuth = np.degrees(np.arctan2(delta[1], delta[0])) % 360
            elevation = np.degrees(np.arcsin(delta[2] / distance)) % 180

            # Проверяем, попадает ли объект в текущий сектор
            if (
                self.current_azimuth <= azimuth <= self.current_azimuth + self.azimuth_range
                and self.current_elevation <= elevation <= self.current_elevation + self.elevation_range
            ):
                visible_objects.append((obj, distance))

        return visible_objects

    def move_to_next_sector(self):
        """
        Переход к следующему сектору сканирования.
        """
        if self.scan_mode == "horizontal":
            # Горизонтальное сканирование: сначала по азимуту, затем по углу наклона
            self.current_azimuth += self.azimuth_speed
            if self.current_azimuth >= self.azimuth_start + self.azimuth_range:
                self.current_azimuth = self.azimuth_start
                self.current_elevation += self.elevation_speed
                if self.current_elevation >= self.elevation_start + self.elevation_range:
                    self.current_elevation = self.elevation_start
        elif self.scan_mode == "vertical":
            # Вертикальное сканирование: сначала по углу наклона, затем по азимуту
            self.current_elevation += self.elevation_speed
            if self.current_elevation >= self.elevation_start + self.elevation_range:
                self.current_elevation = self.elevation_start
                self.current_azimuth += self.azimuth_speed
                if self.current_azimuth >= self.azimuth_start + self.azimuth_range:
                    self.current_azimuth = self.azimuth_start

    def move_to_next_sector_circular(self):
        """
        Переход к следующему сектору сканирования с круговым обзором.
        """
        if self.scan_mode == "horizontal":
            # Горизонтальное сканирование: круговой обзор по азимуту
            self.current_azimuth = (self.current_azimuth + self.azimuth_speed) % 360
            # Если азимут завершил полный круг, увеличиваем угол наклона
            if self.current_azimuth < self.azimuth_speed:
                self.current_elevation = (self.current_elevation + self.elevation_speed) % 180
        elif self.scan_mode == "vertical":
            # Вертикальное сканирование: круговой обзор по углу наклона
            self.current_elevation = (self.current_elevation + self.elevation_speed) % 180
            # Если угол наклона завершил полный круг, увеличиваем азимут
            if self.current_elevation < self.elevation_speed:
                self.current_azimuth = (self.current_azimuth + self.azimuth_speed) % 360

    def update_scan_parameters(
        self,
        new_azimuth_range: float = None,
        new_elevation_range: float = None,
        new_azimuth_speed: float = None,
        new_elevation_speed: float = None
    ):
        """
        Обновление параметров сканирования.

        :param new_azimuth_range: Новый угол раскрыва по азимуту.
        :param new_elevation_range: Новый угол раскрыва по углу наклона.
        :param new_azimuth_speed: Новая скорость сканирования по азимуту.
        :param new_elevation_speed: Новая скорость сканирования по углу наклона.
        """
        if new_azimuth_range is not None:
            self.azimuth_range = new_azimuth_range
        if new_elevation_range is not None:
            self.elevation_range = new_elevation_range
        if new_azimuth_speed is not None:
            self.azimuth_speed = new_azimuth_speed
        if new_elevation_speed is not None:
            self.elevation_speed = new_elevation_speed

    def start(self, objects):
        # Симуляция работы радара
        num_steps = int(self.azimuth_range / self.azimuth_speed * self.elevation_range / self.elevation_speed)
        for step in range(num_steps):
            print(f"Шаг {step + 1}:")
            ### tbd ! ПОЛУЧЕНИЕ ИНФОРМАЦИИ ОБ ОБЪЕКТАХ !
            visible_objects = radar.find_visible_objects(objects)
            print(f"Видимые объекты: {visible_objects}")
            ### tbd ! ПЕРЕДАЧА ИНФОРМАЦИИ О НАЙДЕННЫХ ОБЪЕКТАХ !
            radar.move_to_next_sector()


# ### Пример использования

# # Создаем радар с горизонтальным сканированием
# radar = SectorRadar(
#     position=np.array([0, 0, 0]),
#     id = 0,
#     azimuth_start=0,
#     elevation_start=0,
#     max_distance=1000,
#     azimuth_range=90,
#     elevation_range=45,
#     azimuth_speed=10,
#     elevation_speed=5,
#     scan_mode="horizontal"
# )

# # Список объектов в пространстве
# objects = [
#     np.array([100, 200, 50]),
#     np.array([300, 400, 100]),
#     np.array([500, 600, 150])
# ]

# radar.start(objects)
