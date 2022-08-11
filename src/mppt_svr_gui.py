

import os
import sys
from argparse import ArgumentParser
import logging

# sys.path.insert(0, "../../navigation_server/src/navigation_clients")
sys.path.insert(0, "../../navigation_server/src")

from guizero import App, ListBox, Text, Box, PushButton
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
        # self._proxy = console.server_status()
        self._box = Box(parent, align='top', layout='grid')
        Text(self._box, grid=[0, 0], text="Server@")
        self._addr_text = Text(self._box, grid=[1, 0], text=address)
        self._state_text = Text(self._box, grid=[2, 0])

    def set_state(self, state):
        self._state_text.clear()
        self._state_text.append(state)


def main():
    opts = Options(parser)
    server = "%s:%d" % (opts.address, opts.port)
    # logger setup => stream handler for now
    loghandler = logging.StreamHandler()
    logformat = logging.Formatter("%(asctime)s | [%(levelname)s] %(message)s")
    loghandler.setFormatter(logformat)
    _logger.addHandler(loghandler)
    _logger.setLevel(logging.INFO)

    mppt_svr = MPPT_Client(opts)
    top = App(title="MPPT control")
    server_box = ServerBox(top, server, mppt_svr)
    resp = mppt_svr.server_status()
    if resp is not None:
        server_box.set_state('CONNECTED')

    top.display()


if __name__ == '__main__':
    main()
