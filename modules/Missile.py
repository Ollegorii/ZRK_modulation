import numpy as np
from typing import Optional
from .AirObject import AirObject, Trajectory
from .constants import MessageType, MISSILE_VELOCITY_MODULE, MISSILE_DETONATE_RADIUS, MISSILE_DETONATE_PERIOD


class Missile(AirObject):
    """Класс, моделирующий работу ЗУР с корректировкой траектории"""

    def __init__(self,
                 manager,
                 id: int,
                 pos: np.ndarray,
                 velocity_module: float = MISSILE_VELOCITY_MODULE,
                 detonate_radius: float = MISSILE_DETONATE_RADIUS,
                 detonate_period: float = MISSILE_DETONATE_PERIOD):

        initial_trajectory = Trajectory(start_pos=pos)
        super().__init__(manager, id, pos, initial_trajectory)
        self.speed_mod = velocity_module
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
        # Расчет параметров траектории с текущей позиции
        target_vel = target.trajectory.velocity
        D = target.pos - self.pos

        A = np.sum(np.square(target_vel)) - self.speed_mod**2
        B = 2 * np.dot(target_vel, D)
        C = np.sum(np.square(D))

        discriminant = B**2 - 4*A*C
        if discriminant < 0:
            raise ValueError("Невозможно рассчитать траекторию")

        roots = [
            (-B + np.sqrt(discriminant)) / (2*A),
            (-B - np.sqrt(discriminant)) / (2*A)
        ]

        delta_t = min([r for r in roots if r > 0], default=None)
        if delta_t is None:
            raise ValueError("Нет допустимого времени перехвата")

        V_rocket = target_vel + D/delta_t
        V_norm = V_rocket / np.linalg.norm(V_rocket) * self.speed_mod

        # Сохраняем оригинальное время запуска при обновлении траектории
        new_trajectory = Trajectory(
            velocity=tuple(V_norm),
            start_pos=tuple(self.pos),
            start_time=self._manager.time.get_time() if self.status == 'active' else 0
        )
        self._set_trajectory(new_trajectory)

    def _launch(self) -> None:
        """Запуск ракеты"""
        self.status = 'active'
        self.launch_time = self._manager.time.get_time()
        # Обновляем время старта в траектории
        self.trajectory.start_time = self.launch_time

    def _set_trajectory(self, new_trajectory: Trajectory) -> None:
        self.trajectory = new_trajectory

    def _detonate(self, target_id: int = None, self_detonation: bool = True) -> None:
        """Инициирование подрыва"""
        from .Messages import MissileDetonateMessage, MissilePosMessage
        self.status = 'detonated'

        # Отправка сообщений о подрыве
        detonate_msg = MissileDetonateMessage(
            sender_id=self.id,
            target_id=target_id,
            self_detonation=self_detonation
        )
        self._manager.add_message(detonate_msg)

    def step(self) -> None:
        current_time = self._manager.time.get_time()
        dt = self._manager.time.get_dt()
        from .Messages import MissileDetonateMessage, MissilePosMessage
        if self.status == 'ready':
            # Проверка сообщений на запуск
            messages = self._manager.give_messages_by_type(
                MessageType.LAUNCH_MISSILE,
                self.id,
                step_time=current_time-dt
            )
            if messages:
                self._launch()

        elif self.status == 'active':
            # Обработка сообщений с обновлением цели
            update_messages = self._manager.give_messages_by_type(
                MessageType.UPDATE_TARGET,
                self.id,
                step_time=current_time-dt
            )
            for msg in update_messages:
                self.target = msg.upd_object
                self._calculate_trajectory(self.target)
                print(f"Upd target: {self.target}")

            # Обновление позиции
            super().step()

            # Отправка позиции
            pos_msg = MissilePosMessage(
                sender_id=self.id
            )
            self._manager.add_message(pos_msg)

            # Проверка дистанции до цели
            if self.target and np.linalg.norm(self.pos - self.target.pos) <= self.detonate_radius:
                self._detonate(target_id=self.target.id, self_detonation=False)

            # Расчет времени относительно оригинального запуска
            flight_time = current_time - self.launch_time

            # Проверка таймера (время с момента запуска)
            if flight_time >= self.detonate_period:
                self._detonate(self_detonation=True)

        elif self.status == 'detonated':
            pass
    
    def __repr__(self) -> str:
        """
        Строковое представление объекта цели
    
        :return: строка, содержащая информацию о цели
        """
        position_str = f"[{', '.join(f'{coord:.2f}' for coord in self.pos)}]"
    
        # Получаем скорость из траектории, если она существует
        if hasattr(self, 'trajectory') and self.trajectory is not None:
            velocity = self.trajectory.velocity
            velocity_str = f"[{', '.join(f'{vel:.2f}' for vel in velocity)}]"
        else:
            velocity_str = "[unknown]"
    
        return f"Missile(id={self.id}, pos={position_str}, vel={velocity_str}, prev_pos={self.prev_pos})"
