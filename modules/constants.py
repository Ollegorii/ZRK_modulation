from enum import Enum

class MessageType(Enum):
    LAUNCH_MISSILE = "launch_missile"
    LAUNCHED_MISSILE = "launched_missile"
    MISSILE_COUNT_REQUEST = "missile_count_request"
    MISSILE_COUNT_RESPONSE = "missile_count_response"
    FOUND_OBJECTS = "found_objects"
    ACTIVE_OBJECTS = "active_objects"
    UPDATE_TARGET = 'upd_target'
    MISSILE_GET_HIT = 'missile_get_hit'

GUIDED_MISSILE_SPEED = 1000  # м/с
GUIDED_MISSILE_LIFETIME = 60  # секунд
GUIDED_MISSILE_EXPL_RADIUS = 50  # метров

CCP_ID = 0
