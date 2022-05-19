

import os
import sys
from argparse import ArgumentParser
import logging

sys.path.insert(0, "../../navigation_server/src")

from guizero import App, ListBox, Text, Box, PushButton
from console_client import *


_logger = logging.getLogger("ShipDataClient")


def _parser():
    p = ArgumentParser(description=sys.argv[0])

    p.add_argument("-p", "--port", action="store", type=int,
                   default=4502,
                   help="Console listening port, default 4502")
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


class InstrumentBox:

    def __init__(self, parent, pos, client):
        self._client = client
        self._instrument = None
        self._box = Box(parent, grid=pos, layout='grid', visible=False)
        Text(self._box, grid=[0, 0], text='Name:')
        self._name = Text(self._box, grid=[1,0])
        Text(self._box, grid=[2,0], text='State:')
        self._state = Text(self._box, grid=[3,0])
        self._dev_state = Text(self._box, grid=[4,0])
        Text(self._box, grid=[0, 1], text="Protocol:")
        self._protocol = Text(self._box, grid=[1,1])
        Text(self._box, grid=[0, 2], text="Messages received:")
        self._msg_in = Text(self._box, grid=[1, 2])
        Text(self._box, grid=[0,3], text='Messages sent')
        self._msg_out = Text(self._box, grid=[1, 3])
        self._action = PushButton(self._box, grid=[0,4], command=self.action)
        self._refresh = PushButton(self._box, grid=[1, 4], command=self.refresh, text='Refresh')

    def set_instrument(self, instrument):
        self._instrument = instrument
        self.display()

    def display(self):
        self._name.clear()
        self._name.append(self._instrument.name)
        self._state.clear()
        self._state.append(self._instrument.state)
        self._dev_state.clear()
        self._dev_state.append(self._instrument.dev_state)
        self._protocol.clear()
        self._protocol.append(self._instrument.protocol)
        self._msg_in.clear()
        self._msg_in.append(str(self._instrument.msg_in))
        self._msg_out.clear()
        self._msg_out.append(str(self._instrument.msg_out))
        if self._instrument.state == 'RUNNING':
            self._action.text = 'Stop'
        else:
            self._action.text = 'Start'
        self._box.visible = True

    def refresh(self):
        inst = self._client.get_instrument(self._instrument.name)
        if inst is not None:
            self._instrument = inst
            self.display()

    def action(self):
        if self._action.text == 'Stop':
            self._instrument.stop(self._client)
        else:
            self._instrument.start(self._client)
        self.refresh()


class InstrumentListBox:

    def __init__(self, parent, pos, inst_box: InstrumentBox):
        self._inst_box = inst_box
        self._box = Box(parent, grid=pos, align='top')
        Text(self._box, align='top', text='Instruments')
        self._instr_list = ListBox(self._box, align='top', command=self.select)
        self._instruments = {}

    def set_instruments(self, instr):
        for i in instr:
            self._instr_list.append(i.name)
            self._instruments[i.name] = i

    def select(self, name):
        self._inst_box.set_instrument(self._instruments[name])


class ServerBox:

    def __init__(self, parent, address, server):
        self._address = address
        self._server = server
        self._box = Box(parent, align='top', layout='grid')
        Text(self._box, grid=[0, 0], text="Server@")
        self._addr_text = Text(self._box, grid=[1, 0], text=address)
        self._state_text = Text(self._box, grid=[2, 0])
        PushButton(self._box, grid=[0, 1], text='Stop', command=self.stop_server)
        self._status = Text(self._box, grid=[1, 1])

    def set_address(self, address):
        self._address = address
        self._addr_text.clear()
        self._addr_text.append(address)

    def set_state(self, state):
        self._state_text.clear()
        self._state_text.append(state)

    def stop_server(self):
        self._server.server_cmd('stop')


def main():
    opts = Options(parser)
    server = "%s:%d" % (opts.address, opts.port)
    # logger setup => stream handler for now
    loghandler = logging.StreamHandler()
    logformat = logging.Formatter("%(asctime)s | [%(levelname)s] %(message)s")
    loghandler.setFormatter(logformat)
    _logger.addHandler(loghandler)
    _logger.setLevel(logging.INFO)

    console = ConsoleClient(server)
    top = App(title="Navigation router control")
    server_box = ServerBox(top, server, console)
    inst_wbox = Box(top, align='left', layout='grid')
    inst_box = InstrumentBox(inst_wbox, [1, 0], console)
    instr_list = InstrumentListBox(inst_wbox, [0, 0], inst_box)
    resp = console.server_status()
    if resp is not None:
        server_box.set_state('CONNECTED')
    instruments = console.get_instruments()
    if instruments is not None:
        instr_list.set_instruments(instruments)

    top.display()


if __name__ == '__main__':
    main()
