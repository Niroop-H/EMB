"""
KiCad IPC Channel Client.
Communicates with running KiCad instances via local sockets / named pipes using KiCad's Protobuf API (`kiapi`).
"""

import socket
import os
import sys
import json
from typing import Dict, Any, Optional

class KiCadIPCClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 4242):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.connected = False

    def connect(self) -> bool:
        """Attempts connection to KiCad's API IPC server."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0)
            self.sock.connect((self.host, self.port))
            self.connected = True
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            self.connected = False
            return False

    def send_command(self, command_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sends an API command envelope to KiCad."""
        if not self.connected:
            if not self.connect():
                return {"status": "error", "message": "KiCad IPC server is not running or unreachable"}

        message = {
            "type": command_type,
            "payload": payload
        }
        data = json.dumps(message).encode("utf-8") + b"\n"
        
        try:
            self.sock.sendall(data)
            resp_data = self.sock.recv(4096)
            return json.loads(resp_data.decode("utf-8"))
        except Exception as e:
            self.connected = False
            return {"status": "error", "message": str(e)}

    def reload_schematic(self, sch_file: str) -> Dict[str, Any]:
        return self.send_command("RELOAD_SCHEMATIC", {"path": sch_file})

    def reload_board(self, pcb_file: str) -> Dict[str, Any]:
        return self.send_command("RELOAD_BOARD", {"path": pcb_file})

    def highlight_net(self, net_name: str) -> Dict[str, Any]:
        return self.send_command("HIGHLIGHT_NET", {"net": net_name})

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.connected = False
