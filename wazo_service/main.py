#!/usr/bin/env python3
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import argparse
import dbus

# D-BUS doc: https://www.freedesktop.org/wiki/Software/systemd/dbus/


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
        return unit_properties.Get('org.freedesktop.systemd1.Unit', 'SubState')


def status(service_group):
    print('Checking services...')
    for service in service_group:
        print('\t{status}\t\t{name}'.format(status=service.status(), name=service.name))


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('action', help='Available actions: status')
    parser.add_argument('service_group_name', default='xivo', nargs='?', help='Available groups: xivo')
    args = parser.parse_args()

    service_group = SERVICE_GROUPS[args.service_group_name]
    ACTIONS[args.action](service_group)


ACTIONS = {'status': status}
SERVICE_GROUPS = {'xivo': [Service('xivo-call-logs')]}


if __name__ == '__main__':
    main()
