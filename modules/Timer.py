# modules/Timer.py

from .constants import *

class Timer:
    """Класс для управления временем симуляции (ОБЫЧНЫЙ КЛАСС)"""
    
    def __init__(self):
        self.__dt = SIMULATION_STEP
        self.__time = 0
    
    def set_time(self, time: int) -> None:
        """Установка текущего времени симуляции"""
        self.__time = time
    
    def set_dt(self, dt: int) -> None:
        """Установка текущего времени симуляции"""
        self.__dt = dt

    def get_time(self) -> int:
        """Получение текущего времени симуляции"""
        return self.__time
    
    def update_time(self) -> None:
        """Обновление времени на один шаг"""
        self.__time += self.__dt

    def get_dt(self) -> float:
        """Получение разницы между шагами времени"""
        return self.__dt
