import os.path

from thzsys.acquisition import DataCollection
from thzsys.delayline import DelayControl
from abc import ABCMeta, abstractmethod
from multiprocessing import Process, Queue
from threading import Thread, Event
import numpy as np


class Base(metaclass=ABCMeta):

    def __init__(self):
        """ Signal Collection """
        self._queue, self._thread = Queue(), None
        self._delay, self._task = None, None
        self.iteration = 1
        self.current = 0

    @property
    def delay(self) -> DelayControl:
        return self._delay

    @property
    def task(self) -> DataCollection:
        return self._task

    @property
    def buffer(self) -> list:
        if not self._queue.empty():
            self.current += 1
            return self._queue.get(timeout=10).tolist()
        else:
            return []

    @property
    def num_of_scan(self) -> int:
        return int(self.delay.iteration * self.iteration)

    @property
    def num_of_sample(self) -> int:
        return int(self.delay.length / self.delay.interval)

    def _task_init(self):  # scan task setup
        from thzsys.acquisition import AcquisitionType, TerminalConfiguration, Edge
        self.task.channel = 1
        # self.task.terminal = 3
        self.task.edge = Edge.RISING
        self.task.mode = AcquisitionType.FINITE
        self.task.coupling = TerminalConfiguration.DEFAULT
        self.task.rate = self.task.device.ai_max_multi_chan_rate

    def _fetch_data(self):
        """ Fetch Data """
        del self._task.buffer
        for i in range(self.delay.iteration):
            self._task.read(self.num_of_sample, 1)
            self._queue.put(np.mean(self._task.buffer, axis=0))

    async def _scan_init(self):
        """ Initialize """
        self._task_init()
        self._task.config(self.num_of_sample * self.delay.iteration)
        await self._delay.init()
        await self._delay.start()
        print("<Info> Task Initialized.")

    async def _scan_exec(self):
        """ Execute """
        self._task.start()
        print("<Info> Task Started.")
        await self._delay.run()
        self._fetch_data()
        self._task.stop()
        print("<Info> Task Stopped.")

    def _scan_close(self):
        """ Close """
        self.delay.close()
        self.task.close()
        print("<Info> Task Completed.")


class ThreadMixin(metaclass=ABCMeta):

    def __init__(self):
        """ Scan Thread """
        super().__init__()
        self._idle, self._flag = Event(), Event()
        self._idle.set(), self._flag.set()

    def _main_thread(self):
        """ Main """
        import asyncio
        asyncio.run(self._main_task())

    @abstractmethod
    async def _main_task(self):
        pass

    @property
    def idle(self):
        return self._idle.is_set()

    def start(self):
        """ Start """
        self._thread = Thread(target=self._main_thread)
        self._thread.start()

    def pause(self):
        """ Pause """
        self._flag.clear()

    def resume(self):
        """ Resume """
        self._flag.set()

    def stop(self):
        """ Stop """
        self._idle.set()


class ScanTask(ThreadMixin, Base):

    def __init__(self, delay: DelayControl, acquisition: DataCollection):
        super().__init__()
        self._delay, self._task = delay, acquisition

    async def _main_task(self):
        """ Main Task """
        self._idle.clear()
        await self._scan_init()
        try:
            with open('TempData.csv', 'ab') as cache:
                cache.truncate(0)
                for _ in range(self.iteration):
                    if self._idle.is_set():
                        self._flag.set()
                        break
                    self._flag.wait()
                    await self._scan_exec()
                    np.savetxt(cache, [np.mean(self._task.buffer, axis=0)], fmt='%.4f', delimiter=',')
                else:
                    self._idle.set()  # self._queue.put(np.loadtxt('TempData.csv', delimiter=','))
                    print(len(np.loadtxt('TempData.csv', delimiter=',')))
        finally:
            self._scan_close()


if __name__ == '__main__':

    import asyncio
    import time

    delay = DelayControl("127.0.0.1", 5002)
    acquisition = DataCollection("Dev2")

    task = ScanTask(delay, acquisition)

    delay.length = 100
    delay.offset = 20
    delay.interval = 0.02
    delay.iteration = 3
    task.iteration = 2

    asyncio.run(delay.update())

    task.start()

    # task.stop()

    while 1:
        time.sleep(.1)
        n = task.buffer
        if len(n) > 0:
            print(len(n), len(n[0]), type(n[0]))

    # queue = Queue()
    # proc = Process(target=scan_exec, args=(queue, iteration))
    # proc.start()
    #
    # plt.figure(figsize=(12, 6))
    # plt.ion()
    #
    # for i in range(iteration):
    #     t_data = queue.get(timeout=10)
    #     t_data = np.array(t_data)
    #     f_data = np.fft.fft(t_data[:len(t_seq)], freq_n)
    #     data_plot(i)
    #
    # plt.ioff()
    # plt.show()
