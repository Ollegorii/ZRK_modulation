from abc import ABCMeta, abstractmethod

class AirObject(metaclass=ABCMeta):
    """
    Базовый абстрактный класс для воздушных объектов
    """
    def __init__(self):
        self.__pos = None
        self.__velocity = None
    
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
