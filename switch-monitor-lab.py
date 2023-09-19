import logging
import threading
import time
import json 

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER , CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.lib import hub


# Timeout for switch keep-alive response (in seconds)
KEEP_ALIVE_TIMEOUT = 0.2

class KeepAliveController(app_manager.RyuApp):

    # Specify the OpenFlow version used by the controller
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(KeepAliveController, self).__init__(*args, **kwargs)
        self.switch_status = {}  # Dictionary to track switch status
        self.switch_dp = {}  # Dictionary to track switch status
        self.keep_alive_thread = hub.spawn(self._keep_alive_loop)
        self.config_reply_event = hub.Event()
    
    def _keep_alive_loop(self):
        while True:
            self.print_switch_status()
            self._check_switch_status()
            hub.sleep(2)  # Check switch status every 1 second


###################################################
#       SWITCH UP AND RUNNING 
#       we check if the staus is up and proceed whit
#       sending the keep alive message 
###################################################

    def _check_switch_status(self):
       
        # Get the current timestamp
        timestamp = time.time()

        # Convert the timestamp to a human-readable format
        timestamp_str = time.ctime(timestamp)

        # Log the timestamp
        print(f"*********************")
        print(f"Timestamp: {timestamp_str}")
        print(f"*********************")
       
        for switch_id, status in list(self.switch_dp.items()):
            if status :
                # Send keep-alive message and wait for reply
                self.send_keep_alive_message(switch_id ,status)
                # Wait for the echo reply with a timeout
                hub.sleep(KEEP_ALIVE_TIMEOUT)

            if status == 'DOWN':
                print(f"******* ATTENTION: Switch went offline, i will continue sending keep alive messages {switch_id}")

###################################################
#       SEND KEEP ALIVE MESSAGE 
###################################################

    def send_keep_alive_message(self, switch_id, status): 
            print(f"Sending keep-alive message to switch {switch_id}")
            self.switch_status[switch_id] = 'DOWN'

            ofproto = status.ofproto
            parser = status.ofproto_parser

            # Create a JSON payload with an additional text message
            payload = {
                "message_type": "echo",
                "data": "Hello, switch!",
            }

            json_payload = json.dumps(payload).encode('utf-8')

            # Create an OFPEchoRequest message with the JSON payload
            echo_req_msg = parser.OFPEchoRequest(status, data=json_payload)

            # Log the message value before sending
            print(f"Message Value: {echo_req_msg.data}")

            # Send the OFPEchoRequest message to the switch
            status.send_msg(echo_req_msg)

###################################################
#       HANDLE REPLY
###################################################

    @set_ev_cls(ofp_event.EventOFPEchoReply, MAIN_DISPATCHER)
    def echo_reply_handler(self, ev):
        switch_id = ev.msg.datapath.id
        print(f"Received echo reply from switch {switch_id}")
        self.switch_status[switch_id] = 'UP'

        # We set a flag indicating that a reply was received
        self.config_reply_event.set()



###################################################
#       SWITCH UP AND RUNNING 
###################################################

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER )
    def switch_state_change_handler(self, ev):
        
        # When a switch's state changes, update its status in the switch_status dictionary
        if ev:
            #salvo lo staus
            switch_id = ev.msg.datapath.id
            self.switch_status[ev.msg.datapath.id] = 'UP'
            #salvo il datapath
            self.switch_dp[ev.msg.datapath.id] =  ev.msg.datapath

             # Reset the event flag for each switch
            self.config_reply_event.clear()

        print(f"********* Switch  {ev.msg.datapath.id} is connected *********")


###################################################
#       GET AND PRINT STATUS
###################################################


    def get_switch_status(self):
        # Generate a string representation of the current switch statuses
        switch_status_str = ''
        for switch_id, status in self.switch_status.items():
            switch_status_str += f'Switch {switch_id}: {status}\n'
        return switch_status_str
    
    def print_switch_status(self):
        # Print the current switch statuses to the console and save to a file
        switch_status = self.get_switch_status()
        print(switch_status)


    def start(self):
        super(KeepAliveController, self).start()

