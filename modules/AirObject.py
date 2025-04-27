from abc import abstractmethod
import numpy as np
from .BaseModel import BaseModel


class Trajectory:
    """
    Моделирует движение с учетом времени старта
    S = start_pos + V * (t - start_time)
    """

    def __init__(self,
                 velocity=(0.0, 0.0, 0.0),
                 start_pos=(0.0, 0.0, 0.0),
                 start_time: float = 0.0):
        self.velocity = np.array(velocity, dtype=np.float64)
        self.start_pos = np.array(start_pos, dtype=np.float64)
        self.start_time = start_time

    def get_pos(self, t: float) -> np.ndarray:
        """Вычисляет координаты в момент времени t"""
        return self.start_pos + self.velocity * (t - self.start_time)


class AirObject(BaseModel):
    """
    Абстрактный базовый класс для воздушных объектов
    """
    def __init__(self, manager, id: int, pos: np.ndarray, trajectory: Trajectory):
        super().__init__(manager, id, pos)
        self.trajectory = trajectory
        self.speed_mod = np.linalg.norm(trajectory.velocity)

    def step(self):
        current_time = self._manager.time.get_time()
        self.prev_pos = self.pos if self.trajectory.start_time != current_time else None
        self.pos = self.trajectory.get_pos(current_time)
