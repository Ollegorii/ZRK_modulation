from typing import List
import numpy as np

from .constants import *
from .BaseModel import BaseModel
from .AirObject import AirObject
from .Messages import ActiveObjectsMessage


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
        self.__objects: List[AirObject] = []

    def step(self) -> None:
        """
        Шаг симуляции ВО
        """
        objects_to_remove = []
        for msg in self._manager.give_messages_by_type(MessageType.MISSILE_DETONATE):
            objects_to_remove.append(msg.missile_id)
            if msg.target_id is not None:
                objects_to_remove.append(msg.target_id)

        # !!! objects to add

        for idx, objects in enumerate(self.__objects[:]):
            if objects.id in objects_to_remove:
                del self.__objects[idx]

        for object in self.__objects:
            object.step()

        self._manager.add_message(ActiveObjectsMessage(
            sender_id=self.id,
            active_objects=self.__objects,
        ))
