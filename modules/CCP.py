import typing
import numpy as np
from modules.BaseModel import Manager
from modules.Messages import *
from modules.Missile import Missile
from modules.constants import *
import copy
import logging

OLD_TARGET = "старая цель"
NEW_TARGET = "новая цель"
OLD_ROCKET = "старая ЗУР"

logging.basicConfig(
    level=logging.DEBUG,
    filename='my_log.log',
    encoding='utf-8',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TargetCCP:
    """ Класс для хранения основных параметров сопровождаемых целей	"""

    def __init__(self, target: Target, time: int, following) -> None:
        """
        :param target: цель
        :param time: время, в которое произошло посл изменение класса
        """
        self.target = copy.deepcopy(target)
        self.upd_time = time
        self.following = following
        self.missile_id = None

    def upd_target_ccp(self, target: Target, time: int, upd_follow) -> None:
        """
        Функция для обновления координаты цели
        :param target: updated target
        :param time: время, когда вызвали функцию
        """
        self.target = copy.deepcopy(target)
        self.upd_time = time
        self.following = upd_follow

    def upd_missile_id(self, missile_id: int) -> None:
        self.missile_id = missile_id


class MissileCCP:
    """ Класс для хранения основных параметров запущенных ЗУР	"""

    def __init__(self, missile: Missile, time):
        """
        :param missile: ЗУР
        :param time: время, в которое произошло посл изменение класса
        """
        self.missile = copy.deepcopy(missile)
        self.upd_time = time
        # self.target = self.missile.target

    def upd_missile_ccp(self, missile: Missile, time: int) -> None:
        """
        Функция для обновления ЗУР
        :param missile: updated missile
        :param time: время, когда вызвали функцию
        """
        self.missile = copy.deepcopy(missile)
        # self.target = self.missile.target
        self.upd_time = time


class CombatControlPoint(BaseModel):
    """ Класс ПБУ	"""

    def __init__(self, manager: Manager, id: int, missile_launcher_coords: dict, radars_coords: dict,
                 position: np.ndarray):
        """
        :param manager: менеджер моделей.
        :param id: id объекта моделирования.
        :param missile_launcher_coords координаты пусковых установок.
        :param radars_coords: словарь с координатами всех МФР.
        """
        super().__init__(manager, id, position)
        self._target_dict = {}  # Отслеживаемые цели за которыми летит ЗУР
        self._missile_dict = {}  # Отслеживаемые ЗУР
        self.radars_coords = radars_coords  # координаты МФР
        self.missile_launcher_coords = missile_launcher_coords  # координаты ПУ
        self.missile_launcher_launched = {}
        self.missile_launcher_capacity = {}

        self.initialized = False

    def add_target(self, target_ccp: TargetCCP):
        """
        Добавление новой цели в список целей ПБУ
        """
        self._target_dict[target_ccp.target.id] = target_ccp
        logger.info(f"В ПБУ добавлена цель с id: {target_ccp.target.id}")

    def delete_target(self, target_id):
        """
        :param target_id: id цели
        """
        self._target_dict.pop(target_id, None)
        logger.info(f"В ПБУ удалена цель с id: {target_id}")

    def add_missile(self, missile_ccp: MissileCCP):
        """
        Добавление новой ЗУР в список ракет ПБУ
        """
        self._missile_dict[missile_ccp.missile.id] = missile_ccp
        self._target_dict[missile_ccp.missile.target.id].upd_missile_id(missile_ccp.missile.id)
        logger.info(f"В ПБУ добавлена ракета с id: {missile_ccp.missile.id}")

    def delete_missile(self, missile_id: int):
        """
        :param missile_id: id ракеты
        """
        target_id = self._missile_dict[missile_id].missile.target.id
        self._missile_dict.pop(missile_id, None)
        self.delete_target(target_id)
        logger.info(f"В ПБУ удалена ракета с id: {missile_id}")

    def send_request_msg_to_ML_capacity(self):
        """
        ПБУ запрашивает у ПУ количество ЗУР
        """
        for key in self.missile_launcher_coords.keys():
            self.missile_launcher_capacity[key] = 0
            self.missile_launcher_launched[key] = 0

            req_count_msg = MissileCountRequestMessage(
                time=self._manager.time.get_time(),
                sender_id=self.id,
                receiver_id=key
            )

            self._manager.add_message(req_count_msg)  # ПБУ запрашивает у ПУ количество ЗУР
            logger.info(f"ПБУ запрашивает у ПУ с id {key} количество ЗУР")

    def get_current_missile_launcher_capacity(self):
        """
        ПБУ получает от ПУ сообщения о кол-ве ЗУР
        """
        msg_missile_capacity = self._manager.give_messages_by_type(MessageType.MISSILE_COUNT_RESPONSE)
        if len(msg_missile_capacity) > 0:
            for msg in msg_missile_capacity:
                self.missile_launcher_capacity[msg.sender_id] = msg.count
                logger.info(f"ПБУ получил от ПУ {msg.sender_id} сообщение о том, что у него в наличии {msg.count} ЗУР")

    def check_if_missile_get_hit(self):
        """
        ПБУ получает сообщения от МФР об уничтожении ЗУР
        """
        msg_hit_missiles = self._manager.give_messages_by_type(MessageType.DESTROYED_MISSILE)

        if len(msg_hit_missiles) != 0:
            logger.info(f"ПБУ получил сообщения от МФР об уничтожении ЗУР")
            for msg in msg_hit_missiles:
                self.delete_missile(msg.missile_id)

    def check_if_missiles_launched(self):
        """
        ПБУ получает от ПУ сообщения о запуске ЗУР
        """
        msg_launched_missiles = self._manager.give_messages_by_type(MessageType.LAUNCHED_MISSILE)
        if len(msg_launched_missiles) > 0:
            for msg in msg_launched_missiles:
                logger.info(f"ПБУ получил от ПУ запуске ЗУР c id:{msg.missile.id}")
                self.add_missile(MissileCCP(msg.missile, self._manager.time.get_time()))

    def link_object(self, detected_object):
        """
        ПБУ соотносит объекты
        """

        def calc_range(detected_obj, obj_to_link_pos, obj_to_link_upd_time):
            """ Метода расчета min/max расстояния до возможного объекта"""


            velocity = detected_obj.speed_mod
            if detected_obj.id == 10:
                velocity = 1600
            cur_time = self._manager.time.get_time()
            coord_diff = np.linalg.norm(obj_to_link_pos - detected_obj.pos)
            d_t = cur_time - obj_to_link_upd_time
            print(f'{[cur_time]}, {velocity}, {d_t}, {obj_to_link_pos}, {detected_obj.pos}, {coord_diff}')

            return max(0, velocity * (d_t - POSSIBLE_TARGET_RADIUS * SIMULATION_STEP)), max(0, velocity * (
                    d_t + POSSIBLE_TARGET_RADIUS * SIMULATION_STEP)), coord_diff

        curr_diff = float('inf')
        matched_object_id = None
        classification = NEW_TARGET
        print(f'PBU see {detected_object.pos}')

        # Проверка на старую цель
        for target_id, target_ccp in self._target_dict.items():
            print(f'{[self._manager.time.get_time()]}, {target_id}, {target_ccp.upd_time}, {target_ccp.target}')
            if target_ccp.upd_time == self._manager.time.get_time():
                continue

            min_range, max_range, pos_diff = calc_range(detected_object, target_ccp.target.pos, target_ccp.upd_time)

            if pos_diff < curr_diff and min_range <= pos_diff <= max_range:
                curr_diff = pos_diff
                classification = OLD_TARGET
                matched_object_id = target_id

        # Проверка на старую ЗУР
        print([self._manager.time.get_time()], len(self._missile_dict))
        for missile_id, missile_ccp in self._missile_dict.items():
            print(f'{[self._manager.time.get_time()]}, {missile_id}, {missile_ccp.upd_time}')
            if missile_ccp.upd_time == self._manager.time.get_time():
                continue

            min_range, max_range, pos_diff = calc_range(detected_object, missile_ccp.missile.target.pos,
                                                        missile_ccp.upd_time)
            print(min_range, max_range, pos_diff, curr_diff)
            if pos_diff < curr_diff and min_range <= pos_diff <= max_range:
                curr_diff = pos_diff
                classification = OLD_ROCKET
                matched_object_id = missile_id
        return classification, matched_object_id

    def send_update_msg_to_radar(self, target, missile_id, radar_id):
        """
        ПБУ отправляет сообщение на обновление координат цели
        """

        msg2radar = CPPUpdateTargetRadarMessage(
            time=self._manager.time.get_time(),
            sender_id=self.id,
            receiver_id=radar_id,
            target=target,
            missile_id=missile_id
        )
        self._manager.add_message(msg2radar)
        logger.info(
            f"ПБУ сообщает МФР {radar_id}, что у ЗУР с id:{missile_id}, новые координаты ее цели:{target.pos()}")

    def send_objects_to_GUI(self):
        """
        ПБУ отправляет сообщение на отрисовку в GUI
        """
        for key, missile in self._missile_dict.items():
            obj_id = self._missile_dict[key].missile.id
            msg2drawer = CPPDrawerObjectsMessage(
                time=self._manager.time.get_time(),
                sender_id=self.id,
                receiver_id=MANAGER_ID,
                obj_id=obj_id,
                target_type='ЗУР',
                coordinates=self._missile_dict[key].missile.pos
            )
            self._manager.add_message(msg2drawer)
            logger.info(f"ПБУ отправил {'ЗУР', obj_id} на отрисовку GUI")

        for key, target in self._target_dict.items():
            obj_id = self._target_dict[key].target.id
            obj_type = self._target_dict[key].target.type
            msg2drawer = CPPDrawerObjectsMessage(
                time=self._manager.time.get_time(),
                sender_id=self.id,
                receiver_id=MANAGER_ID,
                obj_id=obj_id,
                target_type=obj_type,
                coordinates=self._target_dict[key].target.pos
            )
            self._manager.add_message(msg2drawer)
            logger.info(f"ПБУ отправил {obj_type, obj_id} на отрисовку GUI")

    def try_to_launch_missile(self, obj, radar_id):
        """
        Проверка есть ли ЗУР для цели, и запуск, если есть
        """
        min_dist = float('inf')
        curr_ml_id = None
        # ищем ближайший ПУ со свободными ЗУР
        for ml_id in self.missile_launcher_coords.keys():
            if self.missile_launcher_launched[ml_id] < self.missile_launcher_capacity[ml_id]:
                sd_pos = self.missile_launcher_coords[ml_id]
                dist = (np.sum((sd_pos - obj.pos) ** 2)) ** 0.5
                if dist < min_dist:
                    curr_ml_id = ml_id
                    min_dist = dist

        if curr_ml_id is not None:
            self.missile_launcher_launched[curr_ml_id] = self.missile_launcher_launched[curr_ml_id] + 1

            # Говорим пу запустить ЗУР по цели с координатами
            launch_msg = CPPLaunchMissileRequestMessage(
                time=self._manager.time.get_time(),
                sender_id=self.id,
                receiver_id=curr_ml_id,
                target=obj,
                target_position=obj.pos,
                radar_id=radar_id
            )
            self._manager.add_message(launch_msg)
            logger.info(
                f"ПБУ отправляет сообщение ПУ с id {curr_ml_id} на запуск ЗУР по цели с координатами:{obj.pos}")
            return True
        else:
            logger.info(f"У ПУ для неё нет свободных ЗУР")
            return False

    def new_target(self, obj, radar_id):
        """
        Обработка случая, когда видимый объект является новой целью
        """
        logger.info("ПБУ определил этот объект как новую цель")
        if self.try_to_launch_missile(obj, radar_id):
            self.add_target(TargetCCP(obj, self._manager.time.get_time(), True))
        else:
            self.add_target(TargetCCP(obj, self._manager.time.get_time(), False))

    def old_target(self, obj, old_obj_id, radar_id):
        """
        Обработка случая, когда видимый объект является старой целью
        """
        logger.info("ПБУ определил этот объект как старую цель")
        is_following = self._target_dict[old_obj_id].following

        if not is_following:
            logger.info("Цель не преследуется ЗУР, пробуем запустить ЗУР по ней")
            if self.try_to_launch_missile(obj, radar_id):
                self._target_dict[old_obj_id].upd_target_ccp(obj, self._manager.time.get_time(), True)
            else:
                self._target_dict[old_obj_id].upd_target_ccp(obj, self._manager.time.get_time(), False)

        else:
            logger.info("Цель уже преследуется ЗУР, обновляем её и перенаправляем ЗУР")
            self._target_dict[old_obj_id].upd_target_ccp(obj, self._manager.time.get_time(), is_following)
            curr_missile_id = self._target_dict[old_obj_id].missile_id
            msg2radar = CPPUpdateTargetRadarMessage(
                time=self._manager.time.get_time(),
                sender_id=self.id,
                receiver_id=radar_id,
                target=obj,
                missile_id=curr_missile_id,
            )
            self._manager.add_message(msg2radar)
            logger.info(
                f"ПБУ сообщает МФР {radar_id}, что у ЗУР с id:{curr_missile_id}, новые координаты ее цели:{obj.pos}")

    def old_rocket(self, obj, old_obj_id):
        """
        Обработка случая, когда видимый объект является старой ЗУР
        """
        logger.info(f"ПБУ определил этот объект как старую ЗУР с id:{self._missile_dict[old_obj_id].missile.id}")
        self._missile_dict[old_obj_id].upd_missile_ccp(obj, self._manager.time.get_time())

    def step(self) -> None:
        """
        Запуск моделирования

        1. Запрашивает у ПУ количество доступных ЗУР
        2. Проверяет есть ли сообщения от радара о том, что перестала существовать ЗУР
        3. Просматривает сообщение от ПУ о запуске ЗУР (добавляет к себе ракету и её цель в словарь)
        4. Просматривает сообщения от Радара в которых передается обнаруженные обьекты
        5. Разделение обьектов на старые/новые цели, ЗУР
          ЗУР - обновить координаты у себя в словаре
          Старая цель - обновить координаты у себя в словаре и перенаправить ЗУР
          Новая цель - добавить её в словарь и дать команду ПУ на запуск ЗУР по ней
        6. Отправить данные UI на отрисовку
        """
        if not self.initialized:
            self.send_request_msg_to_ML_capacity()
            self.initialized = True

        self.get_current_missile_launcher_capacity()
        self.check_if_missile_get_hit()
        self.check_if_missiles_launched()

        msg_from_radar = self._manager.give_messages_by_type(MessageType.FOUND_OBJECTS)
        logger.info(f"ПБУ получил сообщения от {len(msg_from_radar)} радаров/радара")

        if len(msg_from_radar) != 0:
            for msg in msg_from_radar:
                radar_id = msg.sender_id

                objects = msg.visible_objects
                for obj in objects:
                    logger.info(f"ПБУ получил {obj} от МФР с id {msg.sender_id}")
                    # Завязываем трассу (определяем что это за объект)
                    obj_type, old_obj_id = self.link_object(obj)
                    if obj_type == NEW_TARGET:
                        self.new_target(obj, radar_id)
                    elif obj_type == OLD_TARGET:
                        self.old_target(obj, old_obj_id, radar_id)
                    elif obj_type == OLD_ROCKET:
                        self.old_rocket(obj, old_obj_id)

        self.send_objects_to_GUI()
