import numpy as np
from enum import Enum

from .BaseModel import BaseModel
from .AirObject import AirObject


class TargetType(Enum):
    AIR_PLANE = "самолет"
    HELICOPTER = "вертолет"
    ANOTHER = "другое"


class Target(AirObject):
    """
    Класс воздушной цели
    """

    def __init__(self, id: int, type: TargetType, pos: np.array=None, velocity: np.array=None):
        """
        Инициализация воздушной цели

        :param type: тип цели
        """
        super().__init__(id, pos, velocity)  # Вызываем инициализатор родительского класса
        self.__type = type

    @property
    def type(self) -> TargetType:
        return self.__type



class AirEnv(BaseModel):
    """
    Класс воздушной обстановки
    """

    def __init__(self, manager, id: int, pos: np.array) -> None:
        """
        Класс воздушной обстановки

        :param manager: менеджер моделей
        :param id: ID объекта моделирования
        :param pos: позиция объекта
        """
        super().__init__(manager, id, pos)
        self.__targets = []

    def add_target(self, target) -> None:
        """
        Добавление новой цели в ВО

        :param target: цель для добавления
        """
        self.__targets.append(target)

    def step(self) -> None:
        """
        Шаг симуляции ВО
        """
        for target in self.__targets:
            target.step()

        # self.send_message(targets_message)
