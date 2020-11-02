from ..packet import *

class FragHeadPacketAnalyzer:
  
  SICSLOWPAN_DISPATCH_FRAG1 = 0xc0 # 1100 0xxx
  SICSLOWPAN_DISPATCH_FRAGN = 0xe0 # 1110 0xxx

  def matchPacket(self, packet):
    return packet.level == PacketAnalyzer.NETWORK_LEVEL and \
           (packet[0] & 0xD8) == FragHeadPacketAnalyzer.SICSLOWPAN_DISPATCH_FRAG1
  
  def analyzePacket(self, packet):
    hdr_size = 0
    
    if (packet[0] & 0xF8) == FragHeadPacketAnalyzer.SICSLOWPAN_DISPATCH_FRAG1 :
      hdr_size = 4
    elif (packet[0] & 0xF8) == FragHeadPacketAnalyzer.SICSLOWPAN_DISPATCH_FRAGN:
      hdr_size = 5
    
    datagram_size = ((packet[0] & 0x07) << 8) + packet[1]
    datagram_tag = packet.getInt(2, 2)

    offset = 0
    if hdr_size == 5:
      offset = packet[4] * 8
    
    packet.pos += hdr_size

    header = FragHeader()
    header.datagram_size = datagram_size
    header.datagram_tag = datagram_tag
    header.offset = offset

    packet.add_header(header)

    return PacketAnalyzer.ANALYSIS_OK_CONTINUE

class FragHeader:

  def __str__(self):
    verbose = []
    verbose.append("Frag Header ")

    if self.offset == 0 :
      verbose.append("first\n")
    else:
      verbose.append("nth\n")
    
    verbose.append("size = ")
    verbose.append(str(self.datagram_size))
    verbose.append(", tag = ")
    verbose.append(str(self.datagram_tag).zfill(4))
    
    if self.offset > 0:
      verbose.append(", offset = ")
      verbose.append(str(self.offset))

    return ''.join(verbose)
