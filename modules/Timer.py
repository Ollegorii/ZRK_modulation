import constants


class Timer:
    """Класс для управления временем симуляции"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Timer, cls).__new__(cls)
            cls._instance.dt = constants.SUMULATION_TIME_STEP  # в секундах
            cls._instance.time = 0
        return cls._instance
    
    def set_time(self, time: float) -> None:
        """Установка текущего времени симуляции"""
        self.time = time
    
    def get_time(self) -> float:
        """Получение текущего времени симуляции"""
        return self.time
    
    def update_time(self) -> None:
        """Обновление времени на один шаг"""
        self.time += self.dt
