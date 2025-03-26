from abc import ABCMeta

class BaseMessage(metaclass=ABCMeta):
    """ Абстракатный класс сообщения
    :param relevance: важность сообщения
    :param send_time: время отправки сообщения
    :param type: тип сообщения
    :param sender_ID: ID модуля отправителя
    :param receiver_ID: ID модуля получателя
    """
    def __init__(self, type: int, send_time: int, sender_id: int, receiver_id: int, relevance: int = 1) -> None:
        self.relevance = relevance
        self.send_time = send_time
        self.type = type
        self.sender_id = sender_id
        self.receiver_id = receiver_id