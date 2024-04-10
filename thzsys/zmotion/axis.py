from .mo_base import zauxdll
from abc import ABCMeta
from ctypes import *


class Bean(metaclass=ABCMeta):

    def __init__(self):
        """ Axis """
        super().__init__()
        self._handle, self._address = c_void_p(), None
        self._string, self._param = (c_float * 0x10)(), (c_float * 0x10)()

    def _call_method(self, function, *args) -> int:
        """ Call Function """
        return function(self._handle, *args)

    def _set_param(self, param, val) -> int:
        """ Set Parameter """
        return self._call_method(param, self._address, val)

    def _get_param(self, param, val) -> int:
        """ Get Parameter """
        return self._call_method(param, self._address, byref(val))

    def _save_param(self) -> int:
        """ Save Param """
        return self._call_method(
            zauxdll.ZAux_Direct_SetVrf, self._address * 0x20 + 0x50, len(self._param), self._param
        )

    def _load_param(self) -> int:
        """ Load Param """
        return self._call_method(
            zauxdll.ZAux_Direct_GetVrf, self._address * 0x20 + 0x50, len(self._param), self._param
        )

    def _save_string(self) -> int:
        """ Save String """
        return self._call_method(
            zauxdll.ZAux_Direct_SetVrf, self._address * 0x20 + 0x40, len(self._string), self._string
        )

    def _load_string(self) -> int:
        """ Load String """
        return self._call_method(
            zauxdll.ZAux_Direct_GetVrf, self._address * 0x20 + 0x40, len(self._string), self._string
        )


class Param(Bean, metaclass=ABCMeta):

    @property
    def id(self) -> int:
        """ Address """
        return self._address

    @property
    def dpos(self) -> float:
        """ Position """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetDpos, val)
        return val.value

    @dpos.setter
    def dpos(self, value) -> None:
        """ Position """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetDpos, val)

    @property
    def mpos(self) -> float:
        """ Feedback """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetMpos, val)
        return val.value

    @mpos.setter
    def mpos(self, value) -> None:
        """ Feedback """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetMpos, val)

    @property
    def idle(self) -> int:
        """ Idle """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetIfIdle, val)
        return val.value

    @property
    def status(self) -> int:
        """ Status """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetAxisStatus, val)
        return val.value

    @property
    def home_status(self) -> int:
        """ Home Status """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetHomeStatus, val)
        return val.value

    @property
    def stop_reason(self) -> int:
        """ Stop Reason """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetAxisStopReason, val)
        return val.value

    @property
    def enable(self) -> int:
        """ Enable"""
        val = c_int()
        self._call_method(zauxdll.ZAux_Direct_GetOp, self.id + 12, byref(val))
        return val.value

    @enable.setter
    def enable(self, value) -> None:
        """ Enable """
        val = c_int(int(value))
        self._call_method(zauxdll.ZAux_Direct_SetOp, self.id + 12, val)

    @property
    def name(self) -> str:
        """ Name"""
        return ''.join([chr(int(x)) for x in self._string if x > 0])

    @name.setter
    def name(self, value: str) -> None:
        """ Name """
        self._string = (c_float * len(self._string))(*[float(ord(x)) for x in value[:len(self._string)]])
    
    @property
    def mode(self) -> int:
        """ Mode """
        return int(self._param[0])

    @mode.setter
    def mode(self, value) -> None:
        """ Mode """
        self._param[0] = int(value)

    @property
    def atype(self) -> int:
        """ Atype """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetAtype, val)
        return val.value

    @atype.setter
    def atype(self, value) -> None:
        """ Atype """
        val = c_int(int(value))
        self._set_param(zauxdll.ZAux_Direct_SetAtype, val)

    @property
    def units(self) -> float:
        """ Units """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetUnits, val)
        return val.value

    @units.setter
    def units(self, value) -> None:
        """ Units """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetUnits, val)

    @property
    def speed(self) -> float:
        """ Speed """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetSpeed, val)
        return val.value

    @speed.setter
    def speed(self, value) -> None:
        """ Speed """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetSpeed, val)

    @property
    def creep(self) -> float:
        """ Creep """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetCreep, val)
        return val.value

    @creep.setter
    def creep(self, value) -> None:
        """ Creep """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetCreep, val)

    @property
    def lspeed(self) -> float:
        """ Lspeed """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetLspeed, val)
        return val.value

    @lspeed.setter
    def lspeed(self, value) -> None:
        """ Lspeed """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetLspeed, val)

    @property
    def sramp(self) -> float:
        """ Sramp """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetSramp, val)
        return val.value

    @sramp.setter
    def sramp(self, value) -> None:
        """ Sramp """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetSramp, val)

    @property
    def accel(self) -> float:
        """ Accel """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetAccel, val)
        return val.value

    @accel.setter
    def accel(self, value) -> None:
        """ Accel """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetAccel, val)

    @property
    def decel(self) -> float:
        """ Decel """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetDecel, val)
        return val.value

    @decel.setter
    def decel(self, value) -> None:
        """ Decel """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetDecel, val)

    @property
    def fastdec(self) -> float:
        """ FastDec """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetFastDec, val)
        return val.value

    @fastdec.setter
    def fastdec(self, value) -> None:
        """ FastDec """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetFastDec, val)

    @property
    def invert_step(self) -> int:
        """ Invert Step """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetInvertStep, val)
        return val.value

    @invert_step.setter
    def invert_step(self, value) -> None:
        """ Invert Step """
        val = c_int(int(value))
        self._set_param(zauxdll.ZAux_Direct_SetInvertStep, val)

    @property
    def max_speed(self) -> int:
        """ Max Speed """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetMaxSpeed, val)
        return val.value

    @max_speed.setter
    def max_speed(self, value) -> None:
        """ Max Speed """
        val = c_int(int(value))
        self._set_param(zauxdll.ZAux_Direct_SetMaxSpeed, val)

    @property
    def home_wait(self) -> int:
        """ Home Wait """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetHomeWait, val)
        return val.value

    @home_wait.setter
    def home_wait(self, value) -> None:
        """ Home Wait """
        val = c_int(int(value))
        self._set_param(zauxdll.ZAux_Direct_SetHomeWait, val)

    @property
    def fs_limit(self) -> float:
        """ Fs Limit """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetFsLimit, val)
        return val.value

    @fs_limit.setter
    def fs_limit(self, value) -> None:
        """ Fs Limit """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetFsLimit, val)

    @property
    def rs_limit(self) -> float:
        """ Rs Limit """
        val = c_float()
        self._get_param(zauxdll.ZAux_Direct_GetRsLimit, val)
        return val.value

    @rs_limit.setter
    def rs_limit(self, value) -> None:
        """ Rs Limit """
        val = c_float(float(value))
        self._set_param(zauxdll.ZAux_Direct_SetRsLimit, val)

    @property
    def datum_in(self) -> int:
        """ Datum In """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetDatumIn, val)
        return val.value

    @datum_in.setter
    def datum_in(self, value) -> None:
        """ Datum In """
        val = c_int(int(value))
        self._set_param(zauxdll.ZAux_Direct_SetDatumIn, val)

    @property
    def forward_in(self) -> int:
        """ Forward In """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetFwdIn, val)
        return val.value

    @forward_in.setter
    def forward_in(self, value) -> None:
        """ Forward In """
        val = c_int(int(value))
        self._set_param(zauxdll.ZAux_Direct_SetFwdIn, val)

    @property
    def reverse_in(self) -> int:
        """ Reverse In """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetRevIn, val)
        return val.value

    @reverse_in.setter
    def reverse_in(self, value) -> None:
        """ Reverse In """
        val = c_int(int(value))
        self._set_param(zauxdll.ZAux_Direct_SetRevIn, val)

    @property
    def alarm_in(self) -> int:
        """ Alarm In """
        val = c_int()
        self._get_param(zauxdll.ZAux_Direct_GetAlmIn, val)
        return val.value

    @alarm_in.setter
    def alarm_in(self, value) -> None:
        """ Alarm In """
        val = c_int(int(value))
        self._set_param(zauxdll.ZAux_Direct_SetAlmIn, val)

    @property
    def invert_in(self) -> int:
        """ Invert In """
        value = 0
        for i, num in enumerate([self.datum_in, self.forward_in, self.reverse_in, self.alarm_in]):
            val = c_int()
            self._call_method(zauxdll.ZAux_Direct_GetInvertIn, num, byref(val))
            value += val.value << i
        return value

    @invert_in.setter
    def invert_in(self, value) -> None:
        """ Invert In """
        value = int(value)
        for i, num in enumerate([self.datum_in, self.forward_in, self.reverse_in, self.alarm_in]):
            val = c_int(value >> i & 1)
            self._call_method(zauxdll.ZAux_Direct_SetInvertIn, num, val)

    def load_param(self) -> int:
        """ Load Param """
        ret = self._load_param()
        if ret:
            return ret
        else:
            self.atype = self._param[1]
            self.units = self._param[2]
            self.speed = self._param[3]
            self.creep = self._param[4]
            self.lspeed = self._param[5]
            self.sramp = self._param[6]
            self.accel = self._param[7]
            self.decel = self._param[8]
            self.fastdec = self._param[9]
            self.invert_step = self._param[10]
            self.datum_in = self._param[11]
            self.forward_in = self._param[12]
            self.reverse_in = self._param[13]
            self.alarm_in = self._param[14]
            self.invert_in = self._param[15]
            return self._load_string()

    def save_param(self) -> int:
        """ Save Param """
        ret = self._save_string()
        if ret:
            return ret
        else:
            self._param[1] = self.atype
            self._param[2] = self.units
            self._param[3] = self.speed
            self._param[4] = self.creep
            self._param[5] = self.lspeed
            self._param[6] = self.sramp
            self._param[7] = self.accel
            self._param[8] = self.decel
            self._param[9] = self.fastdec
            self._param[10] = self.invert_step
            self._param[11] = self.datum_in
            self._param[12] = self.forward_in
            self._param[13] = self.reverse_in
            self._param[14] = self.alarm_in
            self._param[15] = self.invert_in
            return self._save_param()


class Motion(Bean, metaclass=ABCMeta):

    def step(self, distance: int | float):
        """ Relative Move """
        return self._call_method(zauxdll.ZAux_Direct_Single_Move, self._address, c_float(float(distance)))

    def move(self, position: int | float):
        """ Absolute Move """
        return self._call_method(zauxdll.ZAux_Direct_Single_MoveAbs, self._address, c_float(float(position)))

    def datum(self, mode: int = None):
        """ Home Axis """
        mode = mode if mode is not None else self._param[0]
        return self._call_method(zauxdll.ZAux_Direct_Single_Datum, self._address, c_int(int(mode)))

    def cancel(self, mode: int = None):
        """ Cancel Move """
        mode = mode if mode is not None else 2
        return self._call_method(zauxdll.ZAux_Direct_Single_Cancel, self._address, c_int(int(mode)))
