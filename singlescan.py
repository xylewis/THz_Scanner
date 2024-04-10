from thzsys.acquisition import AcquisitionType, TerminalConfiguration, Edge
from thzsys.acquisition import DataCollection
from thzsys.delayline import DelayControl
from thzsys.zmotion import Zmotion, Axis


async def task_init(delay: DelayControl, acquisition: DataCollection):

    acquisition.channel = 1
    acquisition.terminal = 3
    acquisition.edge = Edge.RISING
    acquisition.mode = AcquisitionType.FINITE
    acquisition.coupling = TerminalConfiguration.DEFAULT
    await delay.update()


async def task_exec(delay: DelayControl, acquisition: DataCollection):

    del acquisition.buffer
    num_of_sample = int(delay.length / delay.interval)
    acquisition.config(num_of_sample * delay.iteration, num_of_sample)
    await delay.init()
    print("<Info> Task Initialized.")
    await delay.start()
    acquisition.start()
    print("<Info> Task Started.")
    await delay.run()
    for _ in range(delay.iteration):
        acquisition.read(num_of_sample)
    acquisition.stop()
    print("<Info> Task Stopped.")
    acquisition.close()
    delay.close()
    print("<Info> Task Completed.")


def main_task():
    import asyncio
    asyncio.run(task_init(delay, acquisition))
    asyncio.run(task_exec(delay, acquisition))
    return np.mean(acquisition.buffer, axis=0)


if __name__ == '__main__':

    import matplotlib.pyplot as plt
    import numpy as np
    import time

    delay = DelayControl("10.168.1.16")
    acquisition = DataCollection("Dev3")

    delay.offset = 0  # Sampling Offset (ps)
    delay.length = 70  # Sampling Length (ps)
    delay.interval = 0.02  # Sampling Interval (ps)
    delay.iteration = 1  # Iteration Average

    ts = [x * delay.interval for x in range(int(delay.length / delay.interval))]

    plt.ion()

    for i in range(5):
        raw_data = main_task()

        plt.clf()
        plt.plot(ts, raw_data)
        plt.title('[Scan: %d | Peak to Peak: %.2f Vpp]' % (i + 1, np.max(raw_data) - np.min(raw_data)))
        plt.xlabel('Time (ps)')
        plt.ylabel('Voltage (V)')
        plt.tight_layout()
        plt.pause(.1)

    plt.ioff()
    plt.show()
