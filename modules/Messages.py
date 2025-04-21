from .BaseMessage import BaseMessage
import numpy as np

from .Missile import Missile
from .constants import MessageType
from enum import Enum
from typing import List

from .BaseModel import BaseModel
from .AirObject import AirObject
from .utils import Target

class LaunchMissileMessage(BaseMessage):
    """
    MissileLauncher -> Missile
    Сообщение с командой на запуск ракеты по указанной цели
    """
    def __init__(self, sender_id: int, receiver_id: int = None, time: int = None):
        super().__init__(type=MessageType.LAUNCH_MISSILE, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
    
    def __repr__(self) -> str:
        return super().__repr__()

class CPPLaunchMissileRequestMessage(BaseMessage):
    """
    CCP -> MissileLauncher
    Сообщение на запуск ракеты по указанной цели
    """
    def __init__(self, sender_id: int, target_id: int, target_position: np.ndarray, radar_id: int, time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.LAUNCH_COMMAND, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.target_id = target_id
        self.target_position = target_position
        self.radar_id = radar_id
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        return f"{base_info}, target_id={self.target_id}, target_position={self.target_position}, radar_id={self.radar_id}"

class LaunchedMissileMessage(BaseMessage):
    """
    MissileLauncher -> CCP
    Сообщение об успешном запуске ракеты
    """
    def __init__(self, sender_id: int, missile: Missile, target_id: int, time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.LAUNCHED_MISSILE, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.missile = missile
        self.target_id = target_id
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        return f"{base_info}, missile.id={self.missile.id if self.missile else None}, target_id={self.target_id}"

class MissileCountRequestMessage(BaseMessage):
    """
    CCP -> MissileLauncher
    Сообщение-запрос количества доступных ракет
    """
    def __init__(self, sender_id: int, time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.MISSILE_COUNT_REQUEST, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
    
    def __repr__(self) -> str:
        return super().__repr__()

class MissileCountResponseMessage(BaseMessage):
    """
    MissileLauncher -> CCP
    Сообщение с количеством доступных ракет
    """
    def __init__(self, sender_id: int, count: int, time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.MISSILE_COUNT_RESPONSE, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.count = count
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        return f"{base_info}, count={self.count}"

class FoundObjectsMessage(BaseMessage):
    """
    Radar -> CCP
    Сообщение о найденных объектах радиолокатором
    """
    def __init__(self, sender_id: int, visible_objects: List[AirObject], time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.FOUND_OBJECTS, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.visible_objects = visible_objects
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        object_ids = [obj.id for obj in self.visible_objects] if self.visible_objects else []
        return f"{base_info}, visible_objects.ids={object_ids}, visible_objects.count={len(object_ids)}"

class CPPUpdateTargetRadarMessage(BaseMessage):
    """
    CCP -> Radar
    Сообщение на обновление координат цели
    """
    def __init__(self, sender_id: int, target: Target, missile_id: int, time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.CCP_UPDATE_TARGET, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.target = target
        self.missile_id = missile_id
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        return f"{base_info}, target.id={self.target.id if self.target else None}, missile_id={self.missile_id}"

class ActiveObjectsMessage(BaseMessage):
    """
    AirEnv -> Radar
    Сообщение об активных объектах
    """
    def __init__(self, sender_id: int, active_objects: List[AirObject], time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.ACTIVE_OBJECTS, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.active_objects = active_objects
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        object_ids = [obj.id for obj in self.active_objects] if self.active_objects else []
        return f"{base_info}, active_objects.ids={object_ids}, active_objects.count={len(object_ids)}"

class UpdateTargetPosition(BaseMessage):
    """
    Radar -> Missile
    Сообщение о новом положении цели
    """
    def __init__(self, sender_id: int, upd_object: Target, time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.UPDATE_TARGET, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.upd_object = upd_object
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        return f"{base_info}, upd_object.id={self.upd_object.id if self.upd_object else None}, upd_object.pos={self.upd_object.pos if self.upd_object else None}"

class DestroyedMissileId(BaseMessage):
    """
    Radar -> CCP
    Сообщение с id уничтноженной ракеты
    """
    def __init__(self, sender_id: int, missile_id: int, time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.DESTROYED_MISSILE, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.missile_id = missile_id
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        return f"{base_info}, missile_id={self.missile_id}"

class MissileDetonateMessage(BaseMessage):
    """
    ЗУР -> ВО, РЛС
    Сообщение о подрыве ЗУР
    """
    def __init__(self, sender_id: int, target_id: int = None):
        super().__init__(type=MessageType.MISSILE_DETONATE, sender_id=sender_id)
        self.missile_id = sender_id
        self.target_id = target_id
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        return f"{base_info}, missile_id={self.missile_id}, target_id={self.target_id}"

class MissilePosMessage(BaseMessage):
    """
    ЗУР -> ВО
    Сообщение о текущем положении ЗУР
    """
    def __init__(self, sender_id: int):
        super().__init__(type=MessageType.MISSILE_POS, sender_id=sender_id)
        self.missile_id = sender_id
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        return f"{base_info}, missile_id={self.missile_id}"

class CPPDrawerObjectsMessage(BaseMessage):
    """
    CCP -> GUI
    Сообщение на обновление координат цели
    """
    def __init__(self, sender_id: int, obj_id: int, type, coordinates: np.ndarray, time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.DRAW_OBJECTS, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.obj_id = obj_id
        self.type = type
        self.coordinates = coordinates
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        return f"{base_info}, obj_id={self.obj_id}, type={self.type}, coordinates={self.coordinates}"

class MissileToAirEnvMessage(BaseMessage):
    """
    MissileLauncher -> AirEnv
    Сообщение об успешном запуске ракеты
    """
    def __init__(self, sender_id: int, missile: Missile, time: int = None, receiver_id: int = None):
        super().__init__(type=MessageType.NEW_MISSILE, send_time=time, sender_id=sender_id, receiver_id=receiver_id)
        self.missile = missile
    
    def __repr__(self) -> str:
        base_info = super().__repr__()
        return f"{base_info}, missile.id={self.missile.id if self.missile else None}"