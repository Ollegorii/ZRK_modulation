from .BaseMessage import BaseMessage
import numpy as np
from .constants import MessageType
from enum import Enum
from typing import List

from .AirEnv import Target


class LaunchStatus(Enum):
    LAUNCHED = "запущена"
    FAILED = "провал"


class LaunchMissileMessage(BaseMessage):
    """
    MissileLauncher -> Missile
    Сообщение с командой на запуск ракеты по указанной цели
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, status: LaunchStatus):
        super().__init__(type=MessageType.LAUNCH_MISSILE, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.status = status


class CPPLaunchMissileRequestMessage(BaseMessage):
    """
    CCP -> MissileLauncher
    Сообщение на запуск ракеты по указанной цели
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, target_id: int, target_position: int, radar_id: int):
        super().__init__(type=MessageType.LAUNCH_MISSILE, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.target_id = target_id
        self.target_position = target_position
        self.radar_id = radar_id


class LaunchedMissileMessage(BaseMessage):
    """
    MissileLauncher -> CCP
    Сообщение об успешном запуске ракеты
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, missile_id: int, target_id: int):
        super().__init__(type=MessageType.LAUNCHED_MISSILE, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.missile_id = missile_id
        self.target_id = target_id




class MissileCountRequestMessage(BaseMessage):
    """
    CCP -> MissileLauncher
    Сообщение-запрос количества доступных ракет
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int):
        super().__init__(type=MessageType.MISSILE_COUNT_REQUEST, time=time, sender_id=sender_id, receiver_id=receiver_id)


class MissileCountResponseMessage(BaseMessage):
    """
    MissileLauncher -> CCP
    Сообщение с количеством доступных ракет
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, count: int):
        super().__init__(type=MessageType.MISSILE_COUNT_RESPONSE, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.count = count


class FoundObjectsMessage(BaseMessage):
    """
    Radar -> CCP
    Сообщение о найденных объектах радиолокатором
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, visible_objects: List[np.ndarray]):
        super().__init__(type=MessageType.FOUND_OBJECTS, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.visible_objects = visible_objects

class CPPUpdateTargetRadarMessage(BaseMessage):
    """
    CCP -> Radar
    Сообщение на обновление координат цели
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, target: int, missile_id: int):
        super().__init__(type=MessageType.UPDATE_TARGET, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.target = target
        self.missile_id = missile_id


class ActiveObjectsMessage(BaseMessage):
    """
    AirEnv -> Radar
    Сообщение об активных объектах
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, active_objects: List[Target]):
        super().__init__(type=MessageType.ACTIVE_OBJECTS, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.active_objects = active_objects


class UpdateTargetPosition(BaseMessage):
    """
    Radar -> Missile
    Сообщение о новом положении цели
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, upd_object: Target):
        super().__init__(type=MessageType.UPDATE_TARGET, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.upd_object = upd_object


class DestroyedMissileId(BaseMessage):
    """
    Radar -> CCP
    Сообщение с id уничтноженной ракеты
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, missile_id: Target):
        super().__init__(type=MessageType.DESTROYED_MISSILE, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.missile_id = missile_id


class MissileDetonateMessage(BaseMessage):
    """
    ЗУР -> ВО, РЛС
    Сообщение о подрыве ЗУР
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, missile_id: int):
        super().__init__(type=MessageType.MISSILE_DETONATE, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.missile_id = missile_id

    def __repr__(self):
        return f"MissileDetonateMessage (time={self.time}, missile_id={self.missile_id})"


class MissilePosMessage(BaseMessage):
    """
    ЗУР -> ВО
    Сообщение о текущем положении ЗУР
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, missile_id: int):
        super().__init__(type=MessageType.MISSILE_POS, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.missile_id = missile_id

    def __repr__(self):
        return f"MissilePosMessage (time={self.time}, missile_id={self.missile_id})"
