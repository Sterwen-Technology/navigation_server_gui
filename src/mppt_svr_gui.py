

import os
import sys
from argparse import ArgumentParser
import logging

# sys.path.insert(0, "../../navigation_server/src/navigation_clients")
sys.path.insert(0, "../../navigation_server/src")

from guizero import App, ListBox, Text, Box, PushButton, Drawing
from victron_mppt.mppt_client import *


_logger = logging.getLogger("MPPTDataClient")


def _parser():
    p = ArgumentParser(description=sys.argv[0])

    p.add_argument("-p", "--port", action="store", type=int,
                   default=4505,
                   help="MPPT server listening port, default 4505")
    p.add_argument("-a", "--address", action="store", type=str,
                   default='127.0.0.1',
                   help="IP address for MPPT server, default is localhost")

    return p


parser = _parser()


class Options(object):
    def __init__(self, p):
        self.parser = p
        self.options = None

    def __getattr__(self, name):
        if self.options is None:
            self.options = self.parser.parse_args()
        try:
            return getattr(self.options, name)
        except AttributeError:
            raise AttributeError(name)


class ServerBox:

    def __init__(self, parent, address, mppt_svr):
        self._address = address
        self._server = mppt_svr

        self._box = Box(parent, align='top', layout='grid')
        Text(self._box, grid=[0, 0], text="Server@")
        self._addr_text = Text(self._box, grid=[1, 0], text=address)
        self._state_text = Text(self._box, grid=[2, 0])
        self._proxy = mppt_svr.getDeviceInfo()
        if self._proxy is None:
            return
        Text(self._box, grid=[0, 1], text="Product ID")
        Text(self._box, grid=[1, 1], text=self._proxy.product_id)
        Text(self._box, grid=[2, 1], text="Firmware")
        Text(self._box, grid=[3, 1], text=self._proxy.firmware)
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
        self._state.clear()
        self._state.append(self._proxy.state)
        self._error.clear()
        self._error.append(self._proxy.error)
        self._mppt.clear()
        self._mppt.append(self._proxy.mppt_state)
        self._max_power.clear()
        self._max_power.append("%5.0f" % self._proxy.day_max_power)
        self._yield.clear()
        self._yield.append("%5.0f" % self._proxy.day_power)

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


def main():
    opts = Options(parser)
    server = "%s:%d" % (opts.address, opts.port)
    # logger setup => stream handler for now
    loghandler = logging.StreamHandler()
    logformat = logging.Formatter("%(asctime)s | [%(levelname)s] %(message)s")
    loghandler.setFormatter(logformat)
    _logger.addHandler(loghandler)
    _logger.setLevel(logging.DEBUG)

    mppt_svr = MPPT_Client(opts)
    top = App(title="MPPT control")
    top.resize(700, 500)
    container = Box(top)
    server_box = ServerBox(container, server, mppt_svr)
    power_curve = Drawing(container, align='bottom', height=200, width='fill')
    power_curve.bg = 'blue'
    resp = mppt_svr.server_status()
    if resp is not None:
        server_box.set_state('CONNECTED')
        server_box.refresh_device()
    else:
        return
    server_box.set_refresh_timers()
    top.display()


if __name__ == '__main__':
    main()
