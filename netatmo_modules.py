# -*- coding: utf-8 -*-
# Copyright (C) 2015 Marco Trevisan
#
# CoPyCloud: a simple python wrapper to manage the Copy.com cloud
#
# Authors:
#  Marco Trevisan (Treviño) <mail@3v1n0.net>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUTa
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import time

class Module(object):

    class Type:
        MAIN = "NAMain"
        OUTDOOR = "NAModule1"
        WIND = "NAModule2"
        RAIN = "NAModule3"
        INDOOR = "NAModule4"

    @staticmethod
    def factory(data):
        if data['type'] == Module.Type.MAIN:
            return ControlUnit(data)
        if data['type'] == Module.Type.OUTDOOR:
            return Outdoor(data)
        if data['type'] == Module.Type.WIND:
            return Wind(data)
        if data['type'] == Module.Type.RAIN:
            return Outdoor(data)
        if data['type'] == Module.Type.INDOOR:
            return Indoor(data)

        raise Exception("No valid type for data found")

    def __init__(self, data):
        self.__data = data

    def __getitem__(self, value):
        return self.__data[value]

    @property
    def id(self):
        return self['_id']

    @property
    def type(self):
        return self['type']

    @property
    def name(self):
        return self['module_name']

    @property
    def dashboard(self):
        return self['dashboard_data']

    @property
    def updated_time(self):
        return self.dashboard['time_utc']

    @property
    def age(self):
        return time.time() - self.updated_time

    @property
    def sensors(self):
        return self['data_type']

    def has_battery(self):
        return False

    def get_sensors_data(self):
        return { s: self.dashboard[s] for s in self.sensors }


class WirelessModule(Module):
    def __signal_levels(self):
        return [self.Signal.LEVEL_0, self.Signal.LEVEL_1, self.Signal.LEVEL_2, self.Signal.LEVEL_3]

    def __signal_nearest_level(self):
        return min(self._signal_levels(), key=lambda l:abs(l-self.signal_strength))

    @property
    def signal_level(self):
        return self._signal_levels().index(self.__signal_nearest_level())

    @property
    def signal_percent(self):
        return clamp(0, (self.Signal.MIN - self.signal_strength) * 100.0 / (self.Signal.MIN - self.Signal.MAX), 100)


class WifiModule(WirelessModule):
    class Signal:
        MIN = 100
        MAX = 60
        LEVEL_0 = 90
        LEVEL_1 = 80
        LEVEL_2 = 70
        LEVEL_3 = 60

    @property
    def signal_strength(self):
        return self['wifi_status']


class RadioModule(WirelessModule):
    class Signal:
        MIN = 90
        MAX = 20
        LEVEL_0 = 86
        LEVEL_1 = 71
        LEVEL_2 = 56
        LEVEL_3 = 20

    def has_battery(self):
        return True

    def __battery_levels(self):
        return [self.Battery.LEVEL_3, self.Battery.LEVEL_2, self.Battery.LEVEL_1, self.Battery.LEVEL_0]

    def __battery_nearest_level(self):
        return min(self.__battery_levels(), key=lambda l:abs(l-self.battery_power))

    @property
    def signal_strength(self):
        return self['rf_status']

    @property
    def battery_power(self):
        return self['battery_vp']

    @property
    def battery_level(self):
        return self.__battery_levels().index(self.__battery_nearest_level())

    @property
    def battery_percent(self):
        return clamp(0, (self.battery_power - self.Battery.MIN) * 100.0 / (self.Battery.MAX - self.Battery.MIN), 100)


class ControlUnit(WifiModule):
    @property
    def station_name(self):
        return self['station_name']


class Indoor(RadioModule):
    class Battery:
        MIN = 4200
        MAX = 6000
        LEVEL_0 = 5640
        LEVEL_1 = 5280
        LEVEL_2 = 4920
        LEVEL_3 = 4560


class Outdoor(RadioModule):
    class Battery:
        MIN = 3600
        MAX = 6000
        LEVEL_0 = 5500
        LEVEL_1 = 5000
        LEVEL_2 = 4500
        LEVEL_3 = 4000


class Wind(RadioModule):
    class Battery:
        MIN = 3950
        MAX = 6000
        LEVEL_0 = 5590
        LEVEL_1 = 5180
        LEVEL_2 = 4770
        LEVEL_3 = 4360


def clamp(minvalue, value, maxvalue):
    return max(minvalue, min(value, maxvalue))
