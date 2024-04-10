from enum import Enum


class System(Enum):
    Sensor = 0x0
    Source = 0x1
    Enable = 0x2
    Laser = 0x3
    Bias = 0x4


class Laser(Enum):
    """ Laser Module """
    OSCILLATOR = 0x4
    AMPLIFIER = 0x8
    PORT = 20000
    RF = 20010
    ELMO = 0x4
    ELMA = 0x8
