from enum import Enum
from .AirObject import AirObject
import numpy as np
from .Manager import Manager

class TargetType(Enum):
    AIR_PLANE = "самолет"
    HELICOPTER = "вертолет"
    ANOTHER = "другое"


class Target(AirObject):
    """
    Класс воздушной цели
    """

    def __init__(
        self,
        manager: Manager,
        id: int,
        pos: np.ndarray = None,
        trajectory: np.ndarray = None,
        type: TargetType = TargetType.ANOTHER
    ):
        """
        Инициализация воздушной цели

        :param type: тип цели
        """
        super().__init__(manager, id, pos, trajectory)  # Вызываем инициализатор родительского класса
        self.__type = type

    @property
    def type(self) -> TargetType:
        return self.__type

    def step(self):
        return super().step()
