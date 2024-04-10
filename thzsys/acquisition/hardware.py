from nidaqmx.constants import TerminalConfiguration, AcquisitionType, Edge, VoltageUnits
from nidaqmx.system.device import Device
from .ac_base import ParamMixin


class Task:

    def __init__(self):
        """ NI-DAQmx Task """
        self._buffer = []
        self._task = None

    @property
    def buffer(self) -> list:
        """ Buffer """
        return self._buffer

    @buffer.deleter
    def buffer(self) -> None:
        """ Buffer """
        self._buffer = []

    def read(self, number_of_samples, timeout=1.0) -> None:
        """ Read Sample """
        self._buffer.append(self._task.read(int(number_of_samples), timeout))

    def start(self) -> None:
        """ Start Task """
        self._task.start()

    def stop(self) -> None:
        """ Stop Task """
        self._task.stop()

    def close(self) -> None:
        """ Close Task """
        self._task.close()


class DataCollection(ParamMixin, Task):

    def __init__(self, hardware):
        """ Data Collection """
        super().__init__()
        self._device = Device(hardware)
        self._param = {
            "physicalChannel": f'{self._device.name}/ai0',
            "sourceTerminal": '',
            "terminalConfig": TerminalConfiguration.DEFAULT,
            "activeEdge": Edge.RISING,
            "inputRange": (-5.0, 5.0),
            "sampleMode": AcquisitionType.CONTINUOUS,
            "sampleRate": self._device.ai_max_multi_chan_rate,
            "scaleUnits": VoltageUnits.VOLTS,
        }

    @property
    def device(self) -> Device:
        """ Device """
        return self._device

    def config(self, number_of_samples: int, sample_interval: int = 0, callback_method=None) -> None:
        """ Configure Task """
        import nidaqmx
        self._task = nidaqmx.Task()
        self._task.ai_channels.add_ai_voltage_chan(
            physical_channel=self._param["physicalChannel"],
            terminal_config=self._param["terminalConfig"],
            min_val=self._param["inputRange"][0],
            max_val=self._param["inputRange"][1],
            units=self._param["scaleUnits"],
        )
        self._task.timing.cfg_samp_clk_timing(
            rate=self._param["sampleRate"],
            source=self._param["sourceTerminal"],
            active_edge=self._param["activeEdge"],
            sample_mode=self._param["sampleMode"],
            samps_per_chan=number_of_samples,
        )
        self._task.register_every_n_samples_acquired_into_buffer_event(
            sample_interval=sample_interval if sample_interval else number_of_samples,
            callback_method=callback_method if callback_method is not None else self._callback,
        )

    @staticmethod
    def _callback(task_handle, every_n_samples_event_type, number_of_samples, callback_data):
        """ Callback Method """
        print("<Process> %d Samples Acquired." % number_of_samples)
        return 0
