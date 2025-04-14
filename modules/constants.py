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
    CCP_INIT_MESSAGE = 'CPP_init_message'


SIMULATION_STEP = 1  # d_t

GUIDED_MISSILE_SPEED = 1000  # м/с
GUIDED_MISSILE_LIFETIME = 60  # секунд
GUIDED_MISSILE_EXPL_RADIUS = 50  # метров

MIN_DIST_DETECTION = 30  # метров
MAX_DIST_DETECTION = 50000 # метров
POSSIBLE_TARGET_RADIUS = 10 # метров

MISSILE_TYPE_DRAWER = 0
TARGET_TYPE_DRAWER = 1

CCP_ID = 0
DRAWER_ID = 1
MANAGER_ID = 2
