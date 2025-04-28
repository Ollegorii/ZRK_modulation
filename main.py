import yaml
import numpy as np
from typing import Dict, List, Any, Tuple
import logging

from modules.Manager import Manager
from modules.AirEnv import AirEnv
from modules.Radar import SectorRadar
from modules.utils import Target, TargetType
from modules.AirObject import Trajectory
from modules.CCP import CombatControlPoint
from modules.MissileLauncher import MissileLauncher
from modules.Missile import Missile
from modules.Timer import Timer
from modules.BaseModel import BaseModel
from modules.constants import MessageType

# создаём логгер для данного модуля
logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        filename='logs/app.log',
        filemode='w',
        encoding='utf-8',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

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
        manager=manager,
        id=air_env_config['id'],
        pos=np.array(air_env_config['position'])
    )
    manager.add_module(air_env)
    objects_by_id[air_env_config['id']] = air_env

    # Создание радаров
    for radar_config in config.get('radars', []):
        radar = SectorRadar(
            manager=manager,
            id=radar_config['id'],
            pos=np.array(radar_config['position']),
            azimuth_start=radar_config['azimuth_start'],
            elevation_start=radar_config['elevation_start'],
            max_distance=radar_config['max_distance'],
            azimuth_range=radar_config['azimuth_range'],
            elevation_range=radar_config['elevation_range'],
            azimuth_speed=radar_config['azimuth_speed'],
            elevation_speed=radar_config['elevation_speed'],
            scan_mode=radar_config['scan_mode']
        )
        manager.add_module(radar)
        objects_by_id[radar_config['id']] = radar

    # Создание пусковых установок
    for ml_config in config.get('missile_launchers', []):
        ml = MissileLauncher(
            manager=manager,
            id=ml_config['id'],
            pos=np.array(ml_config['position']),
            max_missiles=ml_config.get('max_missiles', 5)
        )

        # Добавление ракет в пусковую установку
        for missile_config in ml_config.get('missiles', []):
            initial_traj = Trajectory(
                velocity=(0, 0, 0),
                start_pos=ml_config['position'],
                start_time=0.0
            )

            missile = Missile(
                manager=manager,
                id=missile_config['id'],
                pos=np.array(ml_config['position']),
                velocity_module=missile_config.get('velocity', 1000),
                detonate_radius=missile_config.get('explosion_radius', 50),
                detonate_period=missile_config.get('life_time', 60)
            )
            ml.add_missile(missile)

        manager.add_module(ml)
        objects_by_id[ml_config['id']] = ml

    # Создание пункта боевого управления
    ccp_config = config.get('combat_control_point', {})
    if ccp_config:
        missile_launcher_coords = {
            ml_id: objects_by_id[ml_id].pos
            for ml_id in ccp_config.get('missile_launcher_ids', [])
            if ml_id in objects_by_id
        }
        radars_coords = {
            radar_id: objects_by_id[radar_id].pos
            for radar_id in ccp_config.get('radar_ids', [])
            if radar_id in objects_by_id
        }

        ccp = CombatControlPoint(
            manager=manager,
            id=ccp_config['id'],
            position=np.array([0, 0, 0]),
            missile_launcher_coords=missile_launcher_coords,
            radars_coords=radars_coords
        )
        manager.add_module(ccp)
        objects_by_id[ccp_config['id']] = ccp

    # Добавление целей в воздушную обстановку
    for target_config in air_env_config.get('targets', []):
        target_type = getattr(TargetType, target_config['type'])
        target_id = target_config['id']
        pos = np.array(target_config['position'])
        velocity = np.array(target_config['velocity'])

        target_trajectory = Trajectory(
            velocity=velocity,
            start_pos=pos,
            start_time=0.0
        )

        target = Target(
            manager=manager,
            id=target_id,
            pos=pos,
            trajectory=target_trajectory,
            type=target_type
        )
        air_env.add_target(target)

    return manager, objects_by_id

def run_simulation_from_config(config_path: str):
    """Запуск симуляции из конфиг-файла"""
    config = load_config(config_path)
    manager, objects = create_objects_from_config(config)

    logger.info("Созданные объекты:")
    for obj_id, obj in objects.items():
        if isinstance(obj, MissileLauncher):
            logger.info(f"Пусковая установка (ID: {obj_id}), ракет: {obj.get_missile_count()}")
        elif isinstance(obj, SectorRadar):
            logger.info(f"Радар (ID: {obj_id}), режим: {obj.scan_mode}")
        elif isinstance(obj, CombatControlPoint):
            logger.info(f"Пункт боевого управления (ID: {obj_id})")
        elif isinstance(obj, AirEnv):
            logger.info(f"Воздушная обстановка (ID: {obj_id})")

    simulation_time = config['simulation']['duration']
    logger.info(f"Запуск симуляции на {simulation_time} секунд...")
    manager.run_simulation(simulation_time)

    total_messages = sum(len(messages) for messages in manager.messages.values())
    logger.info(f"Итого сообщений: {total_messages}")

    return manager

if __name__ == "__main__":
    setup_logging()
    run_simulation_from_config('config.yaml')
