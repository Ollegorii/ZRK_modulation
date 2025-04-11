import typing
import numpy as np
from modules.BaseModel import BaseModel, Manager
from modules.AirEnv import TargetType
from modules.Messages import *

OLD_TARGET = "старая цель"
NEW_TARGET = "новая цель"
OLD_ROCKET = "старая ЗУР"


# Возможно наследование от какого-то базового класса типа BaseUnit/Unit/Movable
class TargetCCP:
    """ Класс для хранения основных параметров сопровождаемых целей	"""

    def __init__(self, type: TargetType, coord: np.array, speed: np.array, upd_time: float) -> None:
        """
        :param type: тип цели
        :param coord: координаты цели
        :param speed: скорость цели
        :param upd_time: время, в которое произошло посл изменение класса
        """
        self.type = type
        self.coord = coord
        self.speed = speed
        self.upd_time = upd_time
        self.seen_time = -1

    def upd_сoord(self, new_coord: float, time: float) -> None:
        """
        Функция для обновления координаты цели
        :param new_coord: новая координата цели
        :param time: время, когда вызвали функцию
        """
        self.coord = new_coord
        self.upd_time = time


# Возможно наследование от какого-то базового класса типа BaseUnit/Unit/Movable
class RocketCCP:
    """ Класс для хранения основных параметров запущенных ЗУР	"""

    def __init__(self, coord: np.array, speed: np.array, id: int, target: TargetCCP, time):
        """
        :param coord: текущие координаты ЗУР
        :param id: id ЗУР
        :param target: цель
        :param time: время, в которое произошло посл изменение класса
        """
        self.coord = coord
        self.speed = speed
        self.target = target
        self.id = id
        self.upd_time = time
        self.seen_time = -1

    def upd_сoord(self, new_coord: float, time: float) -> None:
        """
        Функция для обновления координаты ЗУР
        :param new_coord: новая координата ЗУР
        :param time: время, когда вызвали функцию
        """
        self.coord = new_coord
        self.upd_time = time

# TODO fix adding targert/missile
# Возможно наследование от какого-то класса базовых модулей
class CombatControlPoint(BaseModel):
    """ Класс ПБУ	"""

    def __init__(self, manager: Manager, id: int, missile_launcher_coords: dict, radars_coords: dict, position: np.ndarray):
        """
        :param manager: менеджер моделей
        :param id: id объекта моделирования
        :param radars_coords: словарь с координатами всех МФР
        """
        super().__init__(manager, id, position)
        self._target_dict = {}  # Отслеживаемые цели
        self._next_target_id = 0
        self._missile_dict = {}  # Отслеживаемые ЗУР
        self._next_missile_id = 0
        self.radars_coords = radars_coords  # координаты МФР
        self.missile_launcher_coords = missile_launcher_coords  # координаты ПУ
        self.missile_launcher_launched = {}
        self.missile_launcher_capacity = {}

        self.zaglushka = ["zaglushka"]
        self.initialized = False
        self.possible_target_radius = 100

    def get_Radar_info(self, visible_object: list, cur_time: float):
        """
        Получение сообщения об обнаружении цели от Radar и последующее её сопровождение
        """
        pass

    def add_target(self, target: TargetCCP):
        """
        Добавление новой цели в список целей ПБУ
        """
        self._target_dict[self._next_target_id] = target
        print(f"В ПБУ добавлена цель с id: {self._next_target_id}")
        self._next_target_id += 1

    def delete_target(self, target_id):
        """
        :param target_id: id цели
        """
        self._target_dict.pop(target_id, None)
        print(f"В ПБУ удалена цель с id: {target_id}")

    def get_PU_info(self):
        """
        Получение сообщений от ПУ и соотв. реакция на них
        """
        pass

    def add_rocket(self, rocket: RocketCCP):
        """
        Добавление новой ЗУР в список ракет ПБУ
        """
        self._missile_dict[self._next_missile_id] = rocket
        print(f"В ПБУ добавлена ракета с id: {self._next_missile_id}")
        self._next_missile_id += 1

    def delete_rocket(self, rocket_id: int):
        """
        :param rocket_id: id ракеты
        """
        self._missile_dict.pop(rocket_id, None)
        print(f"В ПБУ удалена ракета с id: {rocket_id}")

    def send_msg_to(self):
        """
        Методы общения с другими модулями путем сообщений
        """
        pass


    def send_request_msg_to_ML_capacity(self, time):
        for key in self.missile_launcher_coords.keys():
            self.missile_launcher_capacity[key] = 0
            self.missile_launcher_launched[key] = 0

            req_count_msg = MissileCountRequestMessage(
                time=time,
                sender_id=self.id,
                receiver_id=key
            )

            self._manager.add_message(req_count_msg)  # ПБУ запрашивает у ПУ количество ЗУР
            print(f"ПБУ запрашивает у ПУ с id {key} количество ЗУР")

    def get_current_missile_launcher_capacity(self):
        msg_missile_capacity = self._manager.give_messages_by_type(MessageType.MISSILE_COUNT_RESPONSE)
        if len(msg_missile_capacity) > 0:
            print(f"ПБУ получил от ПУ {len(msg_missile_capacity)} сообщений о кол-ве ЗУР")

            for msg in msg_missile_capacity:
                self.missile_launcher_capacity[msg.sender_id] = msg.count
                print(f"ПБУ получил от ПУ {msg.sender_id} сообщений о {msg.count} ЗУР")

    def check_if_missile_get_hit(self):
        msg_hit_missiles = self._manager.give_messages_by_type(MessageType.MISSILE_GET_HIT) # remember Oleg

        if len(msg_hit_missiles) != 0:
            print(f"ПБУ получил сообщения от МФР об уничтожении ЗУР")

            for msg in msg_hit_missiles:
                self.delete_rocket(msg.missile_id)

    def check_if_missiles_launched(self, time):
        msg_launched_missiles = self._manager.give_messages_by_type(MessageType.LAUNCHED_MISSILE)
        print(f"ПБУ получил от ПУ {len(msg_launched_missiles)} сообщений о запуске ЗУР")
        if len(msg_launched_missiles) > 0:
            if not isinstance(msg_launched_missiles, list):
                msg_launched_missiles = [msg_launched_missiles]

            # Соотносим id ЗУР, координаты ЗУР и координаты их целей
            for msg in msg_launched_missiles:
                target_key = msg.order
                # print(f"{target_key}, {len(self._target_dict.items())}")

                target_coord = self._target_dict[target_key].coord
                target_speed = self._target_dict[target_key].speed_mod
                target_vel = self._target_dict[target_key].speed_dir

                missile_id = msg.missile_id
                ML_id = msg.sender_id
                missile_coord = self.missile_launcher_coords[ML_id]

                self._next_missile_id = self._next_missile_id + 1
                # TODO init RocketCCP
                self._missile_dict[self._next_missile_id] = RocketCCP(missile_coord, missile_id,
                                                                      target_coord, target_vel, target_speed, time)
                print(f"ПБУ получил от ПУ id ЗУР:{missile_id}, начальные координаты ЗУР:{missile_coord}")

    def link_object(self, detected_object, time):
        simulation_step = self._simulating_tick
        curr_diff = float('inf')
        matched_object_id = None
        classification = NEW_TARGET

        obj_pos = detected_object[0]
        pos_error = abs(detected_object[-1])

        # Проверка на старую цель
        for target_id, target in self._target_dict.items():
            if target.last_detection_time == time:
                continue

            target_position = target.coord
            target_velocity = target.speed_mod
            last_update_time = target.upd_time

            position_diff = np.linalg.norm(target_position - obj_pos)
            d_t = time - last_update_time

            min_range = max(0, target_velocity * (d_t - self.possible_target_radius * simulation_step) - pos_error)
            max_range = max(0, target_velocity * (d_t + self.possible_target_radius * simulation_step) + pos_error)

            if (position_diff < curr_diff and min_range <= position_diff <= max_range):
                curr_diff = position_diff
                classification = OLD_TARGET
                matched_object_id = target_id

        # Проверка на старую ЗУР
        for missile_id, missile in self._missile_dict.items():
            if missile.last_detection_time == time:
                continue

            missile_position = missile.coord
            missile_speed = missile.speed_mod
            last_update_time = missile.upd_time

            position_diff = np.linalg.norm(missile_position - obj_pos)
            d_t = time - last_update_time

            min_range = max(0, missile_speed * (d_t - self.possible_target_radius * simulation_step) - pos_error)
            max_range = max(0, missile_speed * (d_t + self.possible_target_radius * simulation_step) + pos_error)

            if (position_diff < curr_diff and
                    min_range <= position_diff <= max_range):
                curr_diff = position_diff
                classification = OLD_ROCKET
                matched_object_id = missile_id

        if classification == OLD_ROCKET:
            self._missile_dict[matched_object_id].updSeenTime(time)
        elif classification == OLD_TARGET:
            self._target_dict[matched_object_id].updSeenTime(time)

        return classification, matched_object_id

    def send_new_target_coords_to_gm_through_MFR(self, gm_new_target_coords, time):
        for missile_id in gm_new_target_coords.keys():
            _, MFR_id, target_coord, target_vel = gm_new_target_coords[missile_id]

            # msg2radar = CombatControl2RadarMsg(time, self._ID, MFR_id, target_coord, target_vel, missile_id)
            # self._sendMessage(msg2radar)
            print(f"ПБУ сообщает МФР {MFR_id}, что у ЗУР с id:{missile_id}, новые координаты ее цели:{target_coord}")

    def send_objects_to_GUI(self, time):
        obj_coords = []
        for key, missile in self._missile_dict.items():
            obj_coords.append([MISSILE_TYPE_DRAWER, missile.coord])

        for key, target in self._target_dict.items():
            obj_coords.append([TARGET_TYPE_DRAWER, target.coord])

        # msg2drawer = CombatControl2DrawerMsg(
        #     time=time,
        #     sender_ID=self._ID,
        #     receiver_ID=DRAWER_ID,
        #     coordinates=obj_coords,
        # )
        # self._sendMessage(msg2drawer)
        print(f"ПБУ отправил {len(obj_coords)} объект(-ов/-а) на отрисовку GUI")

    def simulate(self, time: float) -> None:
        """
        Запуск моделирования
        :param time: текущее время

        1. Проверяет есть ли сообщения от радара о том, что перестала существовать ЗУР
        2. Запрашивает у ПУ количество доступных ЗУР
        3. Просматривает сообщение от ПУ о запуске ЗУР (добавляет к себе ракету и её цель в словарь)
        4. Просматривает сообщения от Радара в которых передается обнаруженные обьекты
        5. Разделение обьектов на старые/новые цели, ЗУР
          ЗУР - обновить координаты у себя в словаре
          Старая цель - обновить координаты у себя в словаре и перенаправить ЗУР
          Новая цель - добавить её в словарь и дать команду ПУ на запуска ЗУР по ней
        6. Отправить данные UI на отрисовку
        
        """
        if not self.initialized:
            # init_msg = CCP_InitMessage(time=time, sender_ID=self._ID, receiver_ID=MANAGER_ID)
            # self._sendMessage(init_msg)

            self.send_request_msg_to_ML_capacity(time)
            self.initialized = True


        self.get_current_missile_launcher_capacity()
        self.check_if_missile_get_hit()
        self.check_if_missiles_launched(time)

        msg_from_MFR = self.zaglushka
        print(f"ПБУ получил сообщения от {len(msg_from_MFR)} МФР")

        # TODO разнести на два разных сообщениея МФР и ПУ
        gm_new_target_coords = {}

        if len(msg_from_MFR) != 0:
            for ml_id in self._missile_dict.keys():
                self._missile_dict[ml_id].updSeenTime(-1)
            for ml_id in self._target_dict.keys():
                self._target_dict[ml_id].updSeenTime(-1)

            # отделить новые цели от всего что было раньше
            for msg in msg_from_MFR:
                print(
                    f"ПБУ получил {len(msg.visible_objects)}, {msg.visible_objects} сообщений от МФР с id {msg.sender_ID}")
                MFR_id = msg.sender_ID

                objects = msg.visible_objects
                for obj in objects:
                    obj_coord = obj[0]
                    obj_speed_direct = obj[1]
                    obj_speed_mod = obj[2]

                    # Завязываем трассу (определяем что это за объект) тут бы тоже мб разнести случаи
                    obj_type, old_obj_id = self.link_object(obj, time)
                    if obj_type == NEW_TARGET:
                        min_dist = float('inf')
                        curr_ml_id = None
                        for ml_id in self.missile_launcher_coords.keys():
                            if self.missile_launcher_launched[ml_id] < self.missile_launcher_capacity[ml_id]:
                                sd_pos = self.missile_launcher_coords[ml_id]
                                dist = (np.sum((sd_pos - obj_coord) ** 2)) ** 0.5
                                if dist < min_dist:
                                    curr_ml_id = ml_id
                                    min_dist = dist

                        if min_dist < GuidedMissile_SPEED_MIN * GuidedMissile_LifeTime:

                            if curr_ml_id is not None:
                                self.missile_launcher_launched[ml_id] = self.missile_launcher_launched[ml_id] + 1
                                self._next_target_id = self._next_target_id + 1
                                # TODO init TargetCCP
                                self._target_dict[self._next_target_id] = TargetCCP(obj_coord, obj_speed_direct,
                                                                                    obj_speed_mod, time)

                                # Говорим пбу запустить ЗУР по цели с координатами
                                # msg2StartingDevice = CombatControl2StartingDeviceMsg(time, self._ID, curr_ml_id,
                                #                                                      self._next_target_id, obj_coord, MFR_id)
                                # self._sendMessage(msg2StartingDevice)
                                print(
                                    f"ПБУ отправляет сообщение ПУ с id {curr_ml_id} на запуск ЗУР по цели с координатами:{obj_coord}")

                            else:
                                print(f"У ПУ больше нет ЗУР!!!")

                        else:
                            print(f"ЗУР не успеет долететь до цели")


                    elif obj_type == OLD_TARGET:
                        old_target_coord = self._target_dict[old_obj_id].coord

                        ###################### TODO ######################
                        # мб отдельный метод для обновления таргета и аналогичный для ЗУР, комплексный
                        # self._target_dict[old_obj_id].upd_coord(obj_coord, time)
                        # self._target_dict[old_obj_id].upd_speed_mod(obj_speed_mod, time)
                        ###################### TODO ######################

                        for key in self._missile_dict.keys():
                            missile = self._missile_dict[ml_id]
                            # если этот старый таргет был таргетом у этого ЗУР, то ЗУР надо  перенаправить
                            if (missile.target_coord == old_target_coord).all():
                                ###################### TODO ######################
                                # мб отдельный метод для обновления таргета и аналогичный для ЗУР, комплексный
                                # self._missile_dict[key].upd_target_coord(obj_coord)
                                # self._missile_dict[key].upd_target_vel(obj_speed_direct)
                                ###################### TODO ######################

                                missile_id = self._missile_dict[key].id
                                missile_coord = self._missile_dict[key].coord
                                target_vel = self._missile_dict[key].target_vel
                                target_coord = self._missile_dict[key].target_coord

                                # зачем вообще вся эта тема с расстоянием до МФР, если я и так ID передаю
                                MFR_missile_dist = np.linalg.norm(self.radars_coords[MFR_id] - missile_coord)

                                # разве оно может быть больше, если МФР зафиксировал её
                                if MFR_missile_dist < MAX_DIST_DETECTION:
                                    if missile_id in gm_new_target_coords.keys():
                                        old_MFR_missile_dist = gm_new_target_coords[missile_id][0]
                                        if MFR_missile_dist < old_MFR_missile_dist:  # why only  this case? # оставляем лучшее измерение?
                                            gm_new_target_coords[missile_id] = [MFR_missile_dist, MFR_id,
                                                                                target_coord, target_vel]
                                            print(
                                                f"инфу о ЗУР с id {missile_id} ПБУ передал Радару с id {MFR_id}, расст от него до ЗУР = {MFR_missile_dist}")

                                    else:
                                        gm_new_target_coords[missile_id] = [MFR_missile_dist, MFR_id, target_coord,
                                                                            target_vel]
                                        print(
                                            f"инфу о ЗУР с id {missile_id} ПБУ передал Радару с id {MFR_id}, расст от него до ЗУР = {MFR_missile_dist}")

                                break

                    elif obj_type == OLD_ROCKET:
                        ###################### TODO ######################
                        # self._missile_dict[old_obj_id].upd_coord(obj_coord, time)
                        # self._missile_dict[old_obj_id].upd_speed_mod(obj_speed_mod, time)
                        ###################### TODO ######################
                        print(
                            f"ПБУ увидел старую ЗУР с id:{self._missile_dict[old_obj_id].id}, новые координаты:{obj_coord}")

        self.send_new_target_coords_to_gm_through_MFR(gm_new_target_coords, time)
        self.send_objects_to_GUI(time)
