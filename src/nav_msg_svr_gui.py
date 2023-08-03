import datetime
import os
import sys
from argparse import ArgumentParser
import logging

# sys.path.insert(0, "../../navigation_server/src/navigation_clients")
sys.path.insert(0, "../../navigation_server/src")

from guizero import App, ListBox, Text, Box, PushButton, MenuBar, Window, TextBox
from navigation_clients.console_client import *
from control_panel import ControlPanel
from mppt_svr_window import MpptServerBox
from util_functions import format_date


_logger = logging.getLogger("ShipDataClient")


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


class CouplerBox:

    def __init__(self, parent, pos, client):
        self._client = client
        self._coupler = None
        self._disabled = True
        self._parent = parent
        self._box = Box(parent, grid=pos, layout='grid', visible=False)
        Text(self._box, grid=[0, 0], text='Name:')
        self._name = Text(self._box, grid=[1 ,0])
        Text(self._box, grid=[2 ,0], text='State:')
        self._state = Text(self._box, grid=[3 ,0])
        self._dev_state = Text(self._box, grid=[4 ,0])
        Text(self._box, grid=[0, 1], text="Protocol:")
        self._protocol = Text(self._box, grid=[1 ,1])
        Text(self._box, grid=[0, 2], text="Messages received:")
        self._msg_in = Text(self._box, grid=[1, 2])
        Text(self._box, grid=[2, 2], text='Rate(msg/s)')
        self._msg_in_rate = Text(self._box, grid=[3, 2])
        Text(self._box, grid=[0, 3], text='Messages sent')
        self._msg_out = Text(self._box, grid=[1, 3])
        Text(self._box, grid=[2, 3], text='Rate(msg/s)')
        self._msg_out_rate = Text(self._box, grid=[3, 3])
        self._action = PushButton(self._box, grid=[0, 4], command=self.action)
        self._suspend_resume = PushButton(self._box, grid=[1, 4], command=self.action2)
        self._refresh = PushButton(self._box, grid=[2, 4], command=self.refresh, text='Refresh')
        self._start_trace = PushButton(self._box, grid=[3,4], command=self.start_trace, text='Start Trace')
        self._stop_trace = PushButton(self._box, grid=[5,4], command=self.stop_trace, text='Stop Trace')
        self._details = PushButton(self._box, grid=[5,4], text='Details')
        self._details_window = None

    def set_coupler(self, coupler):
        self._coupler = coupler
        self._disabled = False
        if self._coupler.coupler_class == 'RawLogCoupler':
            self._start_trace.hide()
            self._stop_trace.hide()
            self._details_window = LogControlWindow(self._parent, self._coupler, self._client)
            self._details.update_command(self.open_details_window)
        self.display()

    def display(self):
        self._name.clear()
        self._name.append(self._coupler.name)
        self._state.clear()
        self._state.append(self._coupler.state)
        self._dev_state.clear()
        self._dev_state.append(self._coupler.dev_state)
        self._protocol.clear()
        self._protocol.append(self._coupler.protocol)
        self._msg_in.clear()
        self._msg_in.append(str(self._coupler.msg_in))
        self._msg_in_rate.clear()
        self._msg_in_rate.append("%5.2f" % self._coupler.input_rate)
        self._msg_out.clear()
        self._msg_out.append(str(self._coupler.msg_out))
        self._msg_out_rate.clear()
        self._msg_out_rate.append("%5.2f" % self._coupler.output_rate)
        if self._coupler.state == 'STOPPED':
            self._action.text = 'Start'
        else:
            self._action.text = 'Stop'
        if self._coupler.state == 'SUSPENDED':
            self._suspend_resume.text = 'Resume'
        else:
            self._suspend_resume.text = 'Suspend'
        self._box.visible = True
        self._box.enable()

    def refresh(self):
        if self._coupler is None:
            return
        try:
            inst = self._client.get_coupler(self._coupler.name)
        except ConsoleAccessException:
            self.disable()
            return
        _logger.debug("Coupler %s refresh msg %d" % (inst.name, inst.msg_in))
        self._coupler = inst
        self.display()

    def action(self):
        if self._action.text == 'Stop':
            self._coupler.stop(self._client)
        else:
            self._coupler.start(self._client)
        self.refresh()

    def action2(self):
        if self._suspend_resume.text == 'Suspend':
            self._coupler.suspend(self._client)
        else:
            self._coupler.resume(self._client)
        self.refresh()

    def disable(self):
        self._disabled = True
        self._coupler = None
        self._box.disable()

    def start_trace(self):
        self._coupler.start_trace(self._client)

    def stop_trace(self):
        self._coupler.stop_trace(self._client)

    def open_details_window(self):
        # print("Coupler class:", self._coupler.coupler_class)
        if self._details_window is not None:
            self._details_window.open()


class LogControlWindow:

    def __init__(self, parent, coupler, client):
        self._coupler = coupler
        self._client = client
        self._window = Window(parent, title='LogReplay Control')
        self._window.hide()

        self._box = Box(self._window, align='top', layout='grid')
        self._box2 = Box(self._box, layout='grid', grid=[0, 0])
        Text(self._box2, grid=[0, 0], text='Log file')
        self._fn = Text(self._box2, grid=[1, 0])
        self._box3 = Box(self._box, layout='grid', grid=[0, 1])
        Text(self._box3, grid=[0, 0], text='Start date')
        self._sd = Text(self._box3, grid=[1, 0])
        self._box4 = Box(self._box, layout='grid', grid=[0, 2])
        Text(self._box4, grid=[0, 0], text='End date')
        self._ed = Text(self._box4, grid=[1, 0])
        self._box5 = Box(self._box, layout='grid', grid=[0, 3])
        Text(self._box5, grid=[0, 0], text='Current replay time')
        self._ct = Text(self._box5, grid=[1, 0])
        self._current_time = None
        self._box6 = Box(self._box, layout='grid', grid=[0, 4])
        Text(self._box6, grid=[0, 0], text='Set replay time')
        self._set_hour = TextBox(self._box6, grid=[1, 0], width=2)
        Text(self._box6, grid=[2, 0], text=':')
        self._set_mn = TextBox(self._box6, grid=[3, 0], width=2)
        Text(self._box6, grid=[4, 0], text=':')
        self._set_sec = TextBox(self._box6, grid=[5, 0], width=2)
        self._set_pb = PushButton(self._box6, grid=[6, 0], text='>>', command=self.copy_date)
        self._apply = PushButton(self._box6, grid=[7, 0], text='Apply', command=self.move_date)

    def open(self):
        log_char = self._coupler.send_cmd(self._client, 'log_file_characteristics')
        if log_char is not None:
            self._fn.append(log_char['filename'])
            self._sd.append(format_date(log_char['start_date']))
            self._ed.append(format_date(log_char['end_date']))
            self._window.show()
            self._box.repeat(10000, self.refresh)
            self.refresh()

    def refresh(self):
        current_date = self._coupler.send_cmd(self._client, 'current_log_date')
        if current_date is None:
            return
        self._current_time = current_date['current_date']
        self._ct.clear()
        self._ct.append(format_date(self._current_time))

    def copy_date(self):
        if self._current_time is not None:
            self._set_hour.value = str(self._current_time.hour)
            self._set_mn.value = str(self._current_time.minute)
            self._set_sec.value = str(self._current_time.second)

    def move_date(self):
        try:
            h = int(self._set_hour.value)
            m = int(self._set_mn.value)
            s = int(self._set_sec.value)
        except ValueError:
            return
        print(h,m,s)
        try:
            new_date = datetime.datetime(
                self._current_time.year,
                self._current_time.month,
                self._current_time.day,
                h, m, s
            )
        except ValueError:
            return
        args = {'target_date': new_date}
        self._coupler.send_cmd(self._client, 'move_to_date', args)


class CouplerListBox:

    def __init__(self, parent, pos, coupler_box: CouplerBox):
        self._coupler_box = coupler_box
        self._box = Box(parent, grid=pos, align='top')
        Text(self._box, align='top', text='Couplers')
        self._coupler_list = ListBox(self._box, align='top', command=self.select)
        self._couplers = {}

    def set_couplers(self, couplers):
        self._coupler_list.clear()
        for i in couplers:
            self._coupler_list.append(i.name)
            self._couplers[i.name] = i

    def select(self, name):
        self._coupler_box.set_coupler(self._couplers[name])

    def clear_list(self):
        self._coupler_list.clear()


class ServerBox:

    def __init__(self, parent, address, console):
        self._address = address
        self._server = console
        self._parent = parent
        self._coupler_list = None
        self._coupler_box = None
        self._devices = None
        self._box = Box(parent, align='top', layout='grid')
        Text(self._box, grid=[0, 0], text="Server@")
        self._addr_text = Text(self._box, grid=[1, 0], text=address)
        self._state_text = Text(self._box, grid=[2, 0])
        self._connected = False
        self._finalized = False
        try:
            self._proxy = console.server_status()
            self._connected = True
        except ConsoleAccessException:
            self._state_text.append('DISCONNECTED')
            return
        self.finalize()

    def finalize(self):
        self._finalized = True
        Text(self._box, grid=[0, 1], text=self._proxy.version)
        Text(self._box, grid=[1, 1], text='Start time')
        self._start_time = Text(self._box, grid=[2, 1], text=self._proxy.start_time)
        PushButton(self._box, grid=[0, 2], text='Stop', command=self.stop_server)
        self._status = Text(self._box, grid=[1, 2], text='Running')
        self._sub_servers_box = Box(self._parent, align='top', layout='grid')
        index = 1
        Text(self._sub_servers_box, grid=[0, 0], text="Sub server name")
        Text(self._sub_servers_box, grid=[1, 0], text="Port")
        Text(self._sub_servers_box, grid=[2, 0], text="Type")
        Text(self._sub_servers_box, grid=[3, 0], text="Connections")
        self._sub_server_lines = []
        for ss in self._proxy.sub_servers():
            self._sub_server_lines.append(SubServerBox(self._sub_servers_box, index, ss))
            index += 1
        Text(self._parent, align='top', text="NMEA2000 Devices")
        self._devices_box = Box(self._parent, align='top', layout='grid')
        Text(self._devices_box, grid=[0, 0], text="Address")
        Text(self._devices_box, grid=[1, 0], text="Manufacturer")
        Text(self._devices_box, grid=[2, 0], text="Product Name")
        Text(self._devices_box, grid=[3, 0], text="Description")
        self._devices = self._server.get_devices()
        self._devices_lines = []
        self.fill_device()

    def fill_device(self):
        index = 1
        for dev in self._devices:
            self._devices_lines.append(DeviceBox(self._devices_box, index, dev))
            index += 1

    def refresh_devices(self):
        devices = self._server.get_devices()
        _logger.info("Number of N2K devices in server %d / current %d" % (len(devices), len(self._devices)))
        if len(self._devices) == len(devices):
            return
        for db in self._devices_lines:
            db.destroy()
        self._devices_lines = []
        self._devices = devices
        self.fill_device()

    def set_coupler_widgets(self, coupler_box, coupler_list):
        self._coupler_list = coupler_list
        self._coupler_box = coupler_box
        self.refresh_couplers()

    def refresh_couplers(self):
        if self._connected:
            try:
                couplers = self._server.get_couplers()
            except ConsoleAccessException:
                return
            if couplers is not None:
                self._coupler_list.set_couplers(couplers)

    def set_address(self, address):
        self._address = address
        self._addr_text.clear()
        self._addr_text.append(address)

    def set_state(self, state):
        self._state_text.clear()
        self._state_text.append(state)

    def set_status(self, status):
        self._status.clear()
        self._status.append(status)

    def stop_server(self):
        self._server.server_cmd('stop')
        self.set_state('DISCONNECTED')
        self._connected = False
        self._coupler_list.clear_list()
        self._coupler_box.disable()

    def refresh(self):
        try:
            self._proxy = self._server.server_status()
        except ConsoleAccessException:
            self.set_state('DISCONNECTED')
            self._connected = False
            if self._finalized:
                self._status.append('Stopped')
                self._status.clear()
                self._start_time.clear()
                self._coupler_list.clear_list()
                self._coupler_list.clear_list()
            return
        if not self._connected:
            if not self._finalized:
                self.finalize()
            self.set_state('CONNECTED')
            self.set_status('Running')
            self._start_time.append(self._proxy.start_time)
            # refresh the couplers
            self._connected = True
            self.refresh_couplers()

        self.refresh_devices()
        self._coupler_box.refresh()
        sub = self._proxy.get_sub_servers()
        for l in self._sub_server_lines:
            l.refresh(sub)

    def set_refresh_timer(self):
        self._box.repeat(10000, self.refresh)

    @property
    def connected(self) -> bool:
        return self._connected


class SubServerBox:

    def __init__(self, parent, index, sub_server):
        self._box = parent
        self._index = index - 1 # index in the server list
        self._name = Text(self._box, grid=[0, index], text=sub_server.name)
        self._port = Text(self._box, grid=[1, index], text=sub_server.port)
        self._type = Text(self._box, grid=[2, index], text=sub_server.server_type)
        self._nb_connections = Text(self._box, grid=[3, index], text=str(sub_server.nb_connections))

    def refresh(self, sub_servers):
        # print("Sub refresh", sub_servers[self._index].name, sub_servers[self._index].nb_connections)
        self._nb_connections.clear()
        self._nb_connections.append(str(sub_servers[self._index].nb_connections))


class DeviceBox:

    def __init__(self, parent, index, device):
        self._box = parent
        self._index = index - 1  # index in the server list
        self._addr = Text(self._box, grid=[0, index], text=device.address)
        self._mfg = Text(self._box, grid=[1, index], text=device.manufacturer_name)
        self._prod = Text(self._box, grid=[2, index], text=device.product_name)
        self._descr = Text(self._box, grid=[3, index], text=device.description)

    def destroy(self):
        self._addr.destroy()
        self._mfg.destroy()
        self._prod.destroy()
        self._descr.destroy()


class MainMenu:

    def __init__(self, parent):
        self._parent = parent
        self._system_window = None
        self._mppt_window = None
        self._menu = MenuBar(parent,
                             toplevel=['File', 'Functions'],
                             options=[
                                [['Quit', self.quit]],
                                [['System', self.system], ['MPPT', self.mppt]]
                             ])

    def quit(self):
        sys.exit(0)

    def system(self):
        self._system_window.open()

    def mppt(self):
        self._mppt_window.open()

    def set_system_window(self, window):
        self._system_window = window

    def set_mppt_window(self, window):
        self._mppt_window = window


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
    top = App(title="Navigation router control", width=800)
    control_panel_window = ControlPanel(top, opts.address, opts.system)
    mppt_window = MpptServerBox(top, opts.address, opts.mppt)
    menu = MainMenu(top)
    menu.set_system_window(control_panel_window)
    menu.set_mppt_window(mppt_window)
    server_box = ServerBox(top, server, console)
    coupler_wbox = Box(top, align='left', layout='grid')
    coupler_box = CouplerBox(coupler_wbox, [1, 0], console)
    coupler_list = CouplerListBox(coupler_wbox, [0, 0], coupler_box)
    server_box.set_coupler_widgets(coupler_box, coupler_list)

    server_box.set_refresh_timer()
    top.display()


if __name__ == '__main__':
    main()
