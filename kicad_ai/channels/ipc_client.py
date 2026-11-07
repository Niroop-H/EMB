# SPDX-License-Identifier: GPL-3.0-or-later
"""Retired JSON-over-TCP prototype; use the native local CLI adapter instead."""
class KiCadIPCClient:
    def __init__(self, host='127.0.0.1', port=4242):
        self.connected = False

    def connect(self):
        return False

    def send_command(self, command_type, payload):
        return {'status': 'error', 'message': 'Legacy TCP transport is disabled. Use native KiCad automation.'}

    def reload_schematic(self, sch_file):
        return self.send_command('RELOAD_SCHEMATIC', {'path': sch_file})

    def reload_board(self, pcb_file):
        return self.send_command('RELOAD_BOARD', {'path': pcb_file})

    def highlight_net(self, net_name):
        return self.send_command('HIGHLIGHT_NET', {'net': net_name})

    def close(self):
        self.connected = False
