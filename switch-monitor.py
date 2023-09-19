import logging
import threading
import time

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.topology import event
from ryu.topology.api import get_switch, get_link

LOG = logging.getLogger(__name__)
logging.basicConfig(filename='myapp.log', level=logging.DEBUG)

class MyController(app_manager.RyuApp):
    # Specify the OpenFlow version used by the controller
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MyController, self).__init__(*args, **kwargs)
        # Initialize the switch status dictionary
        self.switch_status = {}

    @set_ev_cls(event.EventSwitchEnter)
    def switch_enter_handler(self, ev):
        # When a switch enters the network, mark its status as UP in the switch_status dictionary
        switch = ev.switch
        self.switch_status[switch.dp.id] = 'UP'
        # Log the switch connection
        LOG.info("Switch connected: %s", switch.dp.id)

    @set_ev_cls(event.EventSwitchLeave)
    def switch_leave_handler(self, ev):
        # When a switch leaves the network, mark its status as DOWN in the switch_status dictionary
        switch = ev.switch
        self.switch_status[switch.dp.id] = 'DOWN'
        # Log the switch disconnection
        LOG.info("Switch disconnected: %s", switch.dp.id)


    def get_switch_status(self):
        # Generate a string representation of the current switch statuses
        switch_status_str = ''
        for switch_id, status in self.switch_status.items():
            switch_status_str += f'Switch {switch_id}: {status}\n'
        return switch_status_str

    def save_switch_status(self, switch_status):
        # Save the switch status to a file
        try:
            with open('switch_status.txt', 'w') as f:
                f.write(switch_status)
        except IOError:
            LOG.error("Failed to write switch status to file")

    def print_switch_status(self):
        # Print the current switch statuses to the console and save to a file
        switch_status = self.get_switch_status()
        LOG.info(switch_status)
        self.save_switch_status(switch_status)

    def start_switch_status_thread(self):
        # A thread that prints and saves the current switch statuses every 5 seconds
        while True:
            self.print_switch_status()
            time.sleep(5)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, MAIN_DISPATCHER)
    def switch_features_handler(self, ev):
        # When a switch connects to the controller, log its datapath ID
        datapath_id = ev.msg.datapath.id
        if ev.state == 0:  # switch connected
            LOG.info("Switch connected: %s", datapath_id)
            # If the switch is connected, mark its status as UP
            self.switch_status[datapath_id] = 'UP'
        elif ev.state == 2:  # switch disconnected
            LOG.info("Switch disconnected: %s", datapath_id)
            # If the switch is disconnected, mark its status as DOWN and print to the console
            self.switch_status[datapath_id] = 'DOWN'
            print(f"Switch {datapath_id} is disconnected")
        # Check the status of other switches and print to the console if any switch is disconnected
        for switch_id, status in self.switch_status.items():
            if status == 'DOWN':
                print(f"Switch {switch_id} is disconnected")

    def start(self):
        super(MyController, self).start()
        # Start the switch status thread when the controller starts
        LOG.info("Starting switch status monitoring")
        status_thread = threading.Thread(target=self.start_switch_status_thread)
        status_thread.daemon = True
        status_thread.start()
