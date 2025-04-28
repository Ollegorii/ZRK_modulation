import numpy as np
from .utils import Target
from .Manager import Manager
from .constants import *
from .BaseModel import BaseModel
from .Messages import * 
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class SectorRadar(BaseModel):
    def __init__(
        self,
        manager: Manager,
        id: int,
        pos: np.ndarray,
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
        """
        super().__init__(manager, id, pos)
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

    def find_visible_objects(self, objects: List[AirObject]) -> List[AirObject]:
        """
        Поиск объектов, видимых радаром в текущем секторе.
        """
        visible_objects = []

        for obj in objects:
            # Вычисляем расстояние до объекта
            coords = obj.pos
            distance = np.linalg.norm(coords - self.pos)
            if distance > self.max_distance:
                continue

            # Вычисляем углы азимута и наклона до объекта
            delta = coords - self.pos
            azimuth = np.degrees(np.arctan2(delta[1], delta[0])) % 360
            elevation = np.degrees(np.arcsin(delta[2] / distance)) % 180

            # Проверяем, попадает ли объект в текущий сектор
            if (
                self.current_azimuth <= azimuth <= self.current_azimuth + self.azimuth_range
                and self.current_elevation <= elevation <= self.current_elevation + self.elevation_range
            ):
                visible_objects.append(obj)

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
        """
        if new_azimuth_range is not None:
            self.azimuth_range = new_azimuth_range
        if new_elevation_range is not None:
            self.elevation_range = new_elevation_range
        if new_azimuth_speed is not None:
            self.azimuth_speed = new_azimuth_speed
        if new_elevation_speed is not None:
            self.elevation_speed = new_elevation_speed

    def step(self):
        """
        Выполнение одного шага симуляции для МФР
        """
        current_time = self._manager.time.get_time()
        dt = self._manager.time.get_dt()

        objects = self._manager.give_messages_by_type(MessageType.ACTIVE_OBJECTS)[0].active_objects
        if len(objects) == 0:
            raise "ОШИБКА РАДАРА: ВО отправило пустое сообщение"
        visible_objects = self.find_visible_objects(objects)
        logger.info(f"Видимые объекты:")
        for obj in visible_objects:
            logger.info(obj)
        visible_objects_msg = FoundObjectsMessage(
            time=current_time, 
            sender_id=self.id, 
            receiver_id=CCP_ID, 
            visible_objects=visible_objects
        )
        self._manager.add_message(visible_objects_msg)

        # ПРИЕМ ТАРГЕТОВ, КОТОРЫЕ НУЖНО ОБНОВИТЬ, ОТ ПБУ
        messages_to_missile = self._manager.give_messages_by_type(MessageType.UPDATE_TARGET, step_time=current_time-dt)
        # ОТПРАВКА СООБЩЕНИЙ РАКЕТАМ
        for message in messages_to_missile:
            id_missile = message.missile_id
            target = message.target
            upd_msg = UpdateTargetPosition(
                time=current_time, 
                sender_id=self.id, 
                receiver_id=id_missile, 
                upd_object=target
            )
            self._manager.add_message(upd_msg)

        # ПРОВЕРКА СООБЩЕНИЯ ОБ УНИЧТОЖЕНИИ РАКЕТЫ 
        destroy_missile_id_msg = self._manager.give_messages_by_type(MessageType.MISSILE_DETONATE, step_time=current_time-dt)
        # ОТПРАВКА УНИЧТНОЖЕННОЙ РАКЕТЫ НА ПБУ
        for destroy_missile_id in destroy_missile_id_msg:
            destroy_msg = DestroyedMissileId(
                time=current_time, 
                sender_id=self.id, 
                receiver_id=CCP_ID, 
                missile_id=destroy_missile_id.missile_id,
                self_detonation=destroy_missile_id.self_detonation
            )
            self._manager.add_message(destroy_msg)   
                 
        self.move_to_next_sector()

    def start(self, objects):
        """
        Симуляция работы радара для тестирования
        """
        num_steps = int(self.azimuth_range / self.azimuth_speed * self.elevation_range / self.elevation_speed)
        for step in range(num_steps):
            logger.info(f"Шаг {step + 1}:")
            ### tbd ! ПОЛУЧЕНИЕ ИНФОРМАЦИИ ОБ ОБЪЕКТАХ !
            visible_objects = self.find_visible_objects(objects)
            logger.info(f"Видимые объекты: {visible_objects}")
            ### tbd ! ПЕРЕДАЧА ИНФОРМАЦИИ О НАЙДЕННЫХ ОБЪЕКТАХ !
            self.move_to_next_sector()
