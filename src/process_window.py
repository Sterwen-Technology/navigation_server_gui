import datetime
import os
import sys
from argparse import ArgumentParser
import logging

# sys.path.insert(0, "../../navigation_server/src/navigation_clients")
sys.path.insert(0, "../../navigation_server/")

from guizero import App, ListBox, Text, Box, PushButton, MenuBar, Window, TextBox
from navigation_server.navigation_clients import ConsoleClient, GrpcClient
from navigation_server.router_common import GrpcAccessException

from util_functions import format_date, format_timestamp


_logger = logging.getLogger("ShipDataServer")


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
        Text(self._box, grid=[4, 2], text='Raw input count')
        self._raw_count = Text(self._box, grid=[5, 2])
        Text(self._box, grid=[6, 2], text="Raw rate (msg/s)")
        self._raw_rate = Text(self._box, grid=[6, 2])
        self._action = PushButton(self._box, grid=[0, 4], command=self.action)
        self._suspend_resume = PushButton(self._box, grid=[1, 4], command=self.action2)
        self._refresh = PushButton(self._box, grid=[2, 4], command=self.refresh, text='Refresh')
        self._start_trace = PushButton(self._box, grid=[3, 4], command=self.start_trace, text='Start Trace')
        self._stop_trace = PushButton(self._box, grid=[4, 4], command=self.stop_trace, text='Stop Trace')
        self._details = PushButton(self._box, grid=[5, 4], text='Details')
        self._details_window = None

    def set_coupler(self, coupler):
        self._coupler = coupler
        self._disabled = False
        if self._coupler.coupler_class in ('RawLogCoupler', 'TransparentCanLogCoupler'):
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
        self._msg_in_rate.append("%5.1f" % self._coupler.input_rate)
        self._msg_out.clear()
        self._msg_out.append(str(self._coupler.msg_out))
        self._msg_out_rate.clear()
        self._msg_out_rate.append("%5.1f" % self._coupler.output_rate)
        self._raw_count.clear()
        self._raw_count.append(self._coupler.msg_raw)
        self._raw_rate.clear()
        self._raw_rate.append("%6.1f" % self._coupler.input_rate_raw)
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
        except GrpcAccessException:
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
        self._restart = PushButton(self._box6, grid=[8,0], text="Restart", command=self.restart)
        self._box7 = Box(self._box, layout='grid', grid=[0, 5])
        Text(self._box7, grid=[0, 0], text='Filter SA')
        self._sa = TextBox(self._box7, grid=[1, 0], width=3)
        self._remove = PushButton(self._box7, grid=[2, 0], text='Remove', command=self.remove_sa)
        self._add = PushButton(self._box7, grid=[3, 0], text='Add', command=self.add_sa)

    def open(self):
        log_char = self._coupler.send_cmd(self._client, 'log_file_characteristics')
        if log_char is not None:
            self._fn.clear()
            self._fn.append(log_char['filename'])
            self._sd.clear()
            self._sd.append(format_date(log_char['start_date']))
            self._ed.clear()
            self._ed.append(format_date(log_char['end_date']))
            self._window.show()
            self._box.repeat(10000, self.refresh)
            self.refresh()

    def refresh(self):
        try:
            current_date = self._coupler.send_cmd(self._client, 'current_log_date')
        except GrpcAccessException:
            self._window.hide()
            self._box.cancel(self.refresh)
            return

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
        # print(h,m,s)
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

    def restart(self):
        self._coupler.send_cmd(self._client, 'restart')

    def remove_sa(self):
        sa = int(self._sa.value)
        args = {'address': sa}
        self._coupler.send_cmd(self._client, 'remove_sa', args)

    def add_sa(self):
        sa = int(self._sa.value)
        args = {'address': sa}
        self._coupler.send_cmd(self._client, 'add_sa', args)

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


class ProcessWindow:

    def __init__(self, parent, address, name):
        self._address = address
        self._server = GrpcClient.get_client(address)
        self._console = ConsoleClient()
        self._server.add_service(self._console)
        self._parent = parent
        self._coupler_list = None
        self._coupler_box = None
        self._devices = None
        self._window = Window(parent, title=f"Control console for {name}", width=800)
        self._window.hide()
        self._box = Box(self._window, align='top', layout='grid')
        Text(self._box, grid=[0, 0], text="Server@")
        self._addr_text = Text(self._box, grid=[1, 0], text=address)
        self._state_text = Text(self._box, grid=[2, 0])
        self._hostname_text = Text(self._box, grid=[3, 0])
        self._connected = False
        self._proxy = None
        Text(self._box,grid=[0, 1], text="Version")
        self._version_text = Text(self._box, grid=[1, 1])
        Text(self._box, grid=[2, 1], text='Start time')
        self._start_time = Text(self._box, grid=[3, 1])

        PushButton(self._box, grid=[0, 2], text='Stop', command=self.stop_server)
        PushButton(self._box, grid=[3, 2], text="Close", command=self.close)
        self._status = Text(self._box, grid=[1, 2])
        # New fields
        Text(self._box, grid=[0,3], text="Settings:")
        Text(self._box, grid=[0,4], text="Server name:")
        Text(self._box, grid=[2,4], text="Purpose:")

        self._settings = Text(self._box, grid=[1, 3])
        self._server_name = Text(self._box, grid=[1,4])
        self._purpose = Text(self._box, grid=[3,4])

        self._sub_servers_box = Box(self._window, align='top', layout='grid', border=1)
        Text(self._sub_servers_box, grid=[0, 0], text="Sub server name", bold=True)
        Text(self._sub_servers_box, grid=[1, 0], text="Port", bold=True)
        Text(self._sub_servers_box, grid=[2, 0], text="Type", bold=True)
        Text(self._sub_servers_box, grid=[3, 0], text="Connections", bold=True)
        self._sub_server_lines = None

        coupler_wbox = Box(self._window, align='left', layout='grid')
        coupler_box = CouplerBox(coupler_wbox, [1, 0], self._console)
        coupler_list = CouplerListBox(coupler_wbox, [0, 0], coupler_box)
        self.set_coupler_widgets(coupler_box, coupler_list)
        self._finalized = False
        self._window.when_closed = self.close

    def open(self):
        self._window.show()
        try:
            self._proxy = self._console.server_status()
            self._connected = True
        except GrpcAccessException:
            self._state_text.clear()
            self._state_text.append('DISCONNECTED')
            return
        if not self._finalized:
            self.setup_display()
        self.refresh_couplers()
        self._window.repeat(10000, self.refresh)

    def close(self):
        self._window.cancel(self.refresh)
        self._window.hide()


    def setup_display(self):
        self.set_state('CONNECTED')
        self.set_hostname()
        self._settings.clear()
        self._settings.append(self._proxy.settings)
        self._server_name.clear()
        self._server_name.append(self._proxy.name)
        self._purpose.clear()
        self._purpose.append(self._proxy.purpose)
        self._version_text.clear()
        self._version_text.append(self._proxy.version)
        self._start_time.clear()
        self._start_time.append(self._proxy.start_time)
        self._sub_server_lines = []
        index = 1
        for ss in self._proxy.sub_servers():
            self._sub_server_lines.append(SubServerBox(self._sub_servers_box, index, ss))
            index += 1
        self._finalized = True

    def set_coupler_widgets(self, coupler_box, coupler_list):
        self._coupler_list = coupler_list
        self._coupler_box = coupler_box
        self.refresh_couplers()

    def refresh_couplers(self):
        if self._connected:
            try:
                couplers = self._console.get_couplers()
            except GrpcAccessException:
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

    def set_hostname(self):
        self._hostname_text.clear()
        self._hostname_text.append(self._proxy.hostname)

    def set_status(self, status):
        self._status.clear()
        self._status.append(status)

    def stop_server(self):
        try:
            self._console.server_cmd('stop')
        except GrpcAccessException:
            return
        self.set_state('DISCONNECTED')
        self._connected = False
        self._coupler_list.clear_list()
        self._coupler_box.disable()

    def refresh(self):
        _logger.info("Process Window refresh")
        try:
            self._proxy = self._console.server_status()
        except GrpcAccessException:
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
                self.setup_display()
            self.set_state('CONNECTED')
            self.set_status('Running')
            self._start_time.append(self._proxy.start_time)
            self.set_hostname()
            # refresh the couplers
            self._connected = True
            self.refresh_couplers()

        self._coupler_box.refresh()
        sub = self._proxy.get_sub_servers()
        for l in self._sub_server_lines:
            l.refresh(sub)

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

