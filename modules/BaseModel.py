import numpy as np
from abc import ABCMeta, abstractmethod

from .Manager import Manager


class BaseModel(metaclass=ABCMeta):
    """
    Базовый абстрактный класс для всех моделей в системе.
    Определяет общий интерфейс и базовую функциональность для всех моделируемых объектов.
    """

    @abstractmethod
    def __init__(self, manager: Manager, id: int, pos: np.ndarray) -> None:
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
    def pos(self) -> np.ndarray:
        return self.__pos

    @pos.setter
    def pos(self, new_pos: np.ndarray) -> None:
        self.__pos = new_pos

    @abstractmethod
    def step(self) -> None:
        """
        Абстрактный метод, реализующий один шаг симуляции объекта.
        Должен быть переопределен в дочерних классах.
        """
        pass
