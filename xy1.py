from thzsys.acquisition import AcquisitionType, TerminalConfiguration, Edge
from thzsys.acquisition import DataCollection
from thzsys.delayline import DelayControl
from thzsys.zmotion import Zmotion, Axis


async def task_init(delay: DelayControl, acquisition: DataCollection):
    acquisition.channel = 1
    # acquisition.terminal = 3
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
    # print("<Info> Task Started.")
    await delay.run()
    for _ in range(delay.iteration):
        acquisition.read(num_of_sample)
    acquisition.stop()
    # print("<Info> Task Stopped.")
    acquisition.close()
    delay.close()
    # print("<Info> Task Completed.")


def main_task():
    import asyncio
    asyncio.run(task_init(delay, acquisition))
    asyncio.run(task_exec(delay, acquisition))
    return np.mean(acquisition.buffer, axis=0)


if __name__ == '__main__':

    import matplotlib.pyplot as plt
    import numpy as np
    import time

    control = Zmotion("127.0.0.1")
    axis = [Axis(control.handle, i) for i in [1, 2]]
    delay = DelayControl("127.0.0.1",5002)
    acquisition = DataCollection("Dev2")

    # Delay line set
    delay.offset = 20  # Sampling Offset (ps)
    delay.length = 70  # Sampling Length (ps)
    delay.interval = 0.02  # Sampling Interval (ps)
    delay.iteration = 1  # Iteration Average
    f0 = 0.75
    # Axis set
    x_start = -5
    x_end = 5
    x_step = 5
    y_start = 5
    y_end = 5
    y_step = 5
    axis[0].speed = 2.0
    axis[1].speed = 2.0

    x_sequence = np.arange(x_start, x_end + x_step, x_step)
    print(x_sequence)
    y_sequence = np.arange(y_start, y_end + y_step, y_step)
    y_sequence2 = np.arange(y_end, y_start-y_step, -y_step)
    print('y:', y_sequence)
    print('y反转:', y_sequence2)
    X, Y = np.meshgrid(x_sequence, y_sequence2)
    time_n, freq_n = int(delay.length / delay.interval), 8000
    t_seq, f_seq = np.arange(time_n) * delay.interval, np.arange(freq_n) / delay.interval / freq_n
    print(f_seq)

    # Begin scan plane
    axis[0].move(x_start)
    axis[1].move(y_start)
    axis[1].step(-y_step)

    t_summary = []
    f_summary = []

    for i in range(len(y_sequence)):
        axis[1].step(y_step)
        axis[0].move(x_start)
        for j in range(len(x_sequence)):

            while not all([ax.idle for ax in axis]):  # wait axis stopped
                time.sleep(1)
            plt.ion()
            for m in range(1):
                raw_data = main_task()
                print(type(raw_data))
                f_data = np.fft.fft(raw_data, freq_n)
                t_summary.append(raw_data)
                f_summary.append(f_data)

                plt.clf()
                plt.plot(t_seq, raw_data)
                plt.title('[Peak to Peak: %.2f Vpp]' % (np.max(raw_data) - np.min(raw_data)))
                plt.xlabel('Time (ps)')
                plt.ylabel('Voltage (V)')
                plt.tight_layout()
                plt.pause(.1)

            plt.ioff()
            # plt.show()
            print('PosX:', axis[0].dpos, 'Y:', axis[1].dpos)
            axis[0].step(x_step)



    np.savetxt('t_data.txt', t_summary, fmt='%.4f')
    np.savetxt('f_data.txt', f_summary, fmt='%.4f')

    # Data process
    f_seq = f_seq.tolist()
    fN = f_seq.index(f0)
    f_seq_array = np.array(f_summary)
    f0_seq = (f_seq_array[:, fN])
    print(type(f0_seq))
    f0_plane = f0_seq.reshape(len(y_sequence), len(x_sequence))
    plt.ion()
    plt.clf()
    plt.pcolor(X, Y, abs(f0_plane))
    plt.ioff()
    plt.show()
