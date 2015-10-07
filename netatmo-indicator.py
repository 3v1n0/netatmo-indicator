#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Marco Trevisan
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


from ConfigParser import ConfigParser
from ConfigParser import Error as ConfigParserError
from gi.repository import Gtk
from gi.repository import AppIndicator3 as appindicator
from xdg.BaseDirectory import xdg_config_home

import netatmo_api_python.lnetatmo as lnetatmo
import os
import signal

CLIENT_ID = "561467a749c75fa41c8b4569"
CLIENT_SECRET = "9I859KYeqXdrwYT38hBxGiIMqh"

# Workaround Ctrl+C not working with gio-gtk3
signal.signal(signal.SIGINT, signal.SIG_DFL)

class ConfigAuth(lnetatmo.ClientAuth, object):
    def __init__(self):
        config_dir = os.path.join(xdg_config_home, "indicator-netatmo")
        print config_dir
        if not os.path.isdir(config_dir):
            os.mkdir(config_dir)

        self._clientId = CLIENT_ID
        self._clientSecret = CLIENT_SECRET

        self.config_file = os.path.join(config_dir, "indicator-netatmo.conf")
        self.config = ConfigParser()
        self.config.read(self.config_file)

        try:
            self._accessToken = self.config.get('auth', 'ACCESS_TOKEN')
            self.refreshToken = self.config.get('auth', 'REFRESH_TOKEN')
            self.expiration = self.config.get('auth', 'TOKEN_EXPIRATION')
            self.accessToken
        except:
            try:
                (account, password) = self.request_credentials()
                super(ConfigAuth, self).__init__(CLIENT_ID, CLIENT_SECRET, account, password)
                self.update_auth_config()
            except:
                raise Exception("Impossible to connect with provided credentials")

    @property
    def accessToken(self):
        token = super(ConfigAuth, self).accessToken
        self.update_auth_config()
        print("Get Token ",token)
        return token

    def update_auth_config(self):
        print("Updating config ",self._accessToken)
        if not self.config.has_section('auth'):
            self.config.add_section('auth')

        self.config.set('auth', 'ACCESS_TOKEN', self._accessToken)
        self.config.set('auth', 'REFRESH_TOKEN', self.refreshToken)
        self.config.set('auth', 'TOKEN_EXPIRATION', self.expiration)
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def request_credentials(self):
        dialog = Gtk.Dialog("Insert your Netatmo credentials", None, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        dialog.connect("delete-event", Gtk.main_quit)

        label = Gtk.Label("This is a dialog to display additional information")

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
