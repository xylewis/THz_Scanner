from nidaqmx.constants import TerminalConfiguration, AcquisitionType, Edge
from abc import ABCMeta


class ParamMixin(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()
        self._device = None
        self._param = dict()

    @property
    def channel(self) -> str:
        """ Physical Channel """
        return self._param["physicalChannel"]

    @channel.setter
    def channel(self, val: int) -> None:
        """ Physical Channel """
        self._param["physicalChannel"] = '%s/ai%d' % (self._device.name, val)

    @property
    def terminal(self) -> str:
        """ Source Terminal """
        return self._param["sourceTerminal"]

    @terminal.setter
    def terminal(self, val: int) -> None:
        """ Source Terminal """
        self._param["sourceTerminal"] = '/%s/PFI%d' % (self._device.name, val)

    @property
    def coupling(self) -> TerminalConfiguration:
        """ Terminal Config """
        return self._param["terminalConfig"]

    @coupling.setter
    def coupling(self, val: TerminalConfiguration) -> None:
        """ Terminal Config """
        self._param["terminalConfig"] = val

    @property
    def edge(self) -> Edge:
        """ Active Edge """
        return self._param["activeEdge"]

    @edge.setter
    def edge(self, val: Edge) -> None:
        """ Active Edge """
        self._param["activeEdge"] = val

    @property
    def range(self) -> tuple[float, float]:
        """ Input Range """
        return self._param["inputRange"]

    @range.setter
    def range(self, val: tuple[float, float]) -> None:
        """ Input Range """
        self._param["inputRange"] = val

    @property
    def mode(self) -> AcquisitionType:
        """ Sample Mode """
        return self._param["sampleMode"]

    @mode.setter
    def mode(self, val: AcquisitionType) -> None:
        """ Sample Mode """
        self._param["sampleMode"] = val

    @property
    def rate(self) -> float:
        """ Sample Rate """
        return self._param["sampleRate"]

    @rate.setter
    def rate(self, val: float) -> None:
        """ Sample Rate """
        self._param["sampleRate"] = val
