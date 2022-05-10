

import os
import sys
from argparse import ArgumentParser

sys.path.insert(0, "../../navigation_server/src")

from guizero import App, ListBox, Text, Box, PushButton
from console_client import *


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

    def __init__(self, parent):
        self._box = Box(parent, layout='grid', visible=False)
        Text(self._box, grid=[0, 0], text='Name:')
        self._name = Text(self._box, grid=[1,0])
        Text(self._box, grid=[2,0], text='States:')
        self._state = Text(self._box, grid=[3,0])
        self._dev_state = Text(self._box, grid=[4,0])
        Text(self._box, grid=[0, 1], text="Protocol:")
        self._protocol = Text(self._box, grid=[1,1])
        Text(self._box, grid=[0, 2], text="Messages received:")
        self._msg_in = Text(self._box, grid=[1, 2])
        Text(self._box, grid=[0,3], text='Messages sent')
        self._msg_out = Text(self._box, grid=[1, 3])
        self._action = PushButton(self._box, grid=[0,4], command=self.action)
        self._inst_list = {}

    def display(self, instrument_name):
        instrument = self._inst_list[instrument_name]
        self._name.clear()
        self._name.append(instrument.name)
        self._state.clear()
        self._state.append(instrument.state)
        self._dev_state.clear()
        self._dev_state.append(instrument.dev_state)
        self._protocol.clear()
        self._protocol.append(instrument.protocol)
        self._msg_in.clear()
        self._msg_in.append(str(instrument.msg_in))
        self._msg_out.clear()
        self._msg_out.append(str(instrument.msg_out))
        if instrument.state == 'RUNNING':
            self._action.text = 'Stop'
        else:
            self._action.text = 'Start'
        self._box.visible = True

    def add_instrument(self, instrument):
        self._inst_list[instrument.name] = instrument

    def action(self):
        pass


def main():
    opts = Options(parser)
    server = "%s:%d" % (opts.address, opts.port)
    console = ConsoleClient(server)
    top = App(title="Navigation router control")
    box = Box(top, align='left')
    ti = Text(box, align='top', text='Instruments')
    # instr_lists = ListBox(box, align='top')
    inst_box = InstrumentBox(top)
    instr_lists = ListBox(box, align='top', command=inst_box.display)
    instr = console.get_instruments()
    for i in instr:
        instr_lists.append(i.name)
        inst_box.add_instrument(i)

    top.display()


if __name__ == '__main__':
    main()
