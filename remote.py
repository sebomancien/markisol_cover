from enum import IntEnum


class Channel(IntEnum):
    CH1 = 0x1
    CH2 = 0x2
    CH3 = 0x3
    CH4 = 0x4
    CH5 = 0x5
    ALL = 0xF


class Command(IntEnum):
    OPEN  = 0xC
    CLOSE = 0x1
    STOP  = 0x5


class RemoteCommand:
    def __init__(self, remote_id: int, channel: Channel, command: Command, model_id: int) -> None:
        self.remote_id = remote_id
        self.channel   = channel
        self.command   = command
        self.model_id  = model_id

    def encode(self) -> int:
        return (self.model_id << 24) | (self.command << 20) | (self.channel << 16) | self.remote_id

    def decode(self, data: int) -> None:
        self.model_id  = (data >> 24) & 0xFF
        self.command   = Command((data >> 20) & 0xF)
        self.channel   = Channel((data >> 16) & 0xF)
        self.remote_id = (data >>  0) & 0xFFFF
