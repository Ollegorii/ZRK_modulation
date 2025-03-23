import typing
import numpy as np
from enum import Enum
from simulation.BaseModel import BaseModel
from simulation.Manager import Manager


class TargetTypeCCP(Enum):
    AIR_PLANE = "самолет"
    HELICOPTER = "вертолет"
    ANOTHER = "другое"


# Возможно наследование от какого-то базового класса типа BaseUnit/Unit/Movable
class TargetCCP:
    def __init__(self, type: TargetTypeCCP, coord: np.array, speed: np.array, upd_time: float) -> None:
        """
        :param type: тип цели
        :param coord: координаты цели
        :param speed: скорость цели
        :param upd_time: время, в которое произошло посл изменение класса
        """
        self.type = type
        self.coord = coord
        self.speed = speed
        self.upd_time = upd_time
        self.seen_time = -1

    def upd_сoord(self, new_coord: float, time: float) -> None:
        """
        Функция для обновления координаты цели
        :param new_coord: новая координата цели
        :param time: время, когда вызвали функцию
        """
        self.coord = new_coord
        self.upd_time = time


# Возможно наследование от какого-то базового класса типа BaseUnit/Unit/Movable
class RocketCCP:
    def __init__(self, coord: np.array, speed:np.array, id: int, target: TargetCCP, time):
        """
        :param coord: текущие координаты ЗУР
        :param id: id ЗУР
        :param target: цель
        :param time: время, в которое произошло посл изменение класса
        """
        self.coord = coord
        self.speed = speed
        self.target = target
        self.id = id
        self.upd_time = time
        self.seen_time = -1



    def upd_сoord(self, new_coord: float, time: float) -> None:
        """
        Функция для обновления координаты ЗУР
        :param new_coord: новая координата ЗУР
        :param time: время, когда вызвали функцию
        """
        self.coord = new_coord
        self.upd_time = time


# Возможно наследование от какого-то класса базовых модулей
class CombatControlPoint(BaseModel):
    def __init__(self, manager: Manager, ID: int, missile_launcher_coords: dict, radars_coords: dict):
        """
        :param dispatcher: диспетчер моделей
        :param ID: ID объекта моделирования
        :param radars_coords: словарь с координатами всех МФР
        """
        super().__init__(manager, ID, None)
        self._target_dict = {}  # Отслеживаемые цели
        self._next_target_id = 0
        self._rocket_dict = {}  # Отслеживаемые ЗУР
        self._next_rocket_id = 0
        self.radars_coords = radars_coords  # координаты МФР
        self.missile_launcher_coords = missile_launcher_coords  # координаты ПУ

    def get_Radar_info(self, visible_object: list, cur_time: float):
        """
        Получение сообщения об обнаружении цели от Radar и последующее её сопровождение
        """
        pass

    def add_target(self, target: TargetCCP):
        """
        Добавление новой цели в список целей ПБУ
        """
        self._target_dict[self._next_target_id] = target
        print(f"В ПБУ добавлена цель с id: {self._next_target_id}")
        self._next_target_id += 1

    def delete_target(self, target_id):
        """
        :param target_id: id цели
        """
        self._target_dict.pop(target_id, None)
        print(f"В ПБУ удалена цель с id: {target_id}")

    def get_PU_info(self):
        """
        Получение сообщений от ПУ и соотв. реакция на них
        """
        pass

    def add_rocket(self, rocket: RocketCCP):
        """
        Добавление новой ЗУР в список ракет ПБУ
        """
        self._rocket_dict[self._next_rocket_id] = rocket
        print(f"В ПБУ добавлена ракета с id: {self._next_rocket_id}")
        self._next_rocket_id += 1


    def delete_rocket(self, rocket_id: int):
        """
        :param rocket_id: id ракеты
        """
        self._rocket_dict.pop(rocket_id, None)
        print(f"В ПБУ удалена ракета с id: {rocket_id}")

    def send_msg_to(self):
        """
        Методы общения с другими модулями путем сообщений
        """
        pass

    def simulate(self, time: float) -> None:
        """
        Запуск моделирования
        :param time: текущее время
        """
        pass
