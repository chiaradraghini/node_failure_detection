from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
# from ryu.app.wsgi import WSGIApplication
from ryu.lib.packet import packet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ethernet
import ryu.app.ofctl.api as api

class MyFirstApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MyFirstApp, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.src_dict = {}

    #----------------------------------------------------------
    # Write the function: Add a flow in the switch flow table
    #----------------------------------------------------------

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)
        ##############################################################################################
        # This section is needed to guarantee that each rule is installed in order.
        # Otherwise, there are problems in which a packet goes back to the controller because the
        # rule in the next switch has still to be implemented.
        # We send a barrier request that forces the switch to install it immediately before processing
        # another packet.
        # Fixed in OpenFlow 1.4 with BundleMsg
        msg = parser.OFPBarrierRequest(datapath)
        api.send_msg(self, msg, reply_cls=datapath.ofproto_parser.OFPBarrierReply, reply_multi=True)
        ##############################################################################################


    #--------------------------------------------------------------------
    # Write the function: Upon a switch feature reply, add the table miss
    #--------------------------------------------------------------------

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        self.logger.info("Table miss installed for switch: %s", datapath.id)


    #---------------------------------------------------
    # Write the function that handle a packet-in request
    #---------------------------------------------------

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src
        
        if eth_pkt.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        if eth_pkt.ethertype == ether_types.ETH_TYPE_IPV6:
            # ignore ipv6 packet
            return
        
        # Simple broadcast packets manager
        if dst == "ff:ff:ff:ff:ff:ff":
            if src not in self.src_dict:
                self.src_dict[src] = 0
            else: 
                self.src_dict[src] += 1
                if self.src_dict[src] >= 3:
                    return

        # get the received port number from packet_in message.
        in_port = msg.match['in_port']

        self.logger.info("packet in switch: %s, from host: %s, to host: %s, from port: %s", dpid, src, dst, in_port)
        
        # learn a mac address to avoid FLOOD next time.
        if src not in self.mac_to_port[dpid]:            
            self.mac_to_port[dpid][src] = in_port

        # if the destination mac address is already learned,
        # decide which port to output the packet, otherwise FLOOD.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        
        self.logger.info("forwarding table: %s", self.mac_to_port)
        
        # construct action list.
        actions = [parser.OFPActionOutput(out_port)]
        self.logger.info("actions: %s", actions)


        # install a flow to avoid packet_in next time.
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)

