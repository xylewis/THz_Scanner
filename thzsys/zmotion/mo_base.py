from abc import ABCMeta
from ctypes import *
import ctypes
import os.path

# zauxdll = WinDLL(os.path.join(os.path.dirname(__file__), 'zauxdll.dll'))
dll_dir = "./dll"
os.environ["PATH"] += ";" + dll_dir
zauxdll = ctypes.CDLL("zauxdll.dll",winmode=0)
# zauxdll =cdll.LoadLibrary("./zauxdll.dll")

class Base(metaclass=ABCMeta):

    def __init__(self):
        """
        Initialize Module
        """
        self._handle = c_void_p()


class IO(Base, metaclass=ABCMeta):

    def _set_single_output(self, address: int, status) -> int:
        """
        Set Single Output
        :param address: Output Address
        :param status: Status [uint32]
        :return: Response
        """
        return zauxdll.ZAux_Direct_SetOp(self._handle, address, status)

    def _get_single_output(self, address: int, status) -> int:
        """
        Get Single Output
        :param address: Output Address
        :param status: Status [uint32]
        :return: Response
        """
        return zauxdll.ZAux_Direct_GetOp(self._handle, address, byref(status))

    def _get_single_input(self, address: int, status) -> int:
        """
        Get Single Input
        :param address: Input Address
        :param status: Status [uint32]
        :return: Response
        """
        return zauxdll.ZAux_Direct_GetIn(self._handle, address, byref(status))

    def _set_multi_output(self, start: int, end: int, status) -> int:
        """
        Set Multiple Output
        :param start: Start Address
        :param end: End Address
        :param status: Status [uint32]
        :return: Response
        """
        return zauxdll.ZAux_Direct_SetOutMulti(self._handle, start, end, byref(status))

    def _get_multi_output(self, start: int, end: int, status) -> int:
        """
        Get Multiple Output
        :param start: Start Address
        :param end: End Address
        :param status: Status [uint32]
        :return: Response
        """
        return zauxdll.ZAux_Direct_GetOutMulti(self._handle, start, end, byref(status))

    def _get_multi_input(self, start: int, end: int, status) -> int:
        """
        Get Multiple Input
        :param start: Start Address
        :param end: End Address
        :param status: Status [uint32]
        :return: Response
        """
        return zauxdll.ZAux_Direct_GetInMulti(self._handle, start, end, byref(status))


class Modbus(Base, metaclass=ABCMeta):

    def _set_modbus_bit(self, address: int, count: int, data) -> int:
        """
        Set Modbus Bit
        :param address: Start Address
        :param count: Register Number
        :param data: Data List [uint8 *]
        :return: Response
        """
        return zauxdll.ZAux_Modbus_Set0x(self._handle, address, count, byref(data))

    def _get_modbus_bit(self, address: int, count: int, data) -> int:
        """
        Get Modbus Bit
        :param address: Start Address
        :param count: Register Number
        :param data: Data List [uint8 *]
        :return: Response
        """
        return zauxdll.ZAux_Modbus_Get0x(self._handle, address, count, byref(data))

    def _set_modbus_reg(self, address: int, data) -> int:
        """
        Set Modbus Reg
        :param address: Start Address
        :param data: Data List [uint16 *]
        :return: Response
        """
        return zauxdll.ZAux_Modbus_Set4x(self._handle, address, len(data), byref(data))

    def _get_modbus_reg(self, address: int, data) -> int:
        """
        Get Modbus Reg
        :param address: Start Address
        :param data: Data List [uint16 *]
        :return: Response
        """
        return zauxdll.ZAux_Modbus_Get4x(self._handle, address, len(data), byref(data))

    def _set_modbus_long(self, address: int, data) -> int:
        """
        Set Modbus Long
        :param address: Start Address
        :param data: Data List [int *]
        :return: Response
        """
        return zauxdll.ZAux_Modbus_Set4x_Long(self._handle, address, len(data), byref(data))

    def _get_modbus_long(self, address: int, data) -> int:
        """
        Get Modbus Long
        :param address: Start Address
        :param data: Data List [int *]
        :return: Response
        """
        return zauxdll.ZAux_Modbus_Get4x_Long(self._handle, address, len(data), byref(data))

    def _set_modbus_ieee(self, address: int, data) -> int:
        """
        Set Modbus IEEE
        :param address: Start Address
        :param data: Data List [float *]
        :return: Response
        """
        return zauxdll.ZAux_Modbus_Set4x_Float(self._handle, address, len(data), byref(data))

    def _get_modbus_ieee(self, address: int, data) -> int:
        """
        Get Modbus IEEE
        :param address: Start Address
        :param data: Data List [float *]
        :return: Response
        """
        return zauxdll.ZAux_Modbus_Get4x_Float(self._handle, address, len(data), byref(data))

    def _set_modbus_string(self, address: int, data) -> int:
        """
        Set Modbus ASCII
        :param address: Start Address
        :param data: Data List [char *]
        :return: Response
        """
        return zauxdll.ZAux_Modbus_Set4x_String(self._handle, address, len(data), byref(data))

    def _get_modbus_string(self, address: int, data) -> int:
        """
        Get Modbus ASCII
        :param address: Start Address
        :param data: Data List [char *]
        :return: Response
        """
        return zauxdll.ZAux_Modbus_Get4x_String(self._handle, address, len(data), byref(data))


class VR(Base, metaclass=ABCMeta):

    def _set_vr(self, address: int, data) -> int:
        """
        Set VR Register
        :param address: Start Address
        :param data: Data List [float *]
        :return: Response
        """
        return zauxdll.ZAux_Direct_SetVrf(self._handle, address, len(data), byref(data))

    def _get_vr(self, address: int, data) -> int:
        """
        Get VR Register
        :param address: Start Address
        :param data: Data List [float *]
        :return: Response
        """
        return zauxdll.ZAux_Direct_GetVrf(self._handle, address, len(data), byref(data))


class Table(Base, metaclass=ABCMeta):

    def _set_table(self, address: int, data) -> int:
        """
        Set Table Register
        :param address: Start Address
        :param data: Data List [float *]
        :return: Response
        """
        return zauxdll.ZAux_Direct_SetTable(self._handle, address, len(data), byref(data))

    def _get_table(self, address: int, data) -> int:
        """
        Get Table Register
        :param address: Start Address
        :param data: Data List [float *]
        :return: Response
        """
        return zauxdll.ZAux_Direct_GetTable(self._handle, address, len(data), byref(data))
