from .Manager import Manager
import numpy as np
from .Messages import *
from .Missile import Missile
from typing import List

class MissileLauncher(BaseModel):
    """
    Класс пусковой установки
    Отвечает за хранение, подготовку и запуск ракет по воздушным целям
    """
    
    def __init__(self, manager: Manager, id: int, pos: np.array, max_missiles: int = 5) -> None:
        """
        Инициализация пусковой установки
        
        :param manager: Менеджер моделей системы
        :param id: Уникальный идентификатор установки
        :param pos: Позиция установки в пространстве
        :param max_missiles: Максимальное количество ракет на установке
        """
        super().__init__(manager, id, pos)
        self.max_missiles = max_missiles
        self.missiles = []  # Список доступных ракет
        self.launched_missiles = []  # Список запущенных ракет
        
        # self._manager.add_module(self)
        
        print(f"Пусковая установка (ID: {self.id}) инициализирована на позиции {self.pos}")
    
    def add_missile(self, missile: Missile) -> bool:
        """
        Добавление ракеты в пусковую установку
        
        :param missile: Объект ракеты для добавления
        :return: Успешность добавления
        """
        if len(self.missiles) < self.max_missiles and not missile.launched:
            self.missiles.append(missile)
            print(f"Ракета {missile.name} (ID: {missile.id}) добавлена в пусковую установку (ID: {self.id})")
            return True
        else:
            print(f"Невозможно добавить ракету {missile.name} (ID: {missile.id}). Пусковая установка заполнена или ракета уже запущена.")
            return False
    
    def count_missiles(self) -> int:
        """
        Подсчет количества доступных для запуска ракет
        
        :return: Количество незапущенных ракет
        """
        return len(self.missiles)
    
    def launch_missile(self) -> None:
        """
        Запуск ракеты по указанной цели
        
        :param target_position: Координаты цели для поражения
        :return: Запущенная ракета или None, если запуск невозможен
        """
        if not self.missiles:
            print(f"Пусковая установка (ID: {self.id}) не имеет доступных ракет для запуска")
            return None
        
        # Берем первую доступную ракету из списка
        missile = self.missiles.pop(0)
        
        # Запускаем ракету
        success = missile.launch()
        
        if success:
            self.launched_missiles.append(missile)
            print(f"Ракета {missile.name} (ID: {self.id}) успешно запущена с пусковой установки (ID: {self.id})")
            
            # Отправляем сообщение о запуске ракеты
            current_time = int(Timer().get_time())
            launch_msg = LaunchedMissileMessage(
                time=current_time,
                sender_ID=self.id,
                receiver_ID=0,
                missile_id=missile.id
            )
            self.send_message(launch_msg)
        else:
            # Если запуск не удался, возвращаем ракету обратно в список
            self.missiles.append(missile)
            print(f"Не удалось запустить ракету {missile.name} (ID: {missile.id}) с пусковой установки (ID: {self.id})")
    
    def step(self) -> None:
        """
        Выполнение одного шага симуляции для пусковой установки
        """
        print(f"Шаг симуляции пусковой установки (ID: {self.id}). Доступно ракет: {self.count_missiles()}")
        
        # Обработка сообщений от других модулей (команды на запуск)
        messages = self._manager.give_messages_by_id(self.id)
        for msg in messages:
            # Ищем сообщения с командой на запуск ракеты
            if isinstance(msg, LaunchMissileMessage):
                print(f"Получена команда на запуск ракеты")
                self.launch_missile()
    
    def send_message(self, msg) -> None:
        """
        Отправка сообщения через менеджер
        
        :param msg: Сообщение для отправки
        """
        self._manager.add_message(msg)
    
    def get_messages(self) -> List[BaseMessage]:
        """
        Получение всех сообщений, адресованных этой пусковой установке
        
        :return: Список сообщений
        """
        return self._manager.give_messages_by_id(self.id)