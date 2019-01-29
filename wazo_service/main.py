#!/usr/bin/env python
# Copyright 2017-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import print_function

import argparse
import dbus
import os
import subprocess
import sys
import traceback

import xivo_db.bin.check_db

ALL_RUNNING = 0
SOME_STOPPED = 1
SOME_FAILED = 2


class Service(object):
    def __init__(self, name):
        self.name = name
        self.service_name = name
        self.unit_name = name

    def status(self):
        try:
            sysbus = dbus.SystemBus()
            systemd1 = sysbus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
            manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')
        except dbus.DBusException:
            return self.status_without_systemd()

        try:
            unit_path = manager.GetUnit('{}.service'.format(self.unit_name))
        except dbus.DBusException:
            return 'unknown'

        unit = sysbus.get_object('org.freedesktop.systemd1', unit_path)
        unit_properties = dbus.Interface(unit, dbus_interface='org.freedesktop.DBus.Properties')
        status = unit_properties.Get('org.freedesktop.systemd1.Unit', 'ActiveState')
        return self.translate_status(status)

    def status_without_systemd(self):
        with open(os.devnull, 'w') as devnull:
            return_code = subprocess.call(['service', self.service_name, 'status'], stdout=devnull)

        if return_code == 0:
            return 'running'
        if return_code == 3:
            return 'stopped'
        return 'unknown'

    @staticmethod
    def translate_status(status):
        if status == 'active':
            return 'running'
        if status == 'failed':
            return 'failed'
        return 'stopped'


class PostgresService(Service):

    def __init__(self):
        self.name = 'postgresql'
        self.unit_name = 'postgresql@9.6-main'
        self.service_name = 'postgresql'

    def status_without_systemd(self):
        return_code = subprocess.call(['wazo-pg-is-running'])

        if return_code == 0:
            return 'running'
        return 'stopped'


def status(service_group):
    try:
        xivo_db.bin.check_db.main()
    except Exception:
        traceback.print_exc()

    names = [service.name for service in service_group]
    statuses = [service.status() for service in service_group]

    print('Checking services...')
    for name, status in zip(names, statuses):
        print('\t{status}\t\t{name}'.format(status=status, name=name))

    if 'stopped' in statuses:
        return SOME_STOPPED
    if 'failed' in statuses:
        return SOME_FAILED

    return ALL_RUNNING


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('action', help='Available actions: status')
    parser.add_argument('service_group_name', default='default', nargs='?',
                        help='Available groups: all, default, xivo')
    args = parser.parse_args()

    service_group = SERVICE_GROUPS[args.service_group_name]
    status_code = ACTIONS[args.action](service_group)

    sys.exit(status_code)


ACTIONS = {'status': status}
SERVICE_GROUPS = {}
SERVICE_GROUPS['xivo'] = [
    Service('wazo-call-logd'),
    Service('xivo-dxtora'),
    Service('xivo-provd'),
    Service('xivo-agid'),
    Service('asterisk'),
    Service('xivo-amid'),
    Service('xivo-agentd'),
    Service('xivo-ctid'),
    Service('wazo-dird'),
    Service('xivo-dird-phoned'),
    Service('xivo-ctid-ng'),
    Service('xivo-websocketd'),
    Service('wazo-chatd'),
]
SERVICE_GROUPS['default'] = [
    Service('dahdi'),
    Service('wazo-plugind'),
    Service('wazo-webhookd'),
    Service('xivo-sysconfd'),
    Service('xivo-confgend'),
    Service('xivo-confd'),
    Service('wazo-auth')
] + SERVICE_GROUPS['xivo']
SERVICE_GROUPS['all'] = [
    Service('rabbitmq-server'),
    Service('consul'),
    PostgresService(),
    Service('nginx'),
    Service('mongooseim'),
] + SERVICE_GROUPS['default']


if __name__ == '__main__':
    main()
