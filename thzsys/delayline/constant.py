from enum import Enum


class DelayType(Enum):
    UserDefined: int = 0
    FastSampling: int = 1
    HighResolution: int = 2


class Operation(Enum):

    Run: int = 0x0
    Start: int = 0x1
    Cancel: int = 0x2
    Reset: int = 0xf
