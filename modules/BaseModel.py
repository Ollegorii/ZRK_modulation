import numpy as np
from abc import ABCMeta, abstractmethod
from typing import List

from .Manager import BaseMessage, Manager


class BaseModel(metaclass=ABCMeta):
    """
    Базовый абстрактный класс для всех моделей в системе.
    Определяет общий интерфейс и базовую функциональность для всех моделируемых объектов.
    """

    @abstractmethod
    def __init__(self, manager: Manager, id: int, pos: np.array) -> None:
        """
        Базовый класс моделей

        :param manager: менеджер моделей, управляющий взаимодействием между моделями
        :param id: уникальный идентификатор объекта моделирования
        :param pos: начальная позиция объекта в пространстве (numpy array)
        """
        self._manager = manager  # Менеджер, отвечающий за коммуникацию между моделями
        self.__id = id  # Уникальный идентификатор объекта
        self.__pos = pos  # Текущая позиция объекта в пространстве

    @property
    def id(self) -> int:
        return self.__id

    @property
    def pos(self) -> np.array:
        return self.__pos

    @pos.setter
    def pos(self, new_pos: np.array) -> None:
        self.__pos = new_pos

    @abstractmethod
    def step(self) -> None:
        """
        Абстрактный метод, реализующий один шаг симуляции объекта.
        Должен быть переопределен в дочерних классах.
        """
        pass

    def send_message(self, msg) -> None:
        """
        Отправляет сообщение через менеджер другим объектам.

        :param msg: объект сообщения для отправки
        """
        pass

    def get_messages(self) -> List[BaseMessage]:
        """
        Получает список сообщений, адресованных данному объекту.

        :return: список полученных сообщений
        """
        pass
