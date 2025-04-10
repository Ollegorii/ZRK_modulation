from .BaseMessage import BaseMessage
import numpy as np
from .constants import MessageType
from enum import Enum
from typing import List

from .BaseModel import BaseModel
from .AirObject import AirObject
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


class LaunchedMissileMessage(BaseMessage):
    """
    MissileLauncher -> CCP
    Сообщение об успешном запуске ракеты
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, missile_id: int):
        super().__init__(type=MessageType.LAUNCHED_MISSILE, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.missile_id = missile_id


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


class ActiveObjectsMessage(BaseMessage):
    """
    AirEnv -> Radar
    Сообщение об активных объектах
    """
    def __init__(self, time: int, sender_id: int, receiver_id: int, active_objects: List[Target]):
        super().__init__(type=MessageType.ACTIVE_OBJECTS, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.active_objects = active_objects
