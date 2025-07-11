
import logging
import sys
from guizero import Window, Box, Text, PushButton, ListBox


sys.path.insert(0, "../../navigation_server/")

from navigation_server.router_common import GrpcAccessException, GrpcClient, AgentClient
from process_window import ProcessWindow
# from nav_msg_svr_gui import global_variables


_logger = logging.getLogger("ShipDataClient")


class ControlPanel:

    def __init__(self, parent, client, address):
        #

        self._client = client
        self._top = parent
        self._server_address = address  # no port included
        # create the header
        self._box = Box(parent, align='top', layout='grid')
        Text(self._box, grid=[0, 0], text="Server@")
        self._addr_text = Text(self._box, grid=[1, 0], text=self._client.server.address)
        self._state_text = Text(self._box, grid=[2, 0])
        self._hostname_text = Text(self._box, grid=[3, 0])
        self._version = Text(self._box, grid=[0, 1])
        Text(self._box, grid=[1, 1], text='Start time')
        self._start_time = Text(self._box, grid=[2, 1])
        self._connected = False
        system_box = Box(parent, align='top', layout='grid')
        # first row => global system
        Text(system_box, grid=[0, 0], text="System control")
        PushButton(system_box, grid=[1, 0], text="Stop", command=self.stop_system_request)
        PushButton(system_box, grid=[2, 0], text="Restart", command=self.restart_system_request)
        PushButton(system_box, grid=[0,1], text="Restart application", command=self.restart_application)
        Text(parent,align='top', text='processes in system')
        self._process_box = Box(parent, align='top', layout='grid')
        self._process_list = None
        self._box.repeat(10000, self.poll_system)
        self._display_done = False
        try:
            self._system = self._client.system_cmd('status')
            self._connected = True
            self._state_text.append('CONNECTED')
        except GrpcAccessException:
            self._state_text.append('DISCONNECTED')
            return
        if self._system is None:
            return
        self.display_processes()
        self._status_box = Box(parent, align='bottom', layout='grid', width='fill')
        Text(self._status_box, grid=[0,0], text="Command status")
        self._status_text = Text(self._status_box, grid=[1,0])

    @property
    def address(self):
        return self._client.server.address

    def display_processes(self):
        self._hostname_text.append(self._system.hostname)
        self._version.append(self._system.version)
        self._start_time.append(self._system.start_time)
        processes = self._system.get_processes()
        line = 0
        self._process_list = {}
        for process in processes:
            self._process_list[process.name] = ServiceControl(self._process_box, line, self._client, process, self._server_address)
            line += 1
        self._display_done = True

    def refresh_processes(self):
        for process in self._system.get_processes():
            try:
                sc = self._process_list[process.name]
                sc.refresh_process(process)
            except KeyError:
                _logger.error(f"Missing Process line for {process.name}")


    def stop_system(self):
        print("System stop")
        try:
            res = self._client.system_cmd('halt')
        except Exception as e:
            print(e)
        print("System stop executed")
        self._state_text.clear()
        self._state_text.append('DISCONNECTED')


    def restart_system(self):
        self._client.system_cmd('reboot')
        self._state_text.clear()
        self._state_text.append('DISCONNECTED')

    def stop_system_request(self):
        ConfirmationWindow(self._top, "Confirm stopping the navigation router ?", self.stop_system)

    def restart_system_request(self):
        ConfirmationWindow(self._top, "Confirm restarting the navigation router ?", self.restart_system)

    def restart_application(self):
        self._client.system_cmd('navigation_restart')

    def poll_system(self):
        if self._client.server_connected:
            # print("poll server connected")
            if self._connected:
                return
            else:
                self._state_text.clear()
                self._state_text.append('CONNECTED')
                self._connected = True
                self._system = self._client.system_cmd('status')
                if not self._display_done:
                    self.display_processes()
                else:
                    self.refresh_processes()
        else:
            # print("poll server disconnected")
            self._state_text.clear()
            self._state_text.append('DISCONNECTED')
            self._connected = False
            self.update_status_text(f"Connection attempt to server:{self._client.server.address}")
            if self._client.server_connect_wait(5.0):
                self.update_status_text(f"Successful connection to server:{self._client.server.address}")
                self._state_text.clear()
                self._state_text.append('CONNECTED')
                self._connected = True
            else:
                self.update_status_text(f"Connection attempt to server:{self._client.server.address}")

    def update_status_text(self, text:str):
        self._status_text.clear()
        self._status_text.append(text)



class ServiceControl:

    def __init__(self, parent, line, client, process, address):
        self._parent = parent
        self._client = client
        self._process = process
        self._address = address
        Text(parent, grid=[0, line], text=process.name)
        self._state = Text(parent, grid=[1, line], text=process.state)
        self._stat_pb = PushButton(parent, grid=[2, line], text="Status", command=self.status)
        self._start_pb = PushButton(parent, grid=[4,line], text="Start", command=self.start)
        self._restart_pb =PushButton(parent, grid=[5, line], text="Restart", command=self.restart)
        self._stop_pb = PushButton(parent, grid=[3, line], text="Stop", command=self.stop)
        self._interrupt_pb = PushButton(parent, grid=[6, line], text="Int.", command=self.interrupt)
        self._open_pb = PushButton(parent, grid=[7, line], text="Open", command=self.open)
        if not process.console_present:
            self._open_pb.hide()
            self._window = None
        else:
            self._window = ProcessWindow(parent, f"{address}:{process.grpc_port}", process.name)
        self.refresh_process(process)


    def status(self):
        self.exec_cmd('status')

    def start(self):
        self.exec_cmd('start')

    def restart(self):
        self.exec_cmd('restart')

    def stop(self):
        self.exec_cmd('stop')

    def interrupt(self):
        self.exec_cmd('interrupt')
        self._parent.after(5000, self.status)

    def exec_cmd(self, cmd):
        if not self._client.server_connected:
            return
        self._state.clear()
        try:
            resp = self._client.process_cmd(cmd, self._process.name)
            if resp is not None:
                self.refresh_process(resp.process_proxy)
            return
        except GrpcAccessException:
            return

    def open(self):
        self._window.open()


    def refresh_process(self, process):
        self._process = process
        self._state.clear()
        self._state.append(process.state)
        if process.state == 'RUNNING':
            self._start_pb.disable()
            self._restart_pb.enable()
            # self._stop_pb.enable()
            if process.console_present:
                self._open_pb.enable()
        else:
            self._restart_pb.disable()
            # self._stop_pb.disable()
            self._start_pb.enable()
            self._open_pb.disable()


class ConfirmationWindow:

    def __init__(self, parent, message, action):

        self._window = Window(parent)
        self._action = action
        Text(self._window, text=message)
        box = Box(self._window, layout='grid')
        PushButton(box, grid=[0,0], text="Confirm", command=self.confirm)
        PushButton(box, grid=[1,0], text="Cancel", command=self.cancel)
        self._window.show(wait=True)

    def confirm(self):
        self._action()
        self._window.hide()

    def cancel(self):
        self._window.hide()
