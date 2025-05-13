import numpy as np
from typing import Optional
from .AirObject import AirObject, Trajectory
from .constants import MessageType, MISSILE_VELOCITY_MODULE, MISSILE_DETONATE_RADIUS, MISSILE_DETONATE_PERIOD
from .utils import to_seconds


class InterceptionError(Exception):
    """
    Исключение, сигнализирующее о невозможности перехвата цели
    """
    pass


class Missile(AirObject):
    """Класс, моделирующий работу ЗУР с корректировкой траектории"""

    def __init__(self,
                 manager,
                 id: int,
                 pos: tuple = (0, 0, 0),
                 velocity_module: float = MISSILE_VELOCITY_MODULE,
                 detonate_radius: float = MISSILE_DETONATE_RADIUS,
                 detonate_period: float = MISSILE_DETONATE_PERIOD):

        initial_trajectory = Trajectory(start_pos=pos)
        super().__init__(manager, id, np.array(pos), initial_trajectory)
        self.speed_mod = velocity_module
        self.detonate_radius = detonate_radius
        self.detonate_period = detonate_period
        self.status = 'ready'
        self.launch_time: Optional[float] = None
        self.target: Optional[AirObject] = None

    def _calculate_trajectory_params(self, target: AirObject):
        """
        Рассчитывает вектор скорости ракеты для перехвата движущейся цели и время до перехвата.
        """
        target_velocity = target.speed_mod * target.velocity

        D = target.pos - self.pos
        A = np.dot(target_velocity, target_velocity) - self.speed_mod ** 2
        B = 2 * np.dot(target_velocity, D)
        C = np.dot(D, D)
        if abs(A) < 1e-8:
            if abs(B) < 1e-8:
                raise ValueError("Нет решения: неподвижная цель или совпадающие позиции")
            delta_t = -C / B
            if delta_t <= 0:
                raise InterceptionError("Не существует положительного времени перехвата.")
        else:
            discr = B ** 2 - 4 * A * C
            if discr < 0:
                raise InterceptionError("Цель недосягаема: отрицательный дискриминант.")
            t1 = (-B + np.sqrt(discr)) / (2 * A)
            t2 = (-B - np.sqrt(discr)) / (2 * A)
            candidates = [t for t in (t1, t2) if t > 0]
            if not candidates:
                raise InterceptionError("Нет положительных корней для времени перехвата.")
            delta_t = min(candidates)

        V_req = target.speed_mod + D / delta_t
        V_norm = V_req / np.linalg.norm(V_req) * self.speed_mod
        return V_norm, delta_t

    def _launch(self, target: AirObject):
        from .Messages import MissileSuccessfulLaunchMessage, MissileLaunchCancelledMessage

        try:
            V_norm, delta_t = self._calculate_trajectory_params(target)
            self.target = target
            new_trajectory = Trajectory(
                velocity=tuple(V_norm),
                start_pos=tuple(self.pos),
                start_time=to_seconds(self._manager.time.get_time())
            )
            self._set_trajectory(new_trajectory)
            self.launch_time = to_seconds(self._manager.time.get_time())
            msg = MissileSuccessfulLaunchMessage(
                sender_id=self.id,
                launch_time=self.launch_time,
                target=self.target,
                missile=self
            )
            self._manager.add_message(msg)
            self.status = 'active'
        except (InterceptionError, ValueError) as e:
            msg = MissileLaunchCancelledMessage(
                sender_id=self.id,
                reason=str(e),
                missile=self
            )
            self._manager.add_message(msg)

    def _set_trajectory(self, new_trajectory: Trajectory):
        self.trajectory = new_trajectory

    def _detonate(self, target_id: int = None, self_detonation: bool = True):
        from .Messages import MissileDetonateMessage
        msg = MissileDetonateMessage(
            sender_id=self.id,
            target_id=target_id,
            self_detonation=self_detonation
        )
        self._manager.add_message(msg)
        self.status = 'detonated'

    def step(self):
        from .Messages import MissilePosMessage
        current_time = self._manager.time.get_time()
        dt = self._manager.time.get_dt()

        if self.status == 'ready':
            messages = self._manager.give_messages_by_type(
                MessageType.LAUNCH_MISSILE,
                self.id,
                step_time=current_time
            )
            if messages:
                self._launch(messages[-1].target)

        elif self.status == 'active':
            update_msgs = self._manager.give_messages_by_type(
                MessageType.UPDATE_TARGET,
                self.id,
                step_time=current_time - dt
            )
            for msg in update_msgs:
                self.target = msg.upd_object
                try:
                    V_norm, delta_t = self._calculate_trajectory_params(self.target)
                    new_traj = Trajectory(
                        velocity=tuple(V_norm),
                        start_pos=tuple(self.pos),
                        start_time=to_seconds(current_time)
                    )
                    self._set_trajectory(new_traj)
                except (InterceptionError, ValueError):
                    continue

            super().step()

            pos_msg = MissilePosMessage(sender_id=self.id)
            self._manager.add_message(pos_msg)

            distance = np.linalg.norm(self.target.pos - self.pos)
            if distance <= self.detonate_radius:
                self._detonate(target_id=self.target.id, self_detonation=False)
                return

            self.detonate_period -= to_seconds(dt)
            if self.detonate_period <= 0:
                self._detonate()

        elif self.status == 'detonated':
            pass
