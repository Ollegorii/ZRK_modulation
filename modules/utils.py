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
        self.speed_mod = np.linalg.norm(trajectory.velocity)

    @property
    def type(self) -> TargetType:
        return self.__type

    def step(self):
        return super().step()
    
    def __repr__(self) -> str:
        """
        Строковое представление объекта цели
        
        :return: строка, содержащая информацию о цели
        """
        position_str = f"[{', '.join(f'{coord:.2f}' for coord in self.pos)}]"
        
        # Получаем скорость из траектории, если она существует
        if hasattr(self, 'trajectory') and self.trajectory is not None:
            velocity = self.trajectory.velocity
            velocity_str = f"[{', '.join(f'{vel:.2f}' for vel in velocity)}]"
        else:
            velocity_str = "[unknown]"
            
        return f"Target(id={self.id}, type={self.__type.name}, pos={position_str}, vel={velocity_str})"
