#!/usr/bin/env python
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


from ConfigParser import ConfigParser, Error as ConfigParserError
from datetime import datetime
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Gtk, GLib
from netatmo_modules import Module, User
from threading import Lock
from xdg.BaseDirectory import xdg_config_home

import inspect
import netatmo_api_python.lnetatmo as lnetatmo
import os
import signal
import traceback
import sys

OWN_NAME = "netatmo-indicator"
CLIENT_ID = "561467a749c75fa41c8b4569"
CLIENT_SECRET = "9I859KYeqXdrwYT38hBxGiIMqh"
DEFAULT_UPDATE = 300

UNITS = {'Temperature': '°', 'Humidity': '%', 'CO2': 'ppm', 'Pressure': 'mbar',
         'AbsolutePressure': ' mbar', 'Noise': 'db', 'Rain': 'mm',
         'WindAngle': '°', 'WindStrength': 'km/h','GustAngle': '°', 'GustStrength': 'km/h' }

# See https://en.wikipedia.org/wiki/Beaufort_scale
BEAUFORT_SCALE = [{'min': 0, 'max': 1.1, 'name': "calm"},
                  {'min': 1.1, 'max': 5.5, 'name': "light air"},
                  {'min': 5.5, 'max': 11.9, 'name': "light breeze"},
                  {'min': 11.9, 'max': 19.7, 'name': "gentle breeze"},
                  {'min': 19.7, 'max': 28.7, 'name': "breeze"},
                  {'min': 28.7, 'max': 38.8, 'name': "fresh breeze"},
                  {'min': 38.8, 'max': 49.9, 'name': "strong breeze"},
                  {'min': 49.9, 'max': 61.8, 'name': "near gale"},
                  {'min': 61.8, 'max': 74.6, 'name': "gale"},
                  {'min': 74.6, 'max': 88.1, 'name': "strong gale"},
                  {'min': 88.1, 'max': 102.4, 'name': "storm"},
                  {'min': 102.4, 'max': 117.4, 'name': "violent storm"},
                  {'min': 117.4, 'max': sys.maxint, 'name': "hurricane"}]

# Workaround Ctrl+C not working with gio-gtk3
signal.signal(signal.SIGINT, signal.SIG_DFL)


class ConfigAuth(lnetatmo.ClientAuth, object):
    def __init__(self):
        config_dir = os.path.join(xdg_config_home, OWN_NAME)
        if not os.path.isdir(config_dir):
            os.mkdir(config_dir)

        self._clientId = CLIENT_ID
        self._clientSecret = CLIENT_SECRET

        self._config_lock = Lock()
        self.config_file = os.path.join(config_dir, '{}.conf'.format(OWN_NAME))
        self.config = ConfigParser()
        self.config.read(self.config_file)

        self.label_device = self.config_get_optional('interface', 'LABEL_DEVICE', '')
        self.label_sensor = self.config_get_optional('interface', 'LABEL_SENSOR', '')
        self.show_battery = self.config_get_optional('interface', 'SHOW_BATTERY', True)
        self.show_signal = self.config_get_optional('interface', 'SHOW_SIGNAL', True)

        try:
            with self._config_lock:
                self._accessToken = self.config.get('auth', 'ACCESS_TOKEN')
                self.refreshToken = self.config.get('auth', 'REFRESH_TOKEN')
                self.expiration = self.config.getint('auth', 'TOKEN_EXPIRATION')
            self.accessToken
        except:
            try:
                (account, password) = self.request_credentials()
                super(ConfigAuth, self).__init__(CLIENT_ID, CLIENT_SECRET, account, password)
                self.update_auth_config()
            except:
                print(traceback.format_exc())
                raise Exception("Impossible to connect with provided credentials")

    @property
    def accessToken(self):
        token = super(ConfigAuth, self).accessToken
        self.update_auth_config()
        return token

    def config_get_optional(self, section, parameter, default=None):
        try:
            with self._config_lock:
                return self.config.get(section, parameter)
        except:
            return default

    def update_auth_config(self):
        with self._config_lock:
            if not self.config.has_section('auth'):
                self.config.add_section('auth')

            self.config.set('auth', 'ACCESS_TOKEN', self._accessToken)
            self.config.set('auth', 'REFRESH_TOKEN', self.refreshToken)
            self.config.set('auth', 'TOKEN_EXPIRATION', self.expiration)
            with open(self.config_file, 'w') as f:
                self.config.write(f)

    def update_ui_config(self):
        with self._config_lock:
            if not self.config.has_section('interface'):
                self.config.add_section('interface')

            self.config.set('interface', 'LABEL_DEVICE', self.label_device)
            self.config.set('interface', 'LABEL_SENSOR', self.label_sensor)
            self.config.set('interface', 'SHOW_BATTERY', self.show_battery)
            self.config.set('interface', 'SHOW_SIGNAL', self.show_signal)
            with open(self.config_file, 'w') as f:
                self.config.write(f)

    def request_credentials(self):
        dialog = Gtk.Dialog("Insert your Netatmo credentials", None, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        dialog.connect("delete-event", Gtk.main_quit)
        box = Gtk.Box(spacing=10)
        dialog.get_content_area().add(box)

        def on_entry_activated(entry, dialog):
            dialog.response(Gtk.ResponseType.OK)

        account = Gtk.Entry()
        account.set_text("Account")
        account.connect("activate", on_entry_activated, dialog)
        box.pack_start(account, True, True, 0)

        password = Gtk.Entry()
        password.set_text("password")
        password.set_visibility(False)
        password.connect("activate", on_entry_activated, dialog)
        box.pack_start(password, True, True, 0)

        credentials = None
        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            credentials = [account.get_text(), password.get_text()]

        dialog.destroy()
        return credentials


class NetatmoIndicator(object):
    def __init__(self, config_auth):
        self.config_auth = config_auth
        pwd = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
        icon_path = os.path.join(pwd, '{}.png'.format(OWN_NAME))
        self.ind = appindicator.Indicator.new(OWN_NAME, icon_path, appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.update_indicator()
        GLib.timeout_add_seconds(DEFAULT_UPDATE, lambda: self.update_indicator() or True)

    def update_indicator(self):
        try:
            self.update_modules()
        except:
            print(traceback.format_exc())

        self.update_user()
        self.update_label()
        self.populate_menu()

    def add_module_data_if_valid(self, module_data, max_age=3600):
        try:
            module = Module.factory(module_data)
            if module and module.age < max_age:
                 self.modules.append(module)
        except:
            print(traceback.format_exc())

    def update_modules(self):
        self.modules = []
        devices = lnetatmo.DeviceList(self.config_auth)
        for name, station in devices.stations.items():
            self.add_module_data_if_valid(station)
            for m in station['modules']:
                self.add_module_data_if_valid(devices.modules[m])

    def update_user(self):
        try:
            self.user = User(lnetatmo.User(self.config_auth).rawData)
            self.units = UNITS.copy()

            pressure_unit = self.units['Pressure']
            wind_unit = self.units['WindStrength']

            if self.user.wind_unit == User.WindUnit.MPH:
                wind_unit = 'mph'
            elif self.user.wind_unit == User.WindUnit.MS:
                wind_unit = 'ms'
            elif self.user.wind_unit == User.WindUnit.BEAUFORT:
                wind_unit = ''
            elif self.user.wind_unit == User.WindUnit.KNOT:
                wind_unit = 'knot'

            if self.user.pressure_unit == User.PressureUnit.INHG:
                pressure_unit = 'inhg'
            elif self.user.pressure_unit == User.PressureUnit.MMHG:
                pressure_unit = 'mmhg'

            self.units['Pressure'] = pressure_unit
            self.units['AbsolutePressure'] = pressure_unit
            self.units['Rain'] = 'mm' if self.user.units == User.Units.SI else 'in'
            self.units['WindStrength'] = wind_unit
            self.units['GustStrength'] = wind_unit

            for sensor, unit in self.units.items():
                unit = self.units[sensor]
                self.units[sensor] = (" {}").format(unit) if unit not in ['°', '%'] else unit
        except:
            print(traceback.format_exc())

    def update_label(self):
        self.set_label('')
        try:
            assert(len(self.config_auth.label_device))
            assert(len(self.config_auth.label_sensor))
            for module in self.modules:
                if module.id == self.config_auth.label_device:
                    sensor = self.config_auth.label_sensor
                    value = module.dashboard[sensor]
                    self.set_label(self.get_value_unit_label(sensor, value))
        except:
            for module in self.modules:
                if 'Temperature' in module.sensors:
                    value = module.dashboard['Temperature']
                    self.set_label(self.get_value_unit_label(sensor, value))

                if module.type == Module.Type.OUTDOOR:
                    break

    def set_label(self, label):
        self.ind.set_label(str(label), "")

    def get_value_unit_label(self, sensor, value, fallback='—'):
        unit = self.units[sensor] if sensor in self.units.keys() else ''
        value = self.get_value_for_unit(sensor, value)
        if not value or isinstance(value, str):
            return "{}{}".format(value or fallback, unit)
        return "{:1g}{}".format(float("{:.1f}".format(value)), unit)

    def get_value_for_unit(self, sensor, value):
        if not value:
            return None
        if sensor == 'Temperature':
            if self.user.units == User.Units.IMPERIAL:
                return (value * 1.8) + 32
        if sensor == 'Rain':
            if self.user.units == User.Units.IMPERIAL:
                return value / 2.54
        if sensor in ('WindStrength', 'GustStrength'):
            if self.user.wind_unit == User.WindUnit.MPH:
                return value / 1.609344
            if self.user.wind_unit == User.WindUnit.MS:
                return value / 3.6
            if self.user.wind_unit == User.WindUnit.BEAUFORT:
                for level in BEAUFORT_SCALE:
                    if value >= level['min'] and value < level['max']:
                        return level['name']
            if self.user.wind_unit == User.WindUnit.KNOT:
                return value / 1.852
        if sensor == 'Pressure':
            if self.user.pressure_unit == User.PressureUnit.INHG:
                return value / 33.8639
            if self.user.pressure_unit == User.PressureUnit.MMHG:
                return value / 1.33322

        return value

    def populate_menu(self):
        self.menu = Gtk.Menu()
        self.ind.set_menu(self.menu)

        for module in self.modules:
            self.add_module_to_menu(module)
            self.menu.append(Gtk.SeparatorMenuItem.new())

        if not len(self.menu.get_children()):
            it = Gtk.MenuItem("Impossible to fetch data, check your connection or auth")
            it.set_sensitive(False)
            self.menu.append(it)
            self.menu.append(Gtk.SeparatorMenuItem.new())

        it = Gtk.MenuItem("Open web dashboard")
        it.connect('activate', lambda i: os.system("xdg-open https://my.netatmo.com"))
        self.menu.append(it)
        self.menu.show_all()

    def add_module_to_menu(self, module, max_time=3600):
        it = Gtk.MenuItem(module.name)
        it.set_sensitive(False)
        self.menu.append(it)

        for sensor, value in module.get_sensors_data().items():
            value_label = self.get_value_unit_label(sensor, value, fallback='…')
            item = Gtk.MenuItem("  {}: {}".format(sensor, value_label))
            item.connect('activate', self.on_sensor_item_activated, module.id, sensor)
            self.menu.append(item)

        if self.config_auth.show_signal:
            item = Gtk.ImageMenuItem.new_with_label("Signal: ~{:.1f}%".format(module.signal_percent))
            item.set_image(Gtk.Image.new_from_icon_name('nm-signal-{:d}'.format((module.signal_level+1) * 25), Gtk.IconSize.MENU))
            item.set_always_show_image(True)
            item.set_sensitive(False)
            self.menu.append(item)

        if self.config_auth.show_battery and module.has_battery():
            item = Gtk.ImageMenuItem.new_with_label("Battery: {:.1f}%".format(module.battery_percent))
            icon_level = min(range(0, 101, 20), key=lambda l:abs(l-module.battery_percent))
            item.set_image(Gtk.Image.new_from_icon_name('battery-{:03d}'.format(icon_level), Gtk.IconSize.MENU))
            item.set_always_show_image(True)
            item.set_sensitive(False)
            self.menu.append(item)

    def on_sensor_item_activated(self, item, module_id, sensor):
        self.config_auth.label_device = module_id
        self.config_auth.label_sensor = sensor
        self.config_auth.update_ui_config()
        self.update_label()

if __name__ == "__main__":
    ind = NetatmoIndicator(ConfigAuth())
    Gtk.main()
