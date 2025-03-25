import numpy as np
from abc import ABCMeta, abstractmethod

from modules.Manager import BaseMessage, Manager


class BaseModel(ABCMeta):
    @abstractmethod
    def __init__(self, manager: Manager, id: int, pos: np.array) -> None:
        """ Базовый класс
        :param manager: менеджер моделей
        :param id: ID объекта моделирования
        """
        self._manager = manager
        self.__id = id
        self.__pos = pos

    @property
    def id(self):
        return self.__id

    @property
    def pos(self):
        return self.__pos

    @pos.setter
    def pos(self, new_pos):
        self.__pos = new_pos

    @abstractmethod
    def step(self) -> None:
        pass

    def send_message(self, msg: BaseMessage) -> None:
        pass

    def get_messages(self) -> list[BaseMessage]:
        pass
