#!/usr/bin/env python3
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import argparse
import dbus
import sys

ALL_RUNNING = 0
SOME_STOPPED = 1
SOME_FAILED = 2


class Service:
    def __init__(self, name):
        self.name = name

    def status(self):
        sysbus = dbus.SystemBus()
        systemd1 = sysbus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')
        unit_path = manager.GetUnit('{}.service'.format(self.name))
        unit = sysbus.get_object('org.freedesktop.systemd1', unit_path)
        unit_properties = dbus.Interface(unit, dbus_interface='org.freedesktop.DBus.Properties')
        status = unit_properties.Get('org.freedesktop.systemd1.Unit', 'SubState')
        return self.translate_status(status)

    @staticmethod
    def translate_status(status):
        if status == 'running':
            return 'running'
        elif status == 'failed':
            return 'failed'
        else:
            return 'stopped'


def status(service_group):
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
    parser.add_argument('service_group_name', default='default', nargs='?', help='Available groups: xivo')
    args = parser.parse_args()

    service_group = SERVICE_GROUPS[args.service_group_name]
    status_code = ACTIONS[args.action](service_group)

    sys.exit(status_code)


ACTIONS = {'status': status}
SERVICE_GROUPS = {'default': [Service('xivo-call-logs'),
                              Service('xivo-dxtora'),
                              Service('xivo-provd'),
                              Service('xivo-agid'),
                              Service('asterisk'),
                              Service('xivo-amid'),
                              Service('xivo-call-logs'),
                              Service('xivo-agentd'),
                              Service('xivo-ctid'),
                              Service('xivo-dird'),
                              Service('xivo-dird-phoned'),
                              Service('xivo-ctid-ng'),
                              Service('xivo-websocketd')]}


if __name__ == '__main__':
    main()
