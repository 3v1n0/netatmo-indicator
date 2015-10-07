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

class Module:
    class Type:
        MAIN = "NAMain"
        OUTDOOR = "NAModule1"
        WIND = "NAModule2"
        RAIN = "NAModule3"
        INDOOR = "NAModule4"

    class Battery:
        class Indoor:
            MIN = 4200
            MAX = 6000
            LEVEL_0 = 5640
            LEVEL_1 = 5280
            LEVEL_2 = 4920
            LEVEL_3 = 4560

        class Outdoor:
            MIN = 3600
            MAX = 6000
            LEVEL_0 = 5500
            LEVEL_1 = 5000
            LEVEL_2 = 4500
            LEVEL_3 = 4000

        class Wind:
            MIN = 3950
            MAX = 6000
            LEVEL_0 = 5590
            LEVEL_1 = 5180
            LEVEL_2 = 4770
            LEVEL_3 = 4360

    class Signal:
        class Wifi:
            LEVEL_0 = 90
            LEVEL_1 = 80
            LEVEL_2 = 70
            LEVEL_3 = 60

        class Radio:
            LEVEL_0 = 86
            LEVEL_1 = 71
            LEVEL_2 = 56
            LEVEL_3 = 20
