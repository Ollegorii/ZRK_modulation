import yaml
import numpy as np
from enum import Enum
from typing import Dict, List, Any, Tuple

from modules.Manager import Manager
from modules.AirEnv import AirEnv, Target, TargetType
from modules.CCP import CombatControlPoint
from modules.MissileLauncher import MissileLauncher, Missile
from modules.Radar import SectorRadar
from modules.Timer import Timer
from modules.BaseModel import BaseModel

def load_config(config_path: str) -> Dict[str, Any]:
    """Загрузка конфигурации из YAML файла"""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def create_objects_from_config(config: Dict[str, Any]) -> Tuple[Manager, Dict[int, object]]:
    """Создание объектов из конфигурации"""
    manager = Manager()
    objects_by_id = {}
    
    # Настройка таймера
    timer = Timer()
    timer.dt = config['simulation']['time_step']
    manager.time = timer

    # Создание воздушной обстановки
    air_env_config = config['air_environment']
    air_env = AirEnv(
        manager, 
        id=air_env_config['id'], 
        pos=np.array(air_env_config['position'])
    )
    
    # Добавление целей
    for target_config in air_env_config.get('targets', []):
        target_type = getattr(TargetType, target_config['type'])
        target = Target(target_type)
        target.pos = np.array(target_config['position'])
        target.velocity = np.array(target_config['velocity'])
        air_env.add_target(target)
    
    manager.add_module(air_env)
    objects_by_id[air_env_config['id']] = air_env
    
    # Создание пусковых установок с ракетами
    for ml_config in config.get('missile_launchers', []):
        ml = MissileLauncher(
            manager,
            id=ml_config['id'],
            pos=np.array(ml_config['position']),
            max_missiles=ml_config.get('max_missiles', 5)
        )
        
        # Добавление ракет
        for missile_config in ml_config.get('missiles', []):
            missile = Missile(
                dispatcher=manager,
                ID=missile_config['id'],
                vel=missile_config.get('velocity', 1000),
                life_time=missile_config.get('life_time', 60),
                expl_radius=missile_config.get('explosion_radius', 50)
            )
            ml.add_missile(missile)  # Используем метод add_missile вместо прямого доступа к списку
        
        manager.add_module(ml)
        objects_by_id[ml_config['id']] = ml
    
    # Создание радаров
    for radar_config in config.get('radars', []):
        radar = SectorRadar(
            pos=np.array(radar_config['position']),
            id=radar_config['id'],
            azimuth_start=radar_config['azimuth_start'],
            elevation_start=radar_config['elevation_start'],
            max_distance=radar_config['max_distance'],
            azimuth_range=radar_config['azimuth_range'],
            elevation_range=radar_config['elevation_range'],
            azimuth_speed=radar_config['azimuth_speed'],
            elevation_speed=radar_config['elevation_speed'],
            scan_mode=radar_config['scan_mode']
        )
        if isinstance(radar, BaseModel):
            manager.add_module(radar)
        objects_by_id[radar_config['id']] = radar
    
    # Создание пункта боевого управления
    ccp_config = config.get('combat_control_point', {})
    if ccp_config:
        missile_launcher_coords = {ml_id: objects_by_id[ml_id].pos 
                                 for ml_id in ccp_config.get('missile_launcher_ids', [])
                                 if ml_id in objects_by_id}
        
        radar_coords = {radar_id: objects_by_id[radar_id].position 
                       for radar_id in ccp_config.get('radar_ids', [])
                       if radar_id in objects_by_id}
        
        ccp = CombatControlPoint(
            manager, 
            id=ccp_config['id'],
            missile_launcher_coords=missile_launcher_coords,
            radars_coords=radar_coords
        )
        manager.add_module(ccp)
        objects_by_id[ccp_config['id']] = ccp
    
    return manager, objects_by_id

def run_simulation_from_config(config_path: str):
    """Запуск симуляции из конфиг-файла"""
    config = load_config(config_path)
    manager, objects = create_objects_from_config(config)
    
    print("Созданные объекты:")
    for obj_id, obj in objects.items():
        if isinstance(obj, MissileLauncher):
            print(f"Пусковая установка (ID: {obj_id}), ракет: {obj.get_missile_count()}")
        elif isinstance(obj, SectorRadar):
            print(f"Радар (ID: {obj_id}), режим: {obj.scan_mode}")
        elif isinstance(obj, CombatControlPoint):
            print(f"Пункт боевого управления (ID: {obj_id})")
        elif isinstance(obj, AirEnv):
            print(f"Воздушная обстановка (ID: {obj_id}), целей: ")
    
    simulation_time = config['simulation']['duration']
    print(f"\nЗапуск симуляции на {simulation_time} секунд...")
    manager.run_simulation(simulation_time)
    
    total_messages = sum(len(messages) for messages in manager.messages.values())
    print(f"\nИтого сообщений: {total_messages}")

if __name__ == "__main__":
    run_simulation_from_config('config.yaml')