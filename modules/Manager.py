from typing import List, Optional, Dict
from .Timer import Timer
from .BaseMessage import BaseMessage

class Manager:
    """Класс для управления обменом сообщениями между модулями и запуском симуляции"""
    def __init__(self):
        self.time = Timer()
        self.messages = []   # Список всех сообщений
        self.modules = []    # Список модулей системы

    def add_module(self, module) -> None:
        """Добавление модуля в систему"""
        if module not in self.modules:
            self.modules.append(module)
            print(f"Модуль с ID {module.id if hasattr(module, 'id') else 'unknown'} добавлен в систему")
        else:
            print(f"Модуль с ID {module.id if hasattr(module, 'id') else 'unknown'} уже существует в системе")

    def remove_module(self, module_id: int) -> bool:
        """Удаление модуля из системы по ID"""
        for i, module in enumerate(self.modules):
            if hasattr(module, 'id') and module.id == module_id:
                self.modules.pop(i)
                print(f"Модуль с ID {module_id} удален из системы")
                return True
        print(f"Модуль с ID {module_id} не найден в системе")
        return False

    def get_module_by_id(self, module_id: int):
        """Получение модуля по ID"""
        for module in self.modules:
            if hasattr(module, 'id') and module.id == module_id:
                return module
        return None
    def add_message(self, msg: BaseMessage) -> None:
        """Добавление нового сообщения в список сообщений
        
        :param msg: Сообщение для добавления
        """
        self.messages.append(msg)
        # Сортировка сообщений по важности
        self.messages.sort(key=lambda x: -x.priority)

    def give_messages(self) -> List[BaseMessage]:
        """Возвращает все сообщения"""
        return self.messages

    def give_messages_by_id(self, receiver_id: int) -> List[BaseMessage]:
        """Возвращает все сообщения для указанного получателя
        
        :param receiver_id: ID модуля-получателя
        :return: Список сообщений для данного получателя
        """
        return [msg for msg in self.messages if msg.receiver_id == receiver_id]
    
    def run_simulation(self, end_time: int) -> None:
        """Запуск симуляции на указанное количество времени
        
        :param end_time: время завершения симуляции
        """
        while self.time.get_time() < end_time:
            print(f"Текущее время: {self.time.get_time()}")
            # Запуск шага симуляции для каждого модуля
            for module in self.modules:
                module.step()
            
            # Обновление времени после обработки всех модулей
            self.time.update_time()
