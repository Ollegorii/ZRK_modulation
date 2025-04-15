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
    DESTROYED_MISSILE = 'destroyed_missile'
    MISSILE_POS = 'missile_pos'
    MISSILE_DETONATE = 'missile_detonate'


SUMULATION_TIME_STEP = 0.1 # секунд

MISSILE_VELOCITY_MODULE = 1600  # м/с
MISSILE_DETONATE_PERIOD = 120  # секунд
MISSILE_DETONATE_RADIUS = MISSILE_VELOCITY_MODULE * 2 * SUMULATION_TIME_STEP # метров

MIN_DIST_DETECTION = 30  # метров
MAX_DIST_DETECTION = 50000 # метров

MISSILE_TYPE_DRAWER = 0
TARGET_TYPE_DRAWER = 1

CCP_ID = 0
