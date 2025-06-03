
import sys
import logging
sys.path.insert(0, "../../navigation_server/")
_logger = logging.getLogger("ShipDataClient")
from guizero import Window, Text, Box, PushButton, ListBox

from navigation_server.navigation_clients import NetworkClient
from navigation_server.router_common import GrpcClient, GrpcAccessException


class NetworkWindow:

    def __init__(self, parent):
        self._server = None
        self._client = None

        self._top = Window(parent, title="Network Control", width=800)
        self._top.hide()

    def open(self, server):
        if self._server is None:
            self._server = server
            self._client = NetworkClient()
            self._server.add_service(self._client)
        if self._server.state == GrpcClient.NOT_CONNECTED:
            self._server.connect()
        # now retrieve all status and interfaces

        try:
            network_status = self._client.network_status("General")
        except GrpcAccessException:
            _logger.error("No access to network agent")
            return
        for interface in network_status.interfaces():
            print(f"Interface {interface.name} type {interface.device_type()} status {interface.status} device {interface.device_name}")
        self._top.show()
