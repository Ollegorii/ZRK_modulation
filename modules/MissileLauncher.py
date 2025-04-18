from .Manager import Manager
import numpy as np
from .Messages import LaunchMissileMessage, LaunchedMissileMessage, MissileCountRequestMessage, CPPLaunchMissileRequestMessage, MissileCountResponseMessage
from .Missile import Missile
from typing import List, Optional
from .AirEnv import AirEnv, Target
from .constants import *
from .BaseModel import BaseModel

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
        print(f"Пусковая установка (ID: {self.id}) инициализирована на позиции {self.pos}")

    def add_missile(self, missile: Missile) -> bool:
        """
        Добавление ракеты в пусковую установку

        :param missile: Объект ракеты для добавления
        :return: Успешность добавления
        """
        if len(self.missiles) < self.max_missiles and not missile.is_launched:
            missile.dispatcher = self._manager  # Устанавливаем диспетчер
            self.missiles.append(missile)
            print(f"Ракета ID: {missile.id} добавлена в пусковую установку (ID: {self.id})")
            return True
        print(f"Невозможно добавить ракету ID: {missile.id}. Пусковая установка заполнена или ракета уже запущена.")
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
            print(f"Пусковая установка (ID: {self.id}) не имеет доступных ракет для запуска")
            return None

        missile = self.missiles.pop(0)

        # Запускаем ракету
        missile.set(target)
        launch_msg = LaunchMissileMessage(
            receiver_id=missile.id,
            sender_id=self.id,
        )

        self._manager.add_message(launch_msg)

        self.launched_missiles.append(missile)
        print(f"Ракета ID: {missile.id} успешно запущена с пусковой установки (ID: {self.id})")

        # Отправляем сообщение о запуске ракеты
        launched_msg = LaunchedMissileMessage(
            sender_id=self.id,
            receiver_id=CCP_ID,
            missile=missile,
            target_id=target_id,
        )

        self._manager.add_message(launched_msg)
        # TODO раскоментить когда air_env добавит функциональность
        # self.air_env.add_missile(missile)

        return None if missile is None else missile

    def step(self) -> None:
        """
        Выполнение одного шага симуляции для пусковой установки
        """
        current_time = self._manager.time.get_time()
        print(f"Шаг симуляции пусковой установки (ID: {self.id}) в t={current_time}. Доступно ракет: {self.count_missiles()}")

        # Обработка сообщений
        messages = self._manager.give_messages_by_id(self.id)
        for msg in messages:
            if isinstance(msg, CPPLaunchMissileRequestMessage):
                print(f"Получена команда на запуск ракеты к цели ID: {msg.target_id}")
                self.launch_missile(
                    target_pos=msg.target,
                    target_id=msg.target_id,
                    radar_id=msg.radar_id
                )
            elif isinstance(msg, MissileCountRequestMessage):
                # Отправляем ответ с количеством ракет
                count_msg = MissileCountResponseMessage(
                    time=current_time,
                    sender_id=self.id,
                    receiver_id=msg.sender_id,
                    count=self.count_missiles()
                )
                self._manager.add_message(count_msg)
                print(f"Отправлен ответ с количеством ракет: {self.count_missiles()}")

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
                    print(f"Ракета ID: {missile.id} поразила цель!")
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
