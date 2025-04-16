from typing import List
import numpy as np
from enum import Enum

from .BaseModel import BaseModel
from .AirObject import AirObject
from .Messages import ActiveObjectsMessage
from .utils import Target

class AirEnv(BaseModel):
    """
    Класс воздушной обстановки
    """

    def __init__(self, manager, id: int, pos: np.ndarray) -> None:
        """
        Класс воздушной обстановки

        :param manager: менеджер моделей
        :param id: ID объекта моделирования
        :param pos: позиция объекта
        """
        super().__init__(manager, id, pos)
        self.__targets = []

    def add_targets(self, targets: List[Target]) -> None:
        """
        Добавление новой цели в ВО

        :param targets: цель для добавления
        """
        for target in targets:
            self.__targets.append(target)

    def step(self) -> None:
        """
        Шаг симуляции ВО
        """
        for target in self.__targets:
            target.step()

        self._manager.add_message(ActiveObjectsMessage(
            time=self._manager.time.get_time(),
            sender_id=self.id,
            receiver_id=None,
            active_objects=self.__targets,
        ))
