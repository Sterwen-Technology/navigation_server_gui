
import logging
import sys
from guizero import Window, Box, Text, PushButton, ListBox


sys.path.insert(0, "../../navigation_server/")

from navigation_server.router_common import GrpcAccessException, GrpcClient, AgentClient


_logger = logging.getLogger("ShipDataClient")


class ControlPanel:

    def __init__(self, parent, address):
        #
        self._server = GrpcClient.get_client(address)
        self._client = AgentClient()
        self._server.add_service(self._client)
        # test connection
        self._server.connect()
        # create the header
        self._box = Box(parent, align='top', layout='grid')
        Text(self._box, grid=[0, 0], text="Server@")
        self._addr_text = Text(self._box, grid=[1, 0], text=address)
        self._state_text = Text(self._box, grid=[2, 0])
        self._hostname_text = Text(self._box, grid=[3, 0])
        self._connected = False
        system_box = Box(parent, align='top', layout='grid')
        # first row => global system
        Text(system_box, grid=[0, 0], text="System control")
        PushButton(system_box, grid=[1, 0], text="Stop", command=self.stop_system_request)
        PushButton(system_box, grid=[2, 0], text="Restart", command=self.restart_system_request)
        Text(parent,align='top', text='processes in system')
        self._process_box = Box(parent, align='top', layout='grid')
        self._process_list = None

        try:
            self._system = self._client.systemd_cmd('status')
            self._connected = True
        except GrpcAccessException:
            return

        self.display_processes()

    def display_processes(self):
        processes = self._system.get_processes()
        line = 0
        self._process_list = []
        for process in processes:
            self._process_list.append(ServiceControl(self._process_box, line, self._client, process))
            line += 1

    def stop_system(self):
        print("System stop")
        try:
            res = self._client.system_cmd('halt')
        except Exception as e:
            print(e)

    def restart_system(self):
        self._client.system_cmd('reboot')

    def stop_system_request(self):
        ConfirmationWindow(self._top, "Confirm stopping the navigation router ?", self.stop_system)

    def restart_system_request(self):
        ConfirmationWindow(self._top, "Confirm restarting the navigation router ?", self.restart_system)


class ServiceControl:

    def __init__(self, parent, line, client, process):
        self._client = client
        self._process = process
        Text(parent, grid=[0, line], text=process.name)
        self._state = Text(parent, grid=[1, line], text=process.state)
        self._stat_pb = PushButton(parent, grid=[2, line], text="Status", command=self.status)
        self._start_pb = PushButton(parent, grid=[3,line], text="Start", command=self.start)
        self._restart_pb =PushButton(parent, grid=[4, line], text="Restart", command=self.restart)
        self._stop_pb = PushButton(parent, grid=[5, line], text="Stop", command=self.stop)
        self.open_pb = PushButton(parent, grid=[6, line], text="Open", command=self.open)

    def status(self):
        self.exec_cmd('status')

    def start(self):
        self.exec_cmd('start')

    def restart(self):
        self.exec_cmd('restart')

    def stop(self):
        self.exec_cmd('stop')

    def exec_cmd(self, cmd):
        self._state.clear()
        try:
            resp = self._client.process_cmd(cmd, self._process.name)
            if resp is not None:
                self._process = resp
        except GrpcAccessException:
            pass

    def open(self):
        pass


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
