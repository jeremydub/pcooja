from ..packet import *
from ..utils import human_readable_address

class IPv6PacketAnalyzer:

  UNSPECIFIED_ADDRESS = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, \
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

  IPV6_DISPATCH = 0x41

  def matchPacket(self, packet):
    return packet.level == PacketAnalyzer.NETWORK_LEVEL and packet[0] == IPv6PacketAnalyzer.IPV6_DISPATCH
  
  def analyzePacket(self, packet):

    # if packet has less than 40 bytes it is not interesting ...
    if packet.get_payload_size() < 40: return PacketAnalyzer.ANALYSIS_FAILED

    pos = 1

    version = 6
    trafficClass = 0
    flowLabel = 0
    length = packet.getInt(pos + 4, 2)
    proto = packet.getInt(pos + 6, 1)
    ttl = packet.getInt(pos + 7, 1)
    srcAddress = [0x00]*16
    destAddress = [0x00]*16

    packet.copy(pos + 8, srcAddress, 0, 16)
    packet.copy(pos + 24, destAddress, 0, 16)

    # consume dispatch + IP header
    packet.consume_bytes_start(41)

    header_ipv6 = IPv6Header()
    header_ipv6.traffic_class = trafficClass
    header_ipv6.flow_label = flowLabel
    header_ipv6.length = length
    header_ipv6.proto = proto
    header_ipv6.ttl = ttl
    header_ipv6.source = srcAddress
    header_ipv6.destination = destAddress
    packet.add_header(header_ipv6)

    packet.lastDispatch = proto & 0xff
    packet.level = PacketAnalyzer.APPLICATION_LEVEL
    return PacketAnalyzer.ANALYSIS_OK_CONTINUE


class IPv6Header:

    def __str__(self):
        verbose = []
        verbose.append("\033[38;5;166m")
        protoStr = "" + str(self.proto)
        if self.proto == PacketAnalyzer.PROTO_ICMP:
          protoStr = "ICMPv6"
        elif self.proto == PacketAnalyzer.PROTO_UDP:
          protoStr = "UDP"
        elif self.proto == PacketAnalyzer.PROTO_TCP:
          protoStr = "TCP"
        else:
          protoStr = str(self.proto)
        
        verbose.append("IPv6 ")
        verbose.append("TC= ")
        verbose.append(str(self.traffic_class))
        verbose.append(" FL= ")
        verbose.append(str(self.flow_label))
        verbose.append(" TTL= ")
        verbose.append(str(self.ttl))
        verbose.append("\n")
        verbose.append("From ")
        verbose.append(human_readable_address(self.source,2))
        verbose.append(" to ")
        verbose.append(human_readable_address(self.destination,2))
        verbose.append("\033[0m")
        return ''.join(verbose)

    def __repr__(self):
        verbose = []
        verbose.append("\033[38;5;166m")
        verbose.append("IPv6: ")
        verbose.append(human_readable_address(self.source[-2:],2))
        verbose.append(" -> ")
        verbose.append(human_readable_address(self.destination[-2:],2))
        verbose.append("\033[0m")
        return ''.join(verbose)
