from typing import List, Optional, Dict
from .Timer import Timer
from .BaseMessage import BaseMessage
from .constants import MessageType

class Manager:
    """Класс для управления обменом сообщениями между модулями и запуском симуляции"""
    def __init__(self):
        self.time = Timer()
        self.messages: Dict[int, List[BaseMessage]] = {}  # Словарь: {время_шага: [сообщения]}
        self.modules: List = []  # Список модулей системы
        
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

    def add_message(self, msg: BaseMessage, step_time: Optional[int] = None) -> None:
        """Добавление нового сообщения в список сообщений для указанного шага
        
        :param msg: Сообщение для добавления
        :param step_time: Время шага, на котором сообщение будет обработано (если None - текущее время + 1)
        """
        if step_time is None:
            step_time = self.time.get_time() + 1  # По умолчанию сообщение обрабатывается на следующем шаге
        
        if step_time not in self.messages:
            self.messages[step_time] = []
        
        self.messages[step_time].append(msg)
        # Сортировка сообщений по важности (если требуется)
        self.messages[step_time].sort(key=lambda x: -x.priority)

    def give_messages(self, step_time: Optional[int] = None) -> List[BaseMessage]:
        """Возвращает все сообщения для указанного шага (по умолчанию текущий шаг)
        
        :param step_time: Время шага, для которого нужно получить сообщения
        :return: Список сообщений для данного шага
        """
        if step_time is None:
            step_time = self.time.get_time()
        
        return self.messages.get(step_time, [])

    def give_messages_by_id(self, receiver_id: int, step_time: Optional[int] = None) -> List[BaseMessage]:
        """Возвращает сообщения для указанного получателя на заданном шаге
        
        :param receiver_id: ID модуля-получателя
        :param step_time: Время шага (если None - текущий шаг)
        :return: Список сообщений для данного получателя
        """
        if step_time is None:
            step_time = self.time.get_time()
        
        messages_at_step = self.messages.get(step_time, [])
        return [msg for msg in messages_at_step if msg.receiver_id == receiver_id]

    def give_messages_by_type(
        self,
        msg_type: MessageType,
        receiver_id: Optional[int] = None,
        step_time: Optional[int] = None
    ) -> List[BaseMessage]:
        """
        Возвращает сообщения указанного типа, опционально фильтруя по получателю
        
        :param msg_type: Класс сообщения (например, LaunchMissileMessage)
        :param receiver_id: Опциональный ID получателя (если None - не фильтровать по получателю)
        :param step_time: Время шага (если None - текущий шаг)
        :return: Список сообщений указанного типа
        """
        if step_time is None:
            step_time = self.time.get_time()
        
        messages_at_step = self.messages.get(step_time, [])
        
        result = []
        for msg in messages_at_step:
            if isinstance(msg, msg_type):
                if receiver_id is None or msg.receiver_id == receiver_id:
                    result.append(msg)
        
        return result

    def run_simulation(self, end_time: int) -> None:
        """Запуск симуляции на указанное количество времени
        
        :param end_time: время завершения симуляции
        """
        while self.time.get_time() < end_time:
            current_time = self.time.get_time()
            print(f"Текущее время: {current_time}")
            
            # Обработка сообщений для текущего шага (если есть)
            current_messages = self.give_messages(current_time)
            if current_messages:
                print(f"Обработка {len(current_messages)} сообщений на шаге {current_time}")
            
            # Запуск шага симуляции для каждого модуля
            for module in self.modules:
                module.step()
            
            # Обновление времени после обработки всех модулей
            self.time.update_time()