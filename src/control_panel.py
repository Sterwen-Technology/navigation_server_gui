
import logging
import sys
from guizero import Window, Box, Text, PushButton


sys.path.insert(0, "../../navigation_server/src")

from navigation_clients.agent_client import AgentClient


_logger = logging.getLogger("ShipDataClient")


class ControlPanel:

    def __init__(self, parent, address, port):
        #
        addr = "%s:%d" % (address, port)
        self._client = AgentClient(addr)
        # test connection
        self._top = Window(parent, title="Remote Control Panel")
        self._top.hide()
        # now create all the buttons
        box = Box(self._top, layout='grid')
        # first row => global system
        Text(box, grid=[0,0], text="System control")
        PushButton(box, grid=[1,0], text="Stop", command=self.stop_system)
        PushButton(box, grid=[2,0], text="Restart", command=self.restart_system)
        PushButton(box, grid=[0,1], text='Close', command=self.close)

    def open(self):
        _logger.info("Open system control window")
        res = self._client.send_cmd_single_resp('uptime')
        print(res)
        self._top.show()

    def close(self):
        self._top.hide()

    def stop_system(self):
        print("System stop")
        try:
            res = self._client.send_cmd_multiple_resp('ls')
            for r in res:
                print(r)
        except Exception as e:
            print(e)

    def restart_system(self):
        self._client.send_cmd('reboot')




