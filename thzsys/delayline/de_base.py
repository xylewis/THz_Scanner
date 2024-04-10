from abc import ABCMeta


class ParamMixin(metaclass=ABCMeta):

    def __init__(self):
        """ Delay Parameter """
        super().__init__()
        self._param = dict()

    @property
    def iteration(self) -> int:
        """ Iteration """
        return self._param["iteration"]

    @iteration.setter
    def iteration(self, val: int) -> None:
        """ Iteration """
        self._param["iteration"] = int(val)

    @property
    def length(self) -> float:
        """ Length """
        return self._param["length"]

    @length.setter
    def length(self, val: float) -> None:
        """ Length """
        self._param["length"] = float(val)

    @property
    def offset(self) -> float:
        """ Offset """
        return self._param["offset"]

    @offset.setter
    def offset(self, val: float) -> None:
        """ Offset """
        self._param["offset"] = float(val)

    @property
    def interval(self) -> float:
        """ Interval """
        return self._param["interval"]

    @interval.setter
    def interval(self, val: float) -> None:
        """ Interval """
        self._param["interval"] = float(val)

    @property
    def rate(self) -> float:
        """ Rate """
        import math
        return math.sqrt(
            (0.3 * 50 / self._param["multiple"] - self.length) /
            (self.length + self._param["ramp"] * 2) *
            self._param["rate"] + 1
        )

    @rate.setter
    def rate(self, val: int) -> None:
        """ Rate """
        self._param["rate"] = int(val)

    @property
    def multiple(self) -> float:
        """ Multiple """
        return self._param["multiple"]

    @property
    def range(self) -> float:
        """ Range """
        return self._param["range"]

    def _load_param(self, decoder):
        self._param = {
            "iteration": 1,
            "length": 100.0,
            "offset": 0.0,
            "interval": 0.02,
            "rate": 5,
            "multiple": decoder.decode_32bit_int(),
            "range": decoder.decode_64bit_float(),
            "ramp": decoder.decode_64bit_float(),
        }

    def _write_data(self, builder):
        builder.add_32bit_int(self._param['iteration'])
        builder.add_64bit_float(self._param['length'])
        builder.add_64bit_float(self._param['offset'])
        builder.add_64bit_float(self._param['interval'])
        builder.add_32bit_int(self._param["rate"])
