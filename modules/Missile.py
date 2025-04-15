import numpy as np
from typing import Optional
from AirObject import AirObject, Trajectory
from Messages import MissileDetonateMessage, MissilePosMessage, UpdateTargetPosition
from constants import MessageType, MISSILE_VELOCITY_MODULE, MISSILE_DETONATE_RADIUS, MISSILE_DETONATE_PERIOD


class Missile(AirObject):
    """Класс, моделирующий работу ЗУР"""

    def __init__(self,
                 manager,
                 id: int,
                 pos: np.ndarray,
                 velocity_module: float = MISSILE_VELOCITY_MODULE,
                 detonate_radius: float = MISSILE_DETONATE_RADIUS,
                 detonate_period: float = MISSILE_DETONATE_PERIOD):

        initial_trajectory = Trajectory(start_pos=pos)
        super().__init__(manager, id, pos, initial_trajectory)
        self.velocity_module = velocity_module
        self.detonate_radius = detonate_radius
        self.detonate_period = detonate_period
        self.status = 'wait'
        self.launch_time: Optional[float] = None
        self.target: Optional[AirObject] = None

    def set(self, target: AirObject) -> None:
        """Взведение ЗУР в боевое положение"""
        if self.status != 'wait':
            return

        self.status = 'ready'
        self.target = target
        self._calculate_trajectory(target)

    def _calculate_trajectory(self, target: AirObject) -> None:
        # Расчет параметров траектории
        target_vel = target.trajectory.velocity
        D = target.pos - self.pos

        A = np.sum(np.square(target_vel)) - self.velocity_module ** 2
        B = 2 * np.dot(target_vel, D)
        C = np.sum(np.square(D))

        discriminant = B ** 2 - 4 * A * C
        if discriminant < 0:
            raise ValueError("Невозможно рассчитать траекторию")

        roots = [
            (-B + np.sqrt(discriminant)) / (2 * A),
            (-B - np.sqrt(discriminant)) / (2 * A)
        ]

        delta_t = min([r for r in roots if r > 0], default=None)
        if delta_t is None:
            raise ValueError("Нет допустимого времени перехвата")

        V_rocket = target_vel + D / delta_t
        V_norm = V_rocket / np.linalg.norm(V_rocket) * self.velocity_module

        self._set_trajectory(Trajectory(tuple(V_norm), tuple(self.pos)))

    def _launch(self) -> None:
        """Запуск ракеты"""
        self.status = 'active'
        self.launch_time = self._manager.time.get_time()

    def _set_trajectory(self, new_trajectory: Trajectory) -> None:
        self.trajectory = new_trajectory

    def _detonate(self) -> None:
        """Инициирование подрыва"""
        self.status = 'detonated'
        current_time = self._manager.time.get_time()

        # Отправка сообщений о подрыве
        detonate_msg = MissileDetonateMessage(
            time=current_time,
            sender_id=self.id,
            receiver_id=None,  # Широковещательное сообщение
            missile_id=self.id
        )
        self._manager.add_message(detonate_msg)

    def step(self) -> None:
        current_time = self._manager.time.get_time()

        if self.status == 'ready':
            # Проверка сообщений на запуск
            messages = self._manager.give_messages_by_type(
                MessageType.LAUNCH_MISSILE,
                self.id
            )
            if messages:
                self._launch()

        elif self.status == 'active':
            dt = current_time - self.launch_time

            # Обновление позиции
            self.pos = self.trajectory.get_pos(dt)

            # Отправка позиции
            pos_msg = MissilePosMessage(
                time=current_time,
                sender_id=self.id,
                receiver_id=None,  # Для ВО
                missile_id=self.id
            )
            self._manager.add_message(pos_msg)

            # Проверка дистанции до цели
            if self.target and np.linalg.norm(self.pos - self.target.pos) < self.detonate_radius:
                self._detonate()

            # Проверка таймера
            if dt >= self.detonate_period:
                self._detonate()

        elif self.status == 'detonated':
            # Удаление из системы
            self._manager.remove_module(self.id)