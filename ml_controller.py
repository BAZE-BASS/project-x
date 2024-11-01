import requests  # Import the requests library for making HTTP calls
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.lib.packet import packet, ethernet
from ryu.ofproto import ofproto_v1_3

class MLController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MLController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.node_server_url = "http://localhost:3000/classify-traffic"  # URL of your Node.js server

    def predict_attack(self, tx_bytes, rx_bytes):
        """Send traffic data to the Node.js server to classify as attack or normal."""
        try:
            response = requests.post(self.node_server_url, json={
                'tx_bytes': tx_bytes,
                'rx_bytes': rx_bytes
            })

            if response.status_code == 200:
                prediction = response.json().get("prediction")
                return prediction == "attack"
            else:
                self.logger.error(f"Node server returned error: {response.status_code}")
                return False

        except requests.RequestException as e:
            self.logger.error(f"Error contacting Node server: {e}")
            return False

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # Simulate tx_bytes and rx_bytes for demonstration
        tx_bytes = 1200  # Example placeholder value (transmitted bytes)
        rx_bytes = 800   # Example placeholder value (received bytes)

        # Use predict_attack to classify traffic
        if self.predict_attack(tx_bytes, rx_bytes):
            self.logger.info(f"Attack detected from {src} to {dst} on switch {dpid}")
            return

        # Proceed with normal forwarding if no attack
        out_port = self.mac_to_port[dpid][dst] if dst in self.mac_to_port[dpid] else ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]

        # Add flow entry for non-attack traffic
        match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
        self.add_flow(datapath, 1, match, actions)
