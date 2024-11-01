import joblib
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4
from ryu.lib import hub

class MLController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MLController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.model = joblib.load('traffic_model.joblib')
        self.packet_stats = {}  # Track tx/rx bytes by host pairs

    def predict_attack(self, tx_bytes, rx_bytes):
        # Use ML model to predict if traffic is an attack
        prediction = self.model.predict([[tx_bytes, rx_bytes]])
        return prediction[0] == 'attack'

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if ip_pkt:
            src = ip_pkt.src
            dst = ip_pkt.dst
        else:
            src = eth.src
            dst = eth.dst

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # Initialize or update traffic stats for the source-destination pair
        if (src, dst) not in self.packet_stats:
            self.packet_stats[(src, dst)] = {'tx_bytes': 0, 'rx_bytes': 0}
        self.packet_stats[(src, dst)]['tx_bytes'] += len(msg.data)

        # Predict if traffic is an attack
        tx_bytes = self.packet_stats[(src, dst)]['tx_bytes']
        rx_bytes = self.packet_stats[(src, dst)]['rx_bytes']
        if self.predict_attack(tx_bytes, rx_bytes):
            self.logger.info(f"Attack detected from {src} to {dst} on switch {dpid}")
            return  # Drop packet by not sending any action

        # Normal forwarding if no attack
        out_port = self.mac_to_port[dpid][dst] if dst in self.mac_to_port[dpid] else ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]

        # Install a flow to avoid future packet_in events for this flow
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # Send the packet out
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=msg.data)
        datapath.send_msg(out)

    def add_flow(self, datapath, priority, match, actions, idle_timeout=60, hard_timeout=300):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match,
                                instructions=inst, idle_timeout=idle_timeout, hard_timeout=hard_timeout)
        datapath.send_msg(mod)
