import numpy as np
import matplotlib.pyplot as plt
from typing import List


class Unit:
    au: bool = False
    db: bool = True
    rad: bool = False
    deg: bool = True


class DataPlot:
    def __init__(self, ts: float, n: int):
        self._buffer = None
        self._ts = ts
        self._n = n
        self._f = 1.0
        self._tlim = None
        self._flim = None
        self._x = None
        self._y = None
        self._data = []
        self._unit = {
            'amp': True,
            'pha': True,
        }

    @property
    def mat(self):
        return self._data

    @mat.setter
    def mat(self, data) -> None:
        self._data = data

    @mat.deleter
    def mat(self) -> None:
        self._data = []

    @property
    def t(self) -> np.ndarray:
        return np.arange(0, self._tlim, self._ts)

    @t.setter
    def t(self, val: float) -> None:
        self._tlim = val

    @property
    def f(self) -> np.ndarray:
        return np.arange(0, self._flim, 1 / self._ts / self._n)

    @f.setter
    def f(self, val: float) -> None:
        self._flim = val

    @property
    def n(self) -> int:
        return self._n

    @n.setter
    def n(self, val: int) -> None:
        self._n = val

    @property
    def x(self) -> np.ndarray:
        return self._x

    @x.setter
    def x(self, arr: np.ndarray) -> None:
        self._x = arr

    @property
    def y(self) -> np.ndarray:
        return self._y

    @y.setter
    def y(self, arr: np.ndarray) -> None:
        self._y = arr

    @property
    def freq(self) -> float:
        return self._f

    @freq.setter
    def freq(self, val: float) -> None:
        assert 0 <= val <= self._flim
        self._f = val

    @property
    def real(self) -> np.ndarray:
        return np.real(self._buffer)

    @property
    def imag(self) -> np.ndarray:
        return np.imag(self._buffer)

    @property
    def amp(self) -> np.ndarray:
        if self._unit['amp']:
            return np.log10(np.abs(self._buffer)) * 20
        else:
            return np.abs(self._buffer)

    @amp.setter
    def amp(self, log: bool) -> None:
        self._unit['amp'] = log

    @property
    def pha(self) -> np.ndarray:
        if self._unit['pha']:
            return np.angle(self._buffer) / np.pi * 180
        else:
            return np.angle(self._buffer)

    @pha.setter
    def pha(self, deg: bool) -> None:
        self._unit['pha'] = deg

    def load(self, filename: str) -> None:
        self._data = np.genfromtxt(filename)

    def save(self, filename: str) -> None:
        np.savetxt(filename, self._data, fmt='%f', delimiter='\t')

    def fft(self) -> np.ndarray:
        self._buffer = np.fft.fft(self.mat, self.n)
        return self._buffer

    def plot_t(self, pdata) -> None:
        for data in pdata:
            plt.plot(self.t, data[0:len(self.t)])

    def plot_f(self, pdata) -> None:
        for data in pdata:
            plt.plot(self.f, data[0:len(self.f)])

    def plot_img(self, pdata, cmap) -> None:
        data = np.zeros(len(self.x) * len(self.y))
        data[0:len(pdata)] = pdata[:, round(self._f*self._ts*self._n)]
        data = data.reshape(len(self.y), len(self.x))
        x, y = np.meshgrid(self.x, self.y)
        plt.pcolormesh(data, cmap=cmap, shading='flat')
        plt.colorbar(shrink=0.75)
        plt.axis('square')

