from enum import Enum

class ObjectType(Enum):
    AIR_PLANE = "AIR_PLANE"
    HELICOPTER = "HELICOPTER"
    ANOTHER = "ANOTHER"
    MISSILE_LAUNCHER = "MISSILE_LAUNCHER"
    RADAR = "RADAR"

    @classmethod
    def get_display_name(cls, obj_type):
        names = {
            cls.AIR_PLANE: "Самолет",
            cls.HELICOPTER: "Вертолет",
            cls.ANOTHER: "Другой объект",
            cls.MISSILE_LAUNCHER: "Пусковая установка",
            cls.RADAR: "Радар"
        }
        return names.get(obj_type, str(obj_type))

