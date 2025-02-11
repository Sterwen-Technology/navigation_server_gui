
import logging
import sys
from guizero import Window, Box, Text, PushButton, ListBox


sys.path.insert(0, "../../navigation_server/navigation_server")

from navigation_clients.agent_client import AgentClient
from router_common.protobuf_utilities import GrpcAccessException


_logger = logging.getLogger("ShipDataClient")


class ControlPanel:

    def __init__(self, parent, address, port):
        #
        addr = "%s:%d" % (address, port)
        self._client = AgentClient(addr)
        # test connection
        self._top = Window(parent, title="Remote Control Panel", width=1100)
        self._top.hide()
        # now create all the buttons
        self._status = Text(self._top, align='top')
        box = Box(self._top, layout='grid')
        # first row => global system
        Text(box, grid=[0, 0], text="System control")
        PushButton(box, grid=[1, 0], text="Stop", command=self.stop_system_request)
        PushButton(box, grid=[2, 0], text="Restart", command=self.restart_system_request)
        status = ListBox(self._top, align='left', width='fill')
        ServiceControl(box, 1, self._client, 'navigation', "Messages Server", status)
        ServiceControl(box, 2, self._client, "energy", "Energy Management", status)
        NetworkControl(box, 3, self._client, "wlan0", status)

        PushButton(self._top, align='right', text='Close', command=self.close)

    def open(self):
        _logger.info("Open system control window")
        try:
            res = self._client.send_cmd_single_resp('uptime')
        except GrpcAccessException:
            return
        self._status.clear()
        self._status.append(f"Connect on agent running {res}")
        print(res)
        self._top.show()

    def close(self):
        self._top.hide()

    def stop_system(self):
        print("System stop")
        try:
            res = self._client.send_cmd_no_resp('halt')
        except Exception as e:
            print(e)

    def restart_system(self):
        self._client.send_cmd_no_resp('reboot')

    def stop_system_request(self):
        ConfirmationWindow(self._top, "Confirm stopping the navigation router ?", self.stop_system)

    def restart_system_request(self):
        ConfirmationWindow(self._top, "Confirm restarting the navigation router ?", self.restart_system)


class ServiceControl:

    def __init__(self, parent, line, client, service, service_name, status_text):
        self._service = service
        self._client = client
        self._status_text = status_text
        Text(parent, grid=[0, line], text=service_name)
        PushButton(parent, grid=[1, line], text="Status", command=self.status)
        PushButton(parent, grid=[2,line], text="Start", command=self.start)
        PushButton(parent, grid=[3, line], text="Restart", command=self.restart)
        PushButton(parent, grid=[4, line], text="Stop", command=self.stop)

    def status(self):
        self.exec_cmd('status')

    def start(self):
        self.exec_cmd('start')

    def restart(self):
        self.exec_cmd('restart')

    def stop(self):
        self.exec_cmd('stop')

    def exec_cmd(self, cmd):
        self._status_text.clear()
        try:
            lines = self._client.systemd_cmd(cmd, self._service)
            for l in lines:
                self._status_text.append(l)
        except GrpcAccessException:
            pass


class NetworkControl:

    def __init__(self, parent, line, client, interface, status_text):
        self._client = client
        self._interface = interface
        self._status_text = status_text
        Text(parent, grid=[0, line], text=interface)
        PushButton(parent, grid=[1, line], text='Status', command=self.status)
        PushButton(parent, grid=[2, line], text='Reset', command=self.reset)

    def status(self):
        _logger.info("Device status not implemented")

    def reset(self):
        _logger.info(f"Sending reset for {self._interface}")
        self._status_text.clear()
        try:
            line = self._client.network_cmd('reset_device', self._interface)
            self._status_text.append(line)
        except GrpcAccessException:
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
