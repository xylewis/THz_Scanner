from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder
from pymodbus.constants import Endian
from abc import ABCMeta
from .de_base import ParamMixin


class Task(metaclass=ABCMeta):

    def __init__(self):
        """ Modbus TCP Client """
        self._ip_address, self._port = "localhost", 502
        self._client, self._slave_id = None, 1

    @property
    def alive(self) -> bool:
        """ Status """
        return self._client.connected

    @property
    async def idle(self) -> bool:
        """ Idle """
        response = await self._client.read_discrete_inputs(0x0, slave=1)
        return response.bits[0]

    async def init(self):
        """ Init """
        self._client = AsyncModbusTcpClient(self._ip_address, self._port)
        return await self._client.connect()

    async def run(self):
        """ Run """
        return await self._client.write_coil(0x0, True, slave=1)

    async def start(self):
        """ Start """
        return await self._client.write_coil(0x1, True, slave=1)

    async def cancel(self):
        """ Cancel """
        return await self._client.write_coil(0x2, True, slave=1)

    async def reset(self):
        """ Reset """
        return await self._client.write_coil(0xf, True, slave=1)

    def close(self) -> None:
        """ Close """
        self._client.close()


class DelayControl(ParamMixin, Task):

    def __init__(self, host: str, port: int = 502):
        """ Optical Delay Control """
        super().__init__()
        self._ip_address, self._port = host, port
        import asyncio
        asyncio.run(self.restore())

    async def restore(self):
        """ Restore Default """
        self._client = AsyncModbusTcpClient(self._ip_address, self._port)
        await self._client.connect()
        response = await self._client.read_input_registers(0x0, 10, slave=1)
        decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.BIG, wordorder=Endian.LITTLE)
        self._load_param(decoder)
        self._client.close()
        return response

    async def update(self):
        """ Update Parameter """
        self._client = AsyncModbusTcpClient(self._ip_address, self._port)
        await self._client.connect()
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.LITTLE)
        self._write_data(builder)
        response = await self._client.write_registers(0x0, builder.to_registers(), slave=1)
        self._client.close()
        return response
