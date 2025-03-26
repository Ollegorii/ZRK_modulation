from Manager import Manager
from AirEnv import AirEnv, Target, TargetType
import numpy as np
from Timer import Timer

def test_simulation():
    # Создаем менеджер
    manager = Manager()
    
    # Настраиваем таймер
    timer = Timer()
    timer.dt = 0.5  # шаг в секундах
    
    # Создаем воздушную обстановку
    air_env = AirEnv(manager, id=1, pos=np.array([0.0, 0.0, 0.0]))
    
    # Добавляем различные цели
    # air_env.add_target(Target(TargetType.AIR_PLANE))
    # air_env.add_target(Target(TargetType.HELICOPTER))
    # air_env.add_target(Target(TargetType.ANOTHER))
    manager.add_module(air_env)
    manager.run_simulation(5)
    
    # Выводим итоговое количество сообщений
    print(f"\nИтого сообщений: {len(manager.give_messages())}")
    print(f"Сообщения для получателя с ID=0: {len(manager.give_messages_by_id(0))}")


if __name__ == "__main__":
    test_simulation()