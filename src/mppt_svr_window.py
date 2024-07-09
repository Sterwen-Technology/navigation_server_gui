


import sys
import logging

# sys.path.insert(0, "../../navigation_server/src/navigation_clients")
sys.path.insert(0, "../../navigation_server/src")

from guizero import App, Window, Text, Box, PushButton, Drawing
from navigation_clients.mppt_client import *


_logger = logging.getLogger("ShipDataClient")


class MpptServerBox:

    def __init__(self, parent, address, port):
        self._address = "%s:%d" % (address, port)
        self._server = MPPT_Client(self._address)
        self._window = Window(parent, title="MPPT control", width=700)
        self._window.hide()
        self._proxy = None

        self._box = Box(self._window, align='top', layout='grid')
        Text(self._box, grid=[0, 0], text="Server@")
        self._addr_text = Text(self._box, grid=[1, 0], text=address)
        PushButton(self._box, grid=[3, 0], text="Close", command=self.close)
        self._state_text = Text(self._box, grid=[2, 0])
        Text(self._box, grid=[0, 1], text="Product ID")
        self._product_id = Text(self._box, grid=[1, 1], text="Unknown")
        Text(self._box, grid=[2, 1], text="Firmware")
        self._firmware = Text(self._box, grid=[3, 1], text="Unknown")
        Text(self._box, grid=[0,2], text="State")
        self._state = Text(self._box, grid=[1, 2])
        Text(self._box, grid=[2, 2], text="Error")
        self._error = Text(self._box, grid=[3, 2])
        Text(self._box, grid=[4, 2], text="MPPT")
        self._mppt = Text(self._box, grid=[5, 2])
        Text(self._box, grid=[0, 3], text="Max power today(W)")
        self._max_power = Text(self._box, grid=[1, 3])
        Text(self._box, grid=[2, 3], text="Yield today (Wh)")
        self._yield = Text(self._box, grid=[3, 3])
        Text(self._box,grid=[0, 4], text="Current values delivered")
        Text(self._box, grid=[0, 5], text="Circuit Voltage")
        self._volt = Text(self._box, grid=[1, 5])
        Text(self._box, grid=[2, 5], text="Charge (A)")
        self._amp = Text(self._box, grid=[3, 5])
        Text(self._box, grid=[4, 5], text="Power (W)")
        self._power = Text(self._box, grid=[5, 5])
        self._output = None

    def set_state(self, state):
        self._state_text.clear()
        self._state_text.append(state)

    def refresh_device(self):
        self.set_state('CONNECTED')
        self._product_id.clear()
        self._product_id.append(self._proxy.product_id)
        self._firmware.clear()
        self._firmware.append(self._proxy.firmware)
        self._state.clear()
        self._state.append(self._proxy.state)
        self._error.clear()
        self._error.append(self._proxy.error)
        self._mppt.clear()
        self._mppt.append(self._proxy.mppt_state)
        self._max_power.clear()
        self._max_power.append("%5.0f" % self._proxy.day_max_power)
        self._yield.clear()
        self._yield.append("%5.0f" % self._proxy.day_yield)

    def refresh_output(self):
        self._volt.clear()
        self._volt.append("%5.2f" % self._output.voltage)
        self._amp.clear()
        self._amp.append("%5.2f" % self._output.current)
        self._power.clear()
        self._power.append("%3.0f" % self._output.panel_power)

    def get_device(self):
        self._proxy = self._server.getDeviceInfo()
        if self._proxy is not None:
            self.refresh_device()

    def get_output(self):
        self._output = self._server.getOutput()
        if self._output is not None:
            self.refresh_output()

    def set_refresh_timers(self):
        self._box.repeat(20000, self.get_device)
        self._box.repeat(2000, self.get_output)

    def open(self):
        resp = self._server.server_status()
        if resp is not None:
            self.set_state('CONNECTED')
            self.get_device()
            self.get_output()
        else:
            self.set_state('DISCONNECTED')
        self._window.show()
        self.set_refresh_timers()

    def close(self):
        self._window.hide()
        self._box.cancel(self.get_output)
        self._box.cancel(self.get_device)
