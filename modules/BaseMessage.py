from abc import ABCMeta
from .constants import MessageType

class BaseMessage(metaclass=ABCMeta):
    """ Абстракатный класс сообщения
    :param relevance: важность сообщения
    :param send_time: время отправки сообщения
    :param type: тип сообщения
    :param sender_ID: ID модуля отправителя
    :param receiver_ID: ID модуля получателя
    """
    def __init__(self, type: MessageType, sender_id: int, receiver_id: int = None, send_time: int = None, relevance: int = 1) -> None:
        self.relevance = relevance
        self.send_time = send_time
        self.type = type
        self.sender_id = sender_id
        self.receiver_id = receiver_id
    
    def __repr__(self) -> str:
        """
        Возвращает строковое представление сообщения для отладки
        """
        return f"{self.__class__.__name__}: send_time={self.send_time}, type={self.type}, sender_id={self.sender_id}, receiver_id={self.receiver_id}, relevance={self.relevance}"