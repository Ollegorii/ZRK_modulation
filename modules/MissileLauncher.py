from .Manager import Manager
import numpy as np
from .Messages import LaunchMissileMessage, LaunchedMissileMessage, MissileCountRequestMessage, CPPLaunchMissileRequestMessage, MissileCountResponseMessage, MissileToAirEnvMessage, MissileSuccessfulLaunchMessage, MissileLaunchCancelledMessage
from .Missile import Missile
from typing import List, Optional
from .AirEnv import AirEnv
from .utils import Target
from .constants import *
from .BaseModel import BaseModel
import logging

logger = logging.getLogger(__name__)

class MissileLauncher(BaseModel):
    """
    Класс пусковой установки
    Отвечает за хранение, подготовку и запуск ракет по воздушным целям
    """

    def __init__(self, manager: Manager, id: int, pos: np.ndarray, max_missiles: int = 5, air_env: AirEnv = None) -> None:
        """
        Инициализация пусковой установки

        :param manager: Менеджер моделей системы
        :param id: Уникальный идентификатор установки
        :param pos: Позиция установки в пространстве
        :param max_missiles: Максимальное количество ракет на установке
        """
        super().__init__(manager, id, pos)
        self.max_missiles = max_missiles
        self.missiles: List[Missile] = []  # Список доступных ракет
        self.launched_missiles: List[Missile] = []  # Список запущенных ракет
        self.air_env = air_env
        logger.info(f"Пусковая установка (ID: {self.id}) инициализирована на позиции {self.pos}")

    def add_missile(self, missile: Missile) -> bool:
        """
        Добавление ракеты в пусковую установку

        :param missile: Объект ракеты для добавления
        :return: Успешность добавления
        """
        if len(self.missiles) < self.max_missiles:
            self.missiles.append(missile)
            logger.info(f"Ракета ID: {missile.id} добавлена в пусковую установку (ID: {self.id})")
            return True
        logger.info(f"Невозможно добавить ракету ID: {missile.id}. Пусковая установка заполнена или ракета уже запущена.")
        return False

    def count_missiles(self) -> int:
        """
        Подсчет количества доступных для запуска ракет

        :return: Количество незапущенных ракет
        """
        return len(self.missiles)

    def launch_missile(self, target: Target, target_id: Optional[int] = None, radar_id: Optional[int] = None) -> Optional[Missile]:
        """
        Запуск ракеты по указанной цели

        :param target_pos: Координаты цели для поражения
        :param target_id: ID цели (если известен)
        :return: Запущенная ракета или None, если запуск невозможен
        """
        if not self.missiles:
            logger.info(f"Пусковая установка (ID: {self.id}) не имеет доступных ракет для запуска")
            return None

        missile = self.missiles.pop()

        # Запускаем ракету
        # missile.set(target)
        launch_msg = LaunchMissileMessage(
            receiver_id=missile.id,
            sender_id=self.id,
            target=target,
        )
        self._manager.add_message(launch_msg)
        missile.step()

    def step(self) -> None:
        """
        Выполнение одного шага симуляции для пусковой установки
        """
        current_time = self._manager.time.get_time()
        dt = self._manager.time.get_dt()
        logger.info(f"Шаг симуляции пусковой установки (ID: {self.id}) в t={current_time}. Доступно ракет: {self.count_missiles()}")

        # Обработка сообщений
        messages = self._manager.give_messages_by_id(self.id, step_time=current_time-dt)
        # messages += self._manager.give_messages_by_type(msg_type=MessageType.LAUNCH_SUCCESSFUL, step_time=current_time-dt)
        # messages += self._manager.give_messages_by_type(msg_type=MessageType.LAUNCH_CANCELLED, step_time=current_time-dt)
        logger.info(f"ПУ сообщения {messages}")
        for msg in messages:
            if isinstance(msg, CPPLaunchMissileRequestMessage):
                logger.info(f"Получена команда на запуск ракеты к цели ID: {msg.target}")
                self.launch_missile(
                    target=msg.target,
                    # target_id=msg.target_id,
                    radar_id=msg.radar_id
                )
            elif isinstance(msg, MissileSuccessfulLaunchMessage):
                missile = msg.missile
                self.launched_missiles.append(missile)
                logger.info(f"Ракета ID: {missile.id} успешно запущена с пусковой установки (ID: {self.id})")

                # Отправляем сообщение о запуске ракеты
                launched_msg = LaunchedMissileMessage(
                    sender_id=self.id,
                    receiver_id=CCP_ID,
                    missile=missile,
                    target_id=msg.target_id,
                )

                self._manager.add_message(launched_msg)

                # Отправляем сообщение AirEnv с новой ракетой
                msg_for_air_env = MissileToAirEnvMessage(
                    sender_id=self.id,
                    missile=missile,
                )

                self._manager.add_message(msg_for_air_env)
            elif isinstance(msg, MissileLaunchCancelledMessage):
                missile = msg.missile
                self.missiles.append(missile)
                logger.info(f"Ракета ID: {missile.id} не запущена с пусковой установки (ID: {self.id}), добавляем в список доступных ракет")
            elif isinstance(msg, MissileCountRequestMessage):
                # Отправляем ответ с количеством ракет
                count_msg = MissileCountResponseMessage(
                    time=current_time,
                    sender_id=self.id,
                    receiver_id=msg.sender_id,
                    count=self.count_missiles()
                )
                self._manager.add_message(count_msg)
                logger.info(f"Отправлен ответ с количеством ракет: {self.count_missiles()}")

    def update_launched_missiles(self, dt: float) -> None:
        """
        Обновление состояния всех запущенных ракет

        :param dt: Шаг времени
        """
        current_time = self._manager.time.get_time()
        for missile in self.launched_missiles[:]:  # Используем копию списка для безопасного удаления
            if missile.is_active:
                hit, active = missile.update(dt, current_time)
                if hit:
                    logger.info(f"Ракета ID: {missile.id} поразила цель!")
                if not active:
                    self.launched_missiles.remove(missile)

    def get_missile_count(self) -> int:
        """Возвращает общее количество ракет доступных"""
        return len(self.missiles)

    def get_status(self) -> dict:
        """
        Возвращает статус пусковой установки

        :return: Словарь с информацией о состоянии
        """
        return {
            "id": self.id,
            "position": self.pos.tolist(),
            "available_missiles": len(self.missiles),
            "launched_missiles": len(self.launched_missiles),
            "max_missiles": self.max_missiles,
            "missiles": [m.id for m in self.missiles],
            "active_missiles": [m.id for m in self.launched_missiles if m.is_active]
        }