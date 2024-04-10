from .mo_base import IO, Modbus, VR, Table
from .axis import Param, Motion
from .device import Device
from ctypes import *


class Zmotion(Device, IO, Modbus, VR, Table):

    def __init__(self, host):
        super().__init__()
        self._address = host
        if self._connect(self._address):
            raise
        else:
            self._get_system_specification(), self._get_controller_information(), self._get_rtc_time()
        
    @property
    def axes(self):
        """ Axes Status """
        return self._axes

    @property
    def handle(self):
        """ Control Handle """
        return self._handle

    @property
    def model(self) -> str:
        """ Device Model """
        return self._model.value.decode('utf-8')

    @property
    def version(self) -> str:
        """ Firmware Version """
        return self._version.value.decode('utf-8')

    @property
    def serial(self) -> str:
        """ Serial Number """
        return self._serial.value.decode('utf-8')

    @property
    def datetime(self) -> str:
        """ Date Time """
        return self._date.value.decode('utf-8') + ' ' + self._time.value.decode('utf-8')

    def active(self) -> int:
        """ Active Device """
        ret = self._connect(self._address)
        if ret == 20008:
            self._disconnect()
        return ret

    def close(self) -> int:
        """ Close Device """
        if self.handle.value is not None:
            return self._disconnect()
        else:
            return 0

    def get_axes_info(self) -> int:
        """ Get Axes Info """
        ret = self.axes.get_status()
        if ret:
            return ret
        else:
            return self.axes.get_enable()

    def stop_all_axes(self, mode: int = 2) -> int:
        """ Stop All Axes """
        return self.axes.stop_all(mode)


class Module(IO, Modbus):

    def __init__(self, handle, device):
        """
        Initialize Axis
        :param handle: Connection Handle
        :param device: Module Address
        """
        super().__init__()
        self._handle, self._address = handle, device.value

    @property
    def status(self) -> int:
        state = c_int()
        self._get_single_output(self._address, state)
        return state.value

    def _toggle_output(self, address=None) -> int:
        address, state = self._address if address is None else address, c_int()
        ret = self._get_single_output(address, state)
        return ret if ret else self._set_single_output(address, c_int(0 if state.value else 1))

    def _toggle_modbus_bit(self, address=None) -> int:
        address, state = self._address if address is None else address, c_int()
        ret = self._get_modbus_bit(address, 1, state)
        return ret if ret else self._set_modbus_bit(address, 1, c_int(0 if state.value else 1))


class Axis(Param, Motion):

    def __init__(self, handle, index):
        """
        Initialize Axis
        :param handle: Connection Handle
        :param index: Axis Address
        """
        super().__init__()
        self._handle, self._address = handle, index - 1
        self._load_string(), self._load_param()
