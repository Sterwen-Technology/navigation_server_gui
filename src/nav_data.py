import datetime
import sys
import logging

# sys.path.insert(0, "../../navigation_server/src/navigation_clients")
sys.path.insert(0, "../../navigation_server/")

from guizero import Window, Text, Box, PushButton, ListBox
from util_functions import format_date


from navigation_server.navigation_clients import EngineClient
from navigation_server.router_common import GrpcAccessException, GrpcClient


class DataWindow:

    def __init__(self, parent, server_addr, port):
        self._server = GrpcClient(f"{server_addr}:{port}")
        self._engine_client = EngineClient()
        self._server.add_service(self._engine_client)
        self._top = Window(parent, title="Navigation Data Panel", width=1100)
        self._top.hide()
        # engine section
        Text(self._top, align='top', text="Engine")
        box = Box(self._top, align='top', layout='grid')
        Text(box, grid=[0,0], text='State')
        self._state = Text(box, grid=[1, 0], text="Unknown")
        Text(box, grid=[2, 0], text="Total hours")
        self._total_hours = Text(box, grid=[3, 0])
        Text(box, grid=[4, 0], text="Temperature")
        self._temperature = Text(box, grid=[5, 0])
        Text(box, grid=[6, 0], text='Speed')
        self._speed = Text(box, grid=[7, 0])
        Text(box,grid=[8, 0], text="Voltage")
        self._voltage = Text(box, grid=[9, 0])
        Text(box, grid=[0, 1], text="Last start time")
        self._last_start_time = Text(box, grid=[1, 1])
        Text(box, grid=[2, 1], text="Last stop time")
        self._last_stop_time = Text(box, grid=[3, 1])
        self._events_list = ListBox(self._top, align='top', width='fill')


    def open(self):
        if self._server.state == GrpcClient.NOT_CONNECTED:
            self._server.connect()
        self._top.show()
        self.refresh()
        self._top.repeat(10000, self.refresh)

    def close(self):
        self._top.hide()
        self._top.repeat(0, None)

    def refresh(self):
        try:
            engine_data = self._engine_client.get_data(0)
        except GrpcAccessException:
            self._state.clear()
            self._total_hours.clear()
            return
        if engine_data is not None:
            # print(f"state {engine_data.state},at {engine_data.speed}rpm, hours:{engine_data.total_hours}")
            # print(f"Last start {engine_data.last_start_time} - Last stop {engine_data.last_stop_time}")
            try:
                engine_events = self._engine_client.get_events(0)
            except GrpcAccessException:
                return
            if engine_events is not None:
                if len(engine_events) > 0:
                    for ev in engine_events:
                        print(f"Event {ev.timestamp} hours {ev.total_hours} "
                              f"from {ev.previous_state} to {ev.current_state}")
                else:
                    print("No events")
            else:
                print("Problem retrieving events")
            self._state.clear()
            self._state.append(engine_data.state)
            self._total_hours.clear()
            self._total_hours.append("%6.1f" % (engine_data.total_hours / 3600.0))
            self._temperature.clear()
            self._speed.clear()
            self._voltage.clear()
            if engine_data.state == 'ENGINE_OFF':
                self._temperature.append('---')
                self._speed.append('----')
                self._voltage.append('--.--')
            else:
                self._temperature.append('%3.0f' % (engine_data.temperature - 273.16))
                self._speed.append('%4.0f' % engine_data.speed)
                self._voltage.append('%5.2f' % engine_data.alternator_voltage)
            self._last_start_time.clear()
            self._last_stop_time.clear()
            self._last_start_time.append(engine_data.last_start_time)
            self._last_stop_time.append(engine_data.last_stop_time)
            self._events_list.clear()
            engine_events.sort(key=lambda x: x.timestamp, reverse=True)
            # sort the events
            for ev in engine_events:
                ev_date = datetime.datetime.fromisoformat(ev.timestamp)
                self._events_list.append(f"{format_date(ev_date)} - hours:{ev.total_hours / 3600.:4.1f} : {ev.previous_state} => {ev.current_state}")
        else:
            self._state.clear()
            self._total_hours.clear()


