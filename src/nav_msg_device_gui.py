import sys
import logging

# sys.path.insert(0, "../../navigation_server/src/navigation_clients")
sys.path.insert(0, "../../navigation_server/src")

from guizero import App, Window, Text, Box, PushButton, Drawing


_logger = logging.getLogger("ShipDataClient")


class DeviceDetailsWindow:

    def __init__(self, parent, device, client):
        self._device = device
        self._client = client
        self._window = Window(parent, title=f'Details for device address {device.address}')
        self._window.hide()
        


