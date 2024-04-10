from .mo_base import zauxdll, Base
from abc import ABCMeta
from ctypes import *


class Axes(metaclass=ABCMeta):

    def __init__(self, handle):
        self._handle, self._num = handle, 0
        self._idle, self._status, self._enable = (c_int * self._num)(), (c_int * self._num)(), c_uint32()
        self._dpos, self._mpos, self._speed = (c_float * self._num)(), (c_float * self._num)(), (c_float * self._num)()

    @property
    def num(self) -> int:
        return self._num

    @num.setter
    def num(self, val: int) -> None:
        self._num = val

    @property
    def idle(self) -> list:
        """ Axes Idle """
        return [self._idle[i] for i in range(self._num)]

    @property
    def status(self) -> list:
        """ Axes Status """
        return [self._status[i] for i in range(self._num)]

    @property
    def position(self) -> list:
        """ Axes Position """
        return [self._dpos[i] for i in range(self._num)]

    @property
    def feedback(self) -> list:
        """ Axes Feedback """
        return [self._mpos[i] for i in range(self._num)]

    @property
    def speed(self) -> list:
        """ Axes Speed """
        return [self._speed[i] for i in range(self._num)]

    @property
    def enable(self) -> list:
        """ Axes Enable """
        return [self._enable.value >> i & 1 for i in range(self._num)]

    def get_status(self) -> int:
        """ Get Current Status """
        return zauxdll.ZAux_Direct_GetAllAxisInfo(
            self._handle, self._num, byref(self._idle), byref(self._dpos), byref(self._mpos), byref(self._status)
        )

    def get_position(self) -> int:
        """ Get Current Position """
        return zauxdll.ZAux_GetModbusDpos(self._handle, self._num, byref(self._dpos))

    def get_feedback(self) -> int:
        """ Get Current Feedback """
        return zauxdll.ZAux_GetModbusMpos(self._handle, self._num, byref(self._mpos))

    def get_speed(self) -> int:
        """ Get Current Speed """
        return zauxdll.ZAux_GetModbusCurSpeed(self._handle, self._num, byref(self._speed))

    def get_enable(self) -> int:
        """ Get Current Enable """
        return zauxdll.ZAux_Direct_GetOutMulti(self._handle, 12, 12 + self._num - 1, byref(self._enable))

    def stop_all(self, mode: int) -> int:
        """ Stop All Axes """
        return zauxdll.ZAux_Direct_Rapidstop(self._handle, c_int(int(mode)))


class Device(Base):

    def __init__(self):
        """
        Device Module
        """
        super().__init__()
        self._date, self._time = (c_char * 16)(), (c_char * 16)()
        self._axis, self._motor, self._io = c_uint16(), c_uint8(), (c_uint8 * 4)()
        self._model, self._version, self._serial = (c_char * 16)(), (c_char * 16)(), (c_char * 16)()
        self._axes = Axes(self._handle)

    def _get_system_specification(self) -> int:
        """
        Get System Specification
        :return: Response
        """
        return zauxdll.ZAux_GetSysSpecification(self._handle, byref(self._axis), byref(self._motor), self._io)

    def _get_controller_information(self) -> int:
        """
        Get System Information
        :return: Response
        """
        return zauxdll.ZAux_GetControllerInfo(self._handle, self._model, self._version, self._serial)

    def _get_rtc_time(self) -> int:
        """
        Get System RTC Time
        :return: Response
        """
        return zauxdll.ZAux_GetRtcTime(self._handle, self._date, self._time)

    def _sync_rtc_time(self) -> int:
        """
        Sync System RTC Time
        :return: Response
        """
        import time
        datetime = time.strftime("%Y%m%d").encode('utf-8'), time.strftime("%H%M%S").encode('utf-8')
        return zauxdll.ZAux_SetRtcTime(self._handle, *datetime)

    # TODO: ZAux_ZarDown

    def _connect(self, host: str) -> int:
        """
        Connect Device
        :param host: Hostname
        :return: Response
        """
        return zauxdll.ZAux_OpenEth(host.encode('utf-8'), pointer(self._handle))

    def _disconnect(self) -> int:
        """
        Disconnect Device
        :return: Response
        """
        return zauxdll.ZAux_Close(self._handle)
