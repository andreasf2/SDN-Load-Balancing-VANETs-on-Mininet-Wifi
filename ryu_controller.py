from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types
from ryu.lib import hub
import datetime

# ANSI COLOR CODES
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

class VanetLoadBalancer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(VanetLoadBalancer, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id, priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)

    # Η Δράση του Load Balancing
    def trigger_load_balancing(self, datapath):
        if datapath.id == 1:
            parser = datapath.ofproto_parser
            match = parser.OFPMatch(eth_dst="00:00:00:00:00:02")
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 10, match, actions)
            # Κίτρινο χρώμα για την ενέργεια του SDN
            print(f"{CYAN}|{RESET} {YELLOW}[SDN ACTION] Rerouting car2 traffic from AP1 to AP2 (Port 3){RESET}    {CYAN}|{RESET}")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        if eth.ethertype == ether_types.ETH_TYPE_LLDP: return
        
        dst, src, dpid = eth.dst, eth.src, datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        out_port = self.mac_to_port[dpid][dst] if dst in self.mac_to_port[dpid] else datapath.ofproto.OFPP_FLOOD
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        if out_port != datapath.ofproto.OFPP_FLOOD:
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(datapath, 1, match, actions)

        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=msg.data if msg.buffer_id == datapath.ofproto.OFP_NO_BUFFER else None)
        datapath.send_msg(out)

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(2)

    def _request_stats(self, datapath):
        req = datapath.ofproto_parser.OFPPortStatsRequest(datapath, 0, datapath.ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        time_now = datetime.datetime.now().strftime("%H:%M:%S")

        # Γαλάζιο πλαίσιο για τον τίτλο
        print(f"\n{CYAN}[ {time_now} ] {'='*20} NETWORK DASHBOARD {'='*20}{RESET}")
        
        for stat in sorted(body, key=lambda x: x.port_no):
            if stat.port_no < 4000000000:
                # Κανονική λειτουργία (Πράσινο OK)
                print(f"{CYAN}|{RESET} Switch ID: {dpid:19} {CYAN}|{RESET} Port: {stat.port_no:2} {CYAN}|{RESET} Tx Bytes: {stat.tx_bytes:12} {CYAN}|{RESET} Status: {GREEN}OK{RESET} {CYAN}|{RESET}")
                
                # Έλεγχος Υπερφόρτωσης (Κόκκινο Alert)
                if stat.tx_bytes > 50000:
                    print(f"{CYAN}|{RESET} {RED}{BOLD}{'*'*15} ALERT: OVERLOAD DETECTED ON PORT {stat.port_no} {'*'*15}{RESET} {CYAN}|{RESET}")
                    print(f"{CYAN}|{RESET} {YELLOW}ACTION: INITIATING SDN LOAD BALANCING SEQUENCE ...{RESET}                  {CYAN}|{RESET}")
                    
                    self.trigger_load_balancing(ev.msg.datapath)
                    
        print(f"{CYAN}{'='*65}{RESET}")
