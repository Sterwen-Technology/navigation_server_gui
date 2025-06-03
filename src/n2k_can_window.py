import logging
import sys

# sys.path.insert(0, "../../navigation_server/src/navigation_clients")
sys.path.insert(0, "../../navigation_server/")

from guizero import App, ListBox, Text, Box, PushButton, MenuBar, Window, TextBox, ButtonGroup, RadioButton
from navigation_server.navigation_clients import NMEA2000CanClient
from navigation_server.router_common import GrpcAccessException, GrpcClient

from util_functions import format_date, format_timestamp


_logger = logging.getLogger("ShipDataServer")


class N2kCanWindow:

    def __init__(self, parent):

        self._server = None
        self._service = None

        self._parent = Window(parent, title="NMEA2000 and CAN controls", width=800, height=900)
        self._parent.hide()
        status_box = Box(self._parent, align='top', layout='grid')
        self._server_address = Text(status_box, grid=[0, 0])
        self._connect_state = Text(status_box, grid=[1, 0])
        Text(status_box, grid=[0,1], text='Channel:')
        self._channel = Text(status_box, grid=[1,1])
        Text(status_box, grid=[0,2], text="Input msg rate")
        self._in_msg_rate = Text(status_box, grid=[1, 2])
        Text(status_box, grid=[2, 2], text='Output msg rate')
        self._out_msg_rate = Text(status_box, grid=[3, 2])
        Text(status_box, grid=[0, 3], text='CAN bus traces')
        self._traces_control_on = PushButton(status_box, grid=[1,3], text='On', enabled=False, command=self.start_trace)
        self._traces_control_off = PushButton(status_box, grid=[2, 3], text='Off', enabled=False, command=self.stop_trace)
        devices_head = Box(self._parent, align='top')
        Text(devices_head, align='left', text="NMEA2000 Devices")
        PushButton(devices_head, align='right', text='Refresh list', command=self.force_refresh_devices)
        self._devices_box = Box(self._parent, align='top', layout='grid')
        Text(self._devices_box, grid=[0, 0], text="Address")
        Text(self._devices_box, grid=[1, 0], text="Manufacturer")
        Text(self._devices_box, grid=[2, 0], text="Product Name")
        # Text(self._devices_box, grid=[3, 0], text="ISO System Name")
        Text(self._devices_box, grid=[3, 0], text="Last seen ")
        self._n2k_can_stat = None
        self._devices = []
        self._devices_lines = []


    def open(self, address, port):
        if self._server is None:
            self._server = GrpcClient.get_client(f"{address}:{port}")
            self._service = NMEA2000CanClient()
            self._server.add_service(self._service)
            self._server_address.append(address)

        if not self._server.connected:
            self._server.connect()
        try:
            self._n2k_can_stat = self._service.get_status()
            self._connect_state.clear()
            self._connect_state.append("CONNECTED")
        except GrpcAccessException:
            self._connect_state.clear()
            self._connect_state.append("DISCONNECTED")
        if self._n2k_can_stat is not None:
            self._channel.clear()
            self._channel.append(self._n2k_can_stat.channel)
            if self._n2k_can_stat.traces_on:
                self._traces_control_on.disable()
                self._traces_control_off.enable()
            else:
                self._traces_control_on.enable()
                self._traces_control_off.disable()
            self.display_devices()
        self._parent.show()
        self._parent.repeat(10000, self.refresh_display)
        self._parent.when_closed = self.close_window

    def close_window(self):
        self._parent.cancel(self.refresh_display)
        self._parent.hide()

    def fill_device(self):
        index = 1
        for dev in self._devices:
            self._devices_lines.append(DeviceBox(self._devices_box, index, dev))
            index += 1

    def display_devices(self):
        self._in_msg_rate.clear()
        self._out_msg_rate.clear()
        self._in_msg_rate.append(f"{self._n2k_can_stat.incoming_rate:5.1f}")
        self._out_msg_rate.append(f"{self._n2k_can_stat.outgoing_rate:5.1f}")
        devices = self._n2k_can_stat.devices
        _logger.debug("Number of N2K devices in server %d / current %d" % (len(devices), len(self._devices)))
        if len(devices) == len(self._devices):
            change_flag = False
            for dev in devices:
                if dev.changed:
                    change_flag = True
        else:
            change_flag = True
        if not change_flag:
            return
        for db in self._devices_lines:
            db.destroy()
        self._devices_lines = []
        self._devices = devices
        self.fill_device()

    def force_refresh_devices(self):
        self._n2k_can_stat = self._service.get_status('poll')
        self.display_devices()

    def refresh_display(self):
        if self._server.connected:
            self._n2k_can_stat = self._service.get_status()
            self.display_devices()
        else:
            self._server.connect()

    def start_trace(self):
        try:
            resp = self._service.start_trace("")
        except GrpcAccessException:
            _logger.error("Error on traces start")
            return
        if resp.traces_on:
            self._traces_control_on.disable()
            self._traces_control_off.enable()

    def stop_trace(self):
        try:
            resp = self._service.stop_trace()
        except GrpcAccessException:
            _logger.error("Error on traces stop")
            return
        if not resp.traces_on:
            self._traces_control_on.enable()
            self._traces_control_off.disable()


class DeviceBox:

    def __init__(self, parent, index, device):
        self._box = parent
        self._index = index - 1  # index in the server list
        self._addr = Text(self._box, grid=[0, index], text=device.address)
        self._mfg = Text(self._box, grid=[1, index], text=device.manufacturer_name)
        self._prod = Text(self._box, grid=[2, index], text=device.product_name)
        # self._iso_name = Text(self._box, grid=[3, index], text=device.iso_name)
        self._descr = Text(self._box, grid=[3, index], text=format_timestamp(device.last_time_seen))
        self._details = PushButton(self._box, grid=[4, index], text="Details")

    def destroy(self):
        self._addr.destroy()
        self._mfg.destroy()
        self._prod.destroy()
        self._descr.destroy()
        self._details.destroy()