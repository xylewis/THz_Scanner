# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time         : 2024/01/06 15:30
# @Author       : Jiang Xiaohan
# @File         : control.py
# @Version      : v1.1.1
# @Description  : control system
# Copyright (c) 2023, TJU Terahertz Center All Rights Reserved.

from .constant import System
from .zmotion import Module
from enum import Enum
from ctypes import *

__all__ = ["Device", "Laser", "Bias", "Sensor"]


class LaserModule(Module):

    def __init__(self, handle):
        super().__init__(handle, System.Laser)

    @property
    def oscillator(self) -> tuple:
        state, input = (c_short * 1)(), c_int()
        self._get_modbus_reg(0x5, state)
        self._get_single_input(0x11, input)
        return state[0], input.value

    @property
    def amplifier(self) -> tuple:
        state, input = (c_short * 1)(), c_int()
        self._get_modbus_reg(0x6, state)
        self._get_single_input(0x12, input)
        return state[0], input.value

    @property
    def port(self) -> int:
        state = c_int()
        self._get_single_output(0x1, state)
        return state.value

    @property
    def rf(self) -> int:
        state = c_int()
        self._get_single_output(0xb, state)
        return state.value

    def toggle(self, module: Enum, operation: int) -> int:
        """ Module Toggle"""
        return self._toggle_modbus_bit(module.value + operation)


class Laser(Module):

    def __init__(self, handle):
        super().__init__(handle, System.Laser)
        self._module = LaserModule(handle)

    @property
    def module(self) -> Module:
        """ Laser Module """
        return self._module

    def toggle(self) -> int:
        """ Laser Toggle """
        return self._toggle_output()


class Bias(Module):

    def __init__(self, handle):
        super().__init__(handle, System.Bias)

    def toggle(self):
        """ Bias Toggle """
        return self._toggle_output()


class Sensor(Module):

    def __init__(self, handle):
        super().__init__(handle, System.Sensor)

    @property
    def status(self):
        """ Sensor Status """
        state = (c_short * 2)()
        self._get_modbus_reg(self._address, state)
        return [state[0], state[1]]


class Device(Module):

    def __init__(self, handle):
        super().__init__(handle, System.Enable)

    def toggle(self):
        """ Bias Toggle """
        return self._toggle_output()

    def shutdown(self):
        return

    def restart(self):
        return
