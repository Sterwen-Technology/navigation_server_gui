import datetime
import os
import sys
from argparse import ArgumentParser
import logging

# sys.path.insert(0, "../../navigation_server/src/navigation_clients")
sys.path.insert(0, "../../navigation_server/")

from guizero import App, ListBox, Text, Box, PushButton, MenuBar, Window, TextBox
from navigation_server.router_common import GrpcAccessException, GrpcClient
from control_panel import ControlPanel
from mppt_svr_window import MpptServerBox
from util_functions import format_date, format_timestamp
from nav_data import DataWindow
from network_control import NetworkWindow
from n2k_can_window import N2kCanWindow


_logger = logging.getLogger("ShipDataServer")


def _parser():
    p = ArgumentParser(description=sys.argv[0])

    p.add_argument("-p", "--port", action="store", type=int,
                   default=4502,
                   help="Console listening port, default 4502")
    p.add_argument("-a", "--address", action="store", type=str,
                   default='127.0.0.1',
                   help="IP address for Navigation server, default is localhost")
    p.add_argument("-s", "--system", action="store", type=int,
                   default=4506,
                   help="System control agent port, default 4506")
    p.add_argument("-mp", "--mppt", action="store", type=int,
                   default=4505,
                   help="MPPT server listening port, default 4505")
    p.add_argument('-dp', '--data', action='store', type=int, default=4508,
                   help="Data server port, default 4508")

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




class MainMenu:

    def __init__(self, parent):
        self._parent = parent
        self._nmea2000_window = None
        self._mppt_window = None
        self._data_window = None
        self._network_window = None
        self._menu = MenuBar(parent,
                             toplevel=['File', 'Functions'],
                             options=[
                                [['Quit', self.quit]],
                                [['NMEA2000', self.nmea2000], ['Network', self.network], ['MPPT', self.mppt], ['DATA', self.data]]
                             ])

    def quit(self):
        sys.exit(0)

    def mppt(self):
        self._mppt_window.open()

    def set_mppt_window(self, window):
        self._mppt_window = window

    def data(self):
        self._data_window.open()

    def set_data_window(self, window):
        self._data_window = window

    def network(self):
        self._network_window.open()

    def set_network_window(self, window):
        self._network_window = window

    def nmea2000(self):
        self._nmea2000_window.open()

    def set_nmea2000_window(self, window):
        self._nmea2000_window = window


def main():
    opts = Options(parser)
    server = "%s:%d" % (opts.address, opts.port)
    # logger setup => stream handler for now
    loghandler = logging.StreamHandler()
    logformat = logging.Formatter("%(asctime)s | [%(levelname)s] %(message)s")
    loghandler.setFormatter(logformat)
    _logger.addHandler(loghandler)
    _logger.setLevel(logging.INFO)


    top = App(title="Navigation router control", width=900, height=640)
    mppt_window = MpptServerBox(top, opts.address, opts.mppt)
    data_window = DataWindow(top, opts.address, opts.data)
    network_window = NetworkWindow(top, f"{opts.address}:4545")
    nmea2000_window = N2kCanWindow(top, server)
    control_panel = ControlPanel(top, opts.address, 4545)
    menu = MainMenu(top)
    menu.set_mppt_window(mppt_window)
    menu.set_data_window(data_window)
    menu.set_network_window(network_window)
    menu.set_nmea2000_window(nmea2000_window)
    top.display()


if __name__ == '__main__':
    main()
