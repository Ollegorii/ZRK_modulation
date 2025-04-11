import numpy as np
from typing import Optional, Tuple, Any
from .constants import *


class Missile:
    """
    Класс, представляющий управляемую ракету зенитно-ракетного комплекса.
    Моделирует движение, наведение и подрыв ракеты.
    """
    
    def __init__(self, 
                 dispatcher: Any, 
                 ID: int,
                 vel: float = GUIDED_MISSILE_SPEED,
                 life_time: float = GUIDED_MISSILE_LIFETIME,
                 expl_radius: float = GUIDED_MISSILE_EXPL_RADIUS) -> None:
        """
        Инициализация ракеты
        
        :param dispatcher: Диспетчер модели, обеспечивающий связь между компонентами
        :param ID: Уникальный идентификатор ракеты
        :param vel: Скорость полета ракеты в м/с
        :param life_time: Максимальное время жизни ракеты в секундах
        :param expl_radius: Радиус поражения при взрыве в метрах
        """
        self.id = ID
        self.dispatcher = dispatcher
        self.velocity = vel
        self.life_time = life_time
        self.expl_radius = expl_radius
        
        # Текущие параметры состояния
        self.pos = None  # Текущая позиция (будет установлена при запуске)
        self.target_pos = None  # Позиция цели для наведения
        self.launch_time = None  # Время запуска
        self.is_active = False  # Активна ли ракета
        self.is_launched = False  # Запущена ли ракета
        self.distance_traveled = 0.0  # Пройденное расстояние
        self.flight_time = 0.0  # Время полёта
        
        # Параметры наведения
        self.guidance_type = "proportional"  # Тип наведения: "proportional", "pursuit", "lead"
        self.target_id = None  # ID цели
        self.hit_probability = 0.9  # Вероятность попадания при подлете на расстояние поражения
        
        # Траектория полета
        self.trajectory = []  # Для сохранения истории полета
        
        print(f"Создана ракета ID: {self.id}, скорость: {self.velocity} м/с, "
              f"время жизни: {self.life_time} с, радиус поражения: {self.expl_radius} м")
    
    def launch(self, start_pos: np.ndarray, target_pos: np.ndarray, 
               target_id: Optional[int] = None, current_time: float = 0) -> bool:
        """
        Запуск ракеты
        
        :param start_pos: Начальная позиция ракеты (координаты пусковой установки)
        :param target_pos: Текущая позиция цели
        :param target_id: ID цели (если известно)
        :param current_time: Текущее время симуляции
        :return: Успешность запуска
        """
        if self.is_launched:
            print(f"Ракета {self.id} уже запущена")
            return False
        
        self.pos = np.array(start_pos, dtype=float)
        self.target_pos = np.array(target_pos, dtype=float)
        self.target_id = target_id
        self.launch_time = current_time
        self.is_launched = True
        self.is_active = True
        self.trajectory = [self.pos.copy()]
        
        # Вектор направления на цель
        direction = self.target_pos - self.pos
        self.direction_norm = direction / np.linalg.norm(direction)
        
        print(f"Ракета {self.id} запущена с позиции {self.pos} в направлении цели {self.target_pos}")
        return True
    
    def update(self, dt: float, current_time: float, new_target_pos: Optional[np.ndarray] = None) -> Tuple[bool, bool]:
        """
        Обновление состояния ракеты
        
        :param dt: Шаг времени
        :param current_time: Текущее время симуляции
        :param new_target_pos: Новая позиция цели (если есть обновленные данные)
        :return: Кортеж (hit, active): hit - произошло ли поражение цели, active - активна ли ракета
        """
        if not self.is_launched or not self.is_active:
            return False, False
        
        # Обновляем время полета
        self.flight_time = current_time - self.launch_time
        
        # Проверяем время жизни
        if self.flight_time >= self.life_time:
            print(f"Ракета {self.id} исчерпала время жизни")
            self.is_active = False
            return False, False
        
        # Обновляем позицию цели, если есть новые данные
        if new_target_pos is not None:
            self.target_pos = np.array(new_target_pos, dtype=float)
        
        # Вычисляем новое направление на цель (для систем наведения)
        if self.guidance_type in ["proportional", "lead"]:
            direction = self.target_pos - self.pos
            distance = np.linalg.norm(direction)
            
            # Если цель в радиусе поражения, считаем попадание
            if distance <= self.expl_radius:
                print(f"Ракета {self.id} достигла цели! Расстояние: {distance:.2f} м")
                self.is_active = False
                return True, False
            
            # Обновляем направление движения
            self.direction_norm = direction / distance
        
        # Вычисляем перемещение
        movement = self.direction_norm * self.velocity * dt
        self.pos += movement
        self.distance_traveled += np.linalg.norm(movement)
        
        # Сохраняем точку траектории
        self.trajectory.append(self.pos.copy())
        
        return False, True
    
    def detonate(self) -> bool:
        """
        Принудительный подрыв ракеты
        
        :return: Успешность подрыва
        """
        if not self.is_active:
            return False
        
        print(f"Ракета {self.id} подорвана принудительно")
        self.is_active = False
        return True
    
    def get_status(self) -> dict:
        """
        Получение текущего статуса ракеты
        
        :return: Словарь с параметрами состояния
        """
        return {
            "id": self.id,
            "active": self.is_active,
            "launched": self.is_launched,
            "position": self.pos.tolist() if self.pos is not None else None,
            "target_position": self.target_pos.tolist() if self.target_pos is not None else None,
            "flight_time": self.flight_time,
            "distance_traveled": self.distance_traveled,
            "remaining_lifetime": max(0, self.life_time - self.flight_time) if self.is_launched else self.life_time
        }
    
    def __str__(self) -> str:
        """
        Строковое представление ракеты
        
        :return: Информация о ракете в текстовом виде
        """
        status = "активна" if self.is_active else "неактивна"
        launched = "запущена" if self.is_launched else "не запущена"
        position = f"позиция: {self.pos}" if self.pos is not None else "не установлена позиция"
        return f"Ракета ID:{self.id}, {status}, {launched}, {position}"
