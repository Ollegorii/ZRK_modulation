import math
import numpy as np
from typing import Tuple, Optional, List
from abc import ABC
from datetime import datetime
from Messages import BaseMessage, MissileDetonateMessage, MissilePosMessage


class Trajectory:
    """Задает закон прямолинейного равномерного движения"""

    def __init__(
            self,
            velocity: Tuple[float, float, float] = (0, 0, 0),
            start_pos: Tuple[float, float, float] = (0, 0, 0),
            start_time: float = 0.0
    ):
        self.velocity = np.array(velocity, dtype=np.float64)
        self.start_pos = np.array(start_pos, dtype=np.float64)
        self.start_time = start_time

    def get_pos(self, t: float) -> Tuple[float, float, float]:
        """Вычисляет позицию в момент времени t"""
        dt = t - self.start_time
        pos = self.start_pos + self.velocity * dt
        return tuple(pos.round(6))


class AirObject(ABC):
    """Абстрактный базовый класс для воздушных объектов"""

    def __init__(self, manager, obj_id: int):
        self.manager = manager
        self.obj_id = obj_id
        self.trajectory: Optional[Trajectory] = None
        self.status: str = 'wait'

    def get_time(self) -> float:
        return self.manager.get_time()

    def send_message(self, msg: BaseMessage):
        self.manager.send_message(msg)

    def process_messages(self):
        for msg in self.manager.get_messages(self.obj_id):
            self.handle_message(msg)

    def handle_message(self, msg: BaseMessage):
        pass

    def step(self):
        self.process_messages()


class Missile(AirObject):
    """Класс зенитной управляемой ракеты (ЗУР)"""

    def __init__(
            self,
            manager,
            obj_id: int,
            velocity_module: float = 1000,
            pos: Tuple[float, float, float] = (0, 0, 0),
            detonate_radius: float = 1.0,
            detonate_period: float = 50.0
    ):
        super().__init__(manager, obj_id)
        self.velocity_module = velocity_module
        self.detonate_radius = detonate_radius
        self.detonate_period = detonate_period
        self.launch_time: Optional[float] = None
        self.target: Optional[AirObject] = None
        self.trajectory = Trajectory(start_pos=pos)

    def set(self, target: AirObject) -> None:
        """Взведение ЗУР для перехвата цели"""
        if self.status != 'wait':
            raise RuntimeError("Невозможно взвести ЗУР в текущем статусе")

        try:
            t_current = self.get_time()
            target_pos = target.trajectory.get_pos(t_current)
            v_target = target.trajectory.velocity

            D = np.array(target_pos) - self.trajectory.start_pos

            A = np.sum(np.square(v_target)) - self.velocity_module ** 2
            B = 2 * np.dot(v_target, D)
            C = np.sum(np.square(D))

            discriminant = B ** 2 - 4 * A * C

            if A == 0 or discriminant < 0:
                raise ValueError("Цель недостижима")

            sqrt_d = math.sqrt(discriminant)
            roots = [(-B + sqrt_d) / (2 * A), (-B - sqrt_d) / (2 * A)]
            valid_times = [t for t in roots if t > 0]

            if not valid_times:
                raise ValueError("Нет положительных решений")

            delta_t = min(valid_times)

            v_rocket = v_target + D / delta_t
            v_norm = self._normalize_velocity(v_rocket)

            self.trajectory = Trajectory(
                velocity=v_norm,
                start_pos=self.trajectory.start_pos,
                start_time=t_current
            )
            self.target = target
            self.status = 'ready'

        except Exception as e:
            self.status = 'fail'
            raise RuntimeError(f"Ошибка взведения: {str(e)}")

    def _normalize_velocity(self, velocity: np.ndarray) -> Tuple[float, float, float]:
        """Нормализация вектора скорости"""
        magnitude = np.linalg.norm(velocity)
        if magnitude == 0:
            raise ValueError("Нулевая скорость ракеты")
        scale = self.velocity_module / magnitude
        return tuple((velocity * scale).round(6))

    def _launch(self):
        """Приватный метод запуска ЗУР"""
        if self.status != 'ready':
            return

        self.launch_time = self.get_time()
        self.status = 'active'
        self._send_launch_notification()

    def _send_launch_notification(self):
        """Отправка уведомлений о запуске"""
        msg = BaseMessage(
            type='MISSILE_LAUNCH',
            sender_ID=self.obj_id,
            receiver_ID='ALL',
            data={
                'missile_id': self.obj_id,
                'position': self.trajectory.start_pos,
                'target_id': self.target.obj_id
            }
        )
        self.send_message(msg)

    def _detonate(self):
        """Подрыв ЗУР"""
        self.status = 'detonated'
        self._send_detonate_messages()
        self._notify_destruction()

    def _send_detonate_messages(self):
        """Отправка сообщений о подрыве"""
        pos = self.trajectory.get_pos(self.get_time())

        # Сообщение ВО
        msg = MissileDetonateMessage(
            missile_id=self.obj_id,
            pos=pos,
            sender_ID=self.obj_id,
            receiver_ID='AIR_SITUATION'
        )
        self.send_message(msg)

        # Сообщение РЛС
        msg = MissileDetonateMessage(
            missile_id=self.obj_id,
            pos=pos,
            sender_ID=self.obj_id,
            receiver_ID='RADAR'
        )
        self.send_message(msg)

    def _notify_destruction(self):
        """Уведомление о разрушении"""
        msg = BaseMessage(
            type='MISSILE_DESTROYED',
            sender_ID=self.obj_id,
            receiver_ID='ALL',
            data={'missile_id': self.obj_id}
        )
        self.send_message(msg)

    def _update_position(self):
        """Обновление позиции ЗУР"""
        current_time = self.get_time()
        new_pos = self.trajectory.get_pos(current_time)
        self.trajectory.start_pos = np.array(new_pos)

        # Отправка сообщения ВО
        msg = MissilePosMessage(
            missile_id=self.obj_id,
            pos=new_pos,
            sender_ID=self.obj_id,
            receiver_ID='AIR_SITUATION'
        )
        self.send_message(msg)

    def _check_detonation_conditions(self) -> bool:
        """Проверка условий подрыва"""
        if not self.target:
            return False

        current_time = self.get_time()
        missile_pos = np.array(self.trajectory.get_pos(current_time))
        target_pos = np.array(self.target.trajectory.get_pos(current_time))

        distance = np.linalg.norm(missile_pos - target_pos)
        time_since_launch = current_time - self.launch_time

        return distance <= self.detonate_radius or time_since_launch >= self.detonate_period

    def step(self):
        """Шаг симуляции для ЗУР"""
        super().step()

        if self.status == 'ready':
            self._check_launch_command()

        elif self.status == 'active':
            self._update_position()

            if self._check_detonation_conditions():
                self._detonate()
            else:
                self._check_target_update()

        elif self.status == 'detonated':
            pass

    def _check_launch_command(self):
        """Проверка команд на запуск"""
        for msg in self.manager.get_messages(self.obj_id):
            if msg.type == 'LAUNCH_COMMAND':
                self._launch()

    def _check_target_update(self):
        """Проверка обновлений позиции цели"""
        for msg in self.manager.get_messages(self.obj_id):
            if msg.type == 'TARGET_UPDATE':
                self._update_trajectory(msg.data['new_position'])

    def _update_trajectory(self, new_target_pos: Tuple[float, float, float]):
        """Обновление траектории при изменении позиции цели"""
        try:
            current_time = self.get_time()
            current_pos = self.trajectory.get_pos(current_time)

            D = np.array(new_target_pos) - current_pos
            time_remaining = self.detonate_period - (current_time - self.launch_time)

            if time_remaining <= 0:
                return

            new_velocity = D / time_remaining
            v_norm = self._normalize_velocity(new_velocity)

            self.trajectory = Trajectory(
                velocity=v_norm,
                start_pos=current_pos,
                start_time=current_time
            )

        except Exception as e:
            print(f"Ошибка обновления траектории: {str(e)}")