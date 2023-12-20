#!/usr/bin/env python3
# Copyright 2017-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Iterable

import dbus
import xivo_db.check_db

ALL_RUNNING = 0
SOME_STOPPED = 1
SOME_FAILED = 2


class Service:
    def __init__(self, name: str, unit_name: str | None = None) -> None:
        self.name = name
        self.service_name = name
        self.unit_name = unit_name or name

    def status(self) -> str:
        sysbus = dbus.SystemBus()
        systemd1 = sysbus.get_object(
            'org.freedesktop.systemd1', '/org/freedesktop/systemd1'
        )
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')

        try:
            unit_path = manager.GetUnit(f'{self.unit_name}.service')
        except dbus.DBusException:
            return 'unknown'

        unit = sysbus.get_object('org.freedesktop.systemd1', unit_path)
        unit_properties = dbus.Interface(
            unit, dbus_interface='org.freedesktop.DBus.Properties'
        )
        state = unit_properties.Get('org.freedesktop.systemd1.Unit', 'ActiveState')
        return self.translate_status(state)

    @staticmethod
    def translate_status(status: str) -> str:
        if status == 'active':
            return 'running'
        if status == 'failed':
            return 'failed'
        return 'stopped'


class PostgresService(Service):
    def __init__(self) -> None:
        super().__init__('postgresql', unit_name='postgresql@13-main')


def status(service_group: Iterable[Service]) -> int:
    try:
        xivo_db.check_db.main()
    except Exception:
        traceback.print_exc()

    names = [service.name for service in service_group]
    statuses = [service.status() for service in service_group]

    print('Checking services...')
    for name, status in zip(names, statuses):
        print(f'\t{status}\t\t{name}')

    if 'stopped' in statuses:
        return SOME_STOPPED
    if 'failed' in statuses:
        return SOME_FAILED

    return ALL_RUNNING


def main() -> None:
    parser = argparse.ArgumentParser(description='Manage Wazo Services')
    parser.add_argument('action', choices=list(ACTIONS), help='Action to perform')
    parser.add_argument(
        'service_group_name',
        default='default',
        nargs='?',
        help='Filter by service group',
        choices=list(SERVICE_GROUPS),
    )
    args = parser.parse_args()
    service_group = SERVICE_GROUPS[args.service_group_name]
    status_code = ACTIONS[args.action](service_group)

    sys.exit(status_code)


ACTIONS = {'status': status}
WAZO_SERVICES = [
    Service('wazo-call-logd'),
    Service('wazo-dxtora'),
    Service('wazo-provd'),
    Service('wazo-agid'),
    Service('asterisk'),
    Service('wazo-amid'),
    Service('wazo-agentd'),
    Service('wazo-dird'),
    Service('wazo-phoned'),
    Service('wazo-calld'),
    Service('wazo-websocketd'),
    Service('wazo-chatd'),
]
DEFAULT_SERVICES = [
    Service('wazo-plugind'),
    Service('wazo-webhookd'),
    Service('wazo-sysconfd'),
    Service('wazo-confgend'),
    Service('wazo-confd'),
    Service('wazo-auth'),
] + WAZO_SERVICES

ALL_SERVICES = [
    Service('rabbitmq-server'),
    PostgresService(),
    Service('nginx'),
] + DEFAULT_SERVICES

SERVICE_GROUPS = {
    'wazo': WAZO_SERVICES,
    'default': DEFAULT_SERVICES,
    'all': ALL_SERVICES,
}


if __name__ == '__main__':
    main()
