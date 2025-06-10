import datetime
import os
import sys
from argparse import ArgumentParser
import logging

# sys.path.insert(0, "../../navigation_server/src/navigation_clients")
sys.path.insert(0, "../../navigation_server/")

from guizero import App, ListBox, Text, Box, PushButton, MenuBar, Window, TextBox
from navigation_server.router_common import GrpcAccessException, GrpcClient, AgentClient
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
                   default=4545,
                   help="Console listening port, default 4545")
    p.add_argument("-a", "--address", action="store", type=str,
                   default='127.0.0.1',
                   help="IP address for Navigation server, default is localhost")

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


global_variables = {}


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

    def get_connection_parameters(self, process_name) -> (str, int):
        agent = global_variables['agent']
        port = agent.get_port(process_name)
        return global_variables['address'], port

    def quit(self):
        sys.exit(0)

    def mppt(self):
        if self._mppt_window is None:
            self._mppt_window = MpptServerBox(self._parent)
        address, port = self.get_connection_parameters('Energy')
        if port > 0:
            self._mppt_window.open(address, port)

    def set_mppt_window(self, window):
        self._mppt_window = window

    def data(self):
        if self._data_window is None:
            self._data_window = DataWindow(self._parent)
        address, port = self.get_connection_parameters('Data')
        if port > 0:
            self._data_window.open(address, port)

    def set_data_window(self, window):
        self._data_window = window

    def network(self):
        if self._network_window is None:
            self._network_window = NetworkWindow(self._parent)
        agent = global_variables['agent']
        self._network_window.open(agent.server)

    def set_network_window(self, window):
        self._network_window = window

    def nmea2000(self):
        if self._nmea2000_window is None:
            self._nmea2000_window = N2kCanWindow(self._parent)
        address, port = self.get_connection_parameters('STNC_CAN_Server')
        if port > 0 :
            self._nmea2000_window.open(address, port)

    def set_nmea2000_window(self, window):
        self._nmea2000_window = window


def main():
    opts = Options(parser)
    # logger setup => stream handler for now
    loghandler = logging.StreamHandler()
    logformat = logging.Formatter("%(asctime)s | [%(levelname)s] %(message)s")
    loghandler.setFormatter(logformat)
    _logger.addHandler(loghandler)
    _logger.setLevel(logging.INFO)

    if opts.address is not None:
        global_variables['address'] = opts.address

    top = App(title="Navigation router control", width=900, height=640)
    navigation_agent_server = GrpcClient.get_client(f"{opts.address}:{opts.port}")
    agent = AgentClient()
    global_variables['agent'] = agent
    navigation_agent_server.add_service(agent)
    navigation_agent_server.connect()
    if not navigation_agent_server.wait_connect(10.):
        # if no response from the agent server, let's give up
        _logger.error("No agent available")
        return

    menu = MainMenu(top)
    control_panel = ControlPanel(top, agent, opts.address)

    top.display()


if __name__ == '__main__':
    main()
