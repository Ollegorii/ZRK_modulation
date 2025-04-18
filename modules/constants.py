from enum import Enum

class MessageType(Enum):
    LAUNCH_MISSILE = "launch_missile"
    LAUNCHED_MISSILE = "launched_missile"
    LAUNCH_COMMAND = "launch_command"
    MISSILE_COUNT_REQUEST = "missile_count_request"
    MISSILE_COUNT_RESPONSE = "missile_count_response"
    FOUND_OBJECTS = "found_objects"
    ACTIVE_OBJECTS = "active_objects"
    CCP_UPDATE_TARGET = 'ccp_upd_target'
    UPDATE_TARGET = 'upd_target'
    MISSILE_GET_HIT = 'missile_get_hit'
    DESTROYED_MISSILE = 'destroyed_missile'
    DRAW_OBJECTS = 'draw_objects'
    MISSILE_POS = 'missile_pos'
    MISSILE_DETONATE = 'missile_detonate'


SIMULATION_STEP = 0.1  # d_t в секундах

MISSILE_VELOCITY_MODULE = 1600  # м/с
MISSILE_DETONATE_PERIOD = 120  # секунд
MISSILE_DETONATE_RADIUS = MISSILE_VELOCITY_MODULE * 2 * SIMULATION_STEP  # метров

MIN_DIST_DETECTION = 30  # метров
MAX_DIST_DETECTION = 50000  # метров
POSSIBLE_TARGET_RADIUS = 10  # метров

MISSILE_TYPE_DRAWER = 0
TARGET_TYPE_DRAWER = 1

CCP_ID = 0
DRAWER_ID = 1
MANAGER_ID = 2
