from abc import abstractmethod
import numpy as np
from BaseModel import BaseModel


class Trajectory:
    """
    Моделирует прямолинейное равномерное движение: S = S0 + V * t
    """
    def __init__(self, velocity=(0.0, 0.0, 0.0), start_pos=(0.0, 0.0, 0.0)):
        self.velocity = np.array(velocity, dtype=np.float64)
        self.start_pos = np.array(start_pos, dtype=np.float64)

    def get_pos(self, t: float) -> np.ndarray:
        """Вычисляет координаты в момент времени t"""
        return self.start_pos + self.velocity * t


class AirObject(BaseModel):
    """
    Абстрактный базовый класс для воздушных объектов
    """
    def __init__(self, manager, id: int, pos: np.ndarray, trajectory: Trajectory):
        super().__init__(manager, id, pos)
        self.trajectory = trajectory

    @abstractmethod
    def step(self) -> None:
        super().step()