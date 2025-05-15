import numpy as np
from typing import Optional, Tuple
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

    def _calculate_trajectory_params(self, target: "AirObject") -> Tuple[np.ndarray, float]:
        """
        Calculate the velocity vector V (with magnitude self.speed_mod) and
        interception time delta_t such that the interceptor at self.pos with
        speed magnitude self.speed_mod will intercept the target.

        Args:
            self: An object with attributes:
                - pos: np.ndarray of shape (3,), initial position of interceptor.
                - speed_mod: float, speed magnitude of interceptor.
            target: An AirObject with attributes:
                - pos: np.ndarray of shape (3,), initial position of target.
                - speed_mod: float, speed magnitude of target.
                - velocity: np.ndarray of shape (3,), unit direction vector of target's velocity.

        Returns:
            V: np.ndarray of shape (3,), required velocity vector for interceptor.
            delta_t: float, time until interception.
        """
        # Relative displacement from interceptor to target
        d = target.pos - self.pos

        # Target velocity vector
        v_t = target.velocity * target.speed_mod

        # Interceptor speed magnitude
        v0 = self.speed_mod

        # Quadratic coefficients for interception time
        # a t^2 + b t + c = 0
        a = np.dot(v_t, v_t) - v0 ** 2
        b = 2 * np.dot(d, v_t)
        c = np.dot(d, d)

        # Solve for t
        if abs(a) < 1e-6:
            # Degenerate case: speeds are nearly equal, linear solution
            if abs(b) < 1e-6:
                raise ValueError(
                    "No interception possible: target and interceptor are stationary relative or parallel.")
            t = -c / b
        else:
            disc = b ** 2 - 4 * a * c
            if disc < 0:
                raise ValueError("No real interception time: target is too fast or out of range.")
            sqrt_disc = np.sqrt(disc)
            t1 = (-b + sqrt_disc) / (2 * a)
            t2 = (-b - sqrt_disc) / (2 * a)
            # Select smallest positive time
            times = [t for t in (t1, t2) if t > 0]
            if not times:
                raise ValueError("Interception times are not positive; interception not possible in future.")
            t = min(times)

        # Compute required interceptor velocity vector
        V = (d / t) + v_t

        # Normalize to exact magnitude self.speed_mod to avoid rounding drift
        V = V / np.linalg.norm(V) * v0

        return V, t

    def _launch(self, target: AirObject, launcher_id):
        from .Messages import MissileSuccessfulLaunchMessage, MissileLaunchCancelledMessage

        try:
            V, t = self._calculate_trajectory_params(target)
            self.target = target
            new_trajectory = Trajectory(
                velocity=tuple(V),
                start_pos=tuple(self.pos),
                start_time=to_seconds(self._manager.time.get_time())
            )
            self._set_trajectory(new_trajectory)
            self.launch_time = to_seconds(self._manager.time.get_time())
            msg = MissileSuccessfulLaunchMessage(
                sender_id=self.id,
                launch_time=self.launch_time,
                target=self.target,
                missile=self,
                launcher_id=launcher_id
            )
            self._manager.add_message(msg)
            self.status = 'active'
        except (InterceptionError, ValueError) as e:
            msg = MissileLaunchCancelledMessage(
                sender_id=self.id,
                reason=str(e),
                missile=self,
                launcher_id=launcher_id
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
                self._launch(messages[-1].target, messages[-1].sender_id)

        elif self.status == 'active':
            update_msgs = self._manager.give_messages_by_type(
                MessageType.UPDATE_TARGET,
                self.id,
                step_time=current_time - dt
            )
            for msg in update_msgs:
                self.target = msg.upd_object
                try:
                    V, t = self._calculate_trajectory_params(self.target)
                    new_trajectory = Trajectory(
                        velocity=tuple(V),
                        start_pos=tuple(self.pos),
                        start_time=to_seconds(self._manager.time.get_time())
                    )
                    self._set_trajectory(new_trajectory)
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
