from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, icmp, tcp, udp, arp
import logging


class PacketLogger(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]


    def __init__(self, *args, **kwargs):
        super(PacketLogger, self).__init__(*args, **kwargs)

        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler('packet_log.txt')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.logger.info("Packet Logger Initialized. Waiting for traffic...")


    # IMPORTANT: install table-miss rule
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                   ofproto.OFPCML_NO_BUFFER)
        ]

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=0,
            match=match,
            instructions=inst
        )

        datapath.send_msg(mod)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)

        if eth_pkt.ethertype == 35020:
            return

        log_msg = f"[Switch {datapath.id} | Port {in_port}] "
        log_msg += f"MAC: {eth_pkt.src} -> {eth_pkt.dst} | "

        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        arp_pkt = pkt.get_protocol(arp.arp)

        if ipv4_pkt:
            log_msg += f"IPv4: {ipv4_pkt.src} -> {ipv4_pkt.dst} | Protocol: "

            if pkt.get_protocol(icmp.icmp):
                log_msg += "ICMP"
            elif pkt.get_protocol(tcp.tcp):
                tcp_pkt = pkt.get_protocol(tcp.tcp)
                log_msg += f"TCP ({tcp_pkt.src_port}->{tcp_pkt.dst_port})"
            elif pkt.get_protocol(udp.udp):
                udp_pkt = pkt.get_protocol(udp.udp)
                log_msg += f"UDP ({udp_pkt.src_port}->{udp_pkt.dst_port})"
            else:
                log_msg += f"Other ({ipv4_pkt.proto})"

        elif arp_pkt:
            log_msg += f"ARP: {arp_pkt.src_ip} -> {arp_pkt.dst_ip}"
        else:
            log_msg += f"EtherType: {hex(eth_pkt.ethertype)}"

        self.logger.info(log_msg)

        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )

        datapath.send_msg(out)
