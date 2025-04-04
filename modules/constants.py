from enum import Enum

class MessageType(Enum):
    LAUNCH_MISSILE = 1
    LAUNCHED_MISSILE = 2

GUIDED_MISSILE_SPEED = 1000  # м/с
GUIDED_MISSILE_LIFETIME = 60  # секунд
GUIDED_MISSILE_EXPL_RADIUS = 50  # метров