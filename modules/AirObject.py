from abc import ABCMeta, abstractmethod
import numpy as np

class AirObject(metaclass=ABCMeta):
    """
    Базовый абстрактный класс для воздушных объектов
    """
    def __init__(self, id: int, pos: np.array=None, velocity: np.array=None):
        self.id = id
        self.__pos = pos
        self.__velocity = velocity
    
    @property
    def pos(self):
        return self.__pos
    
    @pos.setter
    def pos(self, value):
        self.__pos = value
    
    @property
    def velocity(self):
        return self.__velocity
    
    @velocity.setter
    def velocity(self, value):
        self.__velocity = value
    
    def step(self):
        """
        Метод для выполнения шага симуляции
        """
        # Базовая реализация, например, обновление позиции
        if self.__pos is not None and self.__velocity is not None:
            self.__pos += self.__velocity
