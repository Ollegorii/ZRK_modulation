from .BaseMessage import BaseMessage
import numpy as np
from .constants import MessageType
from enum import Enum
from typing import List

from .BaseModel import BaseModel
from .AirObject import AirObject


class LaunchStatus(Enum):
    LAUNCHED = "запущена"
    FAILED = "провал"
    

class LaunchMissileMessage(BaseMessage):
    """Сообщение с командой на запуск ракеты по указанной цели"""
    def __init__(self, time: int, sender_id: int, receiver_id: int, status: LaunchStatus):
        super().__init__(type=MessageType.LAUNCH_MISSILE, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.status = status


class LaunchedMissileMessage(BaseMessage):
    """Сообщение об успешном запуске ракеты"""
    def __init__(self, time: int, sender_id: int, receiver_id: int, missile_id: int):
        super().__init__(type=MessageType.LAUNCHED_MISSILE, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.missile_id = missile_id


class FoundObjectsMessage(BaseMessage):
    '''Сообщение о найденных объектах радиолокатором'''
    def __init__(self, time: int, sender_id: int, receiver_id: int, visible_objects: List[np.array]):
        super().__init__(type=MessageType.FOUND_OBJECTS, time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.visible_objects = visible_objects