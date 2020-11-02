from ..packet import *
from ..utils import human_readable_address

class IEEE802154Analyzer:

  def matchPacket(self, packet):
    return packet.level == PacketAnalyzer.MAC_LEVEL

  def nextLevel(self,packet_bytes, level):
    """
    this protocol always have network level packets as payload
    """
    return PacketAnalyzer.NETWORK_LEVEL

  def analyzePacket(self,packet):
    """
    create a 802.15.4 packet of the bytes and 'dispatch' to the next handler
    """
    pos = packet.pos

    # FCF field
    fcfType = int(packet.data[pos + 0] & 0x07)

    # booleans
    fcfSecurity = ((packet.data[pos + 0] >> 3) & 0x01) != 0
    fcfPending = ((packet.data[pos + 0] >> 4) & 0x01) != 0
    fcfAckRequested = ((packet.data[pos + 0] >> 5) & 0x01) != 0
    fcfIntraPAN = ((packet.data[pos + 0] >> 6) & 0x01) != 0

    fcfDestAddrMode = int((packet.data[pos + 1] >> 2) & 0x03)
    fcfFrameVersion = int((packet.data[pos + 1] >> 4) & 0x03)
    fcfSrcAddrMode = int((packet.data[pos + 1] >> 6) & 0x03)

    # Sequence number
    seqNumber = int(packet.data[pos + 2] & 0xff)

    # Addressing Fields
    destPanID = 0
    srcPanID = 0
    sourceAddress = None
    destAddress = None

    pos += 3

    if (fcfDestAddrMode > 0):
      destPanID = (packet.data[pos] & 0xff) + ((packet.data[pos + 1] & 0xff) << 8)
      pos += 2
      if fcfDestAddrMode == IEEE802154Header.SHORT_ADDRESS:
        destAddress = [0x00]*2
        destAddress[1] = packet.data[pos]
        destAddress[0] = packet.data[pos + 1]
        pos += 2
      elif fcfDestAddrMode == IEEE802154Header.LONG_ADDRESS:
        destAddress = [0x00]*8
        for i in range(8):
          destAddress[i] = packet.data[pos + 7 - i]
        pos += 8

    if fcfSrcAddrMode > 0:
      if fcfIntraPAN:
        srcPanID = destPanID
      else:
        srcPanID = int((packet.data[pos] & 0xff) + ((packet.data[pos + 1] & 0xff) << 8))
        pos += 2
      
      if fcfSrcAddrMode == IEEE802154Header.SHORT_ADDRESS:
        sourceAddress = [0x00]*2
        sourceAddress[1] = packet.data[pos]
        sourceAddress[0] = packet.data[pos + 1]
        pos += 2
      elif fcfSrcAddrMode == IEEE802154Header.LONG_ADDRESS:
        sourceAddress = [0x00]*8
        for i in range(8):
          sourceAddress[i] = packet.data[pos + 7 - i]
        pos += 8

    # update packet
    packet.pos = pos
    # remove CRC from the packet
    packet.consume_bytes_end(2)

    packet.level = PacketAnalyzer.NETWORK_LEVEL

    header = IEEE802154Header()
    header.seq_number = seqNumber
    header.fcf_type = fcfType
    header.fcf_security = fcfSecurity
    header.fcf_pending = fcfPending
    header.fcf_ack_requested = fcfAckRequested
    header.fcf_intra_pan = fcfIntraPAN
    header.dest_pan_id = destPanID
    header.src_pan_id = srcPanID
    header.source = sourceAddress
    header.destination = destAddress
    header.fcf_dest_addr_mode = fcfDestAddrMode
    header.fcf_frame_version = fcfDestAddrMode
    header.fcf_src_addr_mode = fcfSrcAddrMode

    packet.add_header(header)

    if fcfType == IEEE802154Header.ACKFRAME:
      # got ack - no more to do ...
      return PacketAnalyzer.ANALYSIS_OK_FINAL

    return PacketAnalyzer.ANALYSIS_OK_CONTINUE

class IEEE802154Header:

  #Addressing modes
  NO_ADDRESS = 0
  RSV_ADDRESS = 1
  SHORT_ADDRESS = 2
  LONG_ADDRESS = 3

  #Frame types
  BEACONFRAME = 0x00
  DATAFRAME = 0x01
  ACKFRAME = 0x02
  CMDFRAME = 0x03

  typeS = ["-", "D", "A", "C"]
  typeVerbose = ["BEACON", "DATA", "ACK", "CMD"]
  addrModeNames = ["None", "Reserved", "Short", "Long"]

  def __str__(self):
    verbose = []
    verbose.append("\033[38;5;34m")
    verbose.append("IEEE 802.15.4 ")
    verbose.append(IEEE802154Header.typeVerbose[self.fcf_type] if self.fcf_type < len(IEEE802154Header.typeVerbose) else "?")
    verbose.append(" #")
    verbose.append(str(self.seq_number))

    if self.fcf_type != IEEE802154Header.ACKFRAME:
      verbose.append("\nFrom ")
      if self.src_pan_id != 0:
        verbose.append("0x")
        verbose.append(hex(self.src_pan_id >> 8)[2:])
        verbose.append(hex(self.src_pan_id & 0xff)[2:])
        verbose.append('/')
      
      verbose.append(human_readable_address(self.source,1))
      verbose.append(" to ")
      if self.dest_pan_id != 0:
        verbose.append("0x")
        verbose.append(hex(self.dest_pan_id >> 8)[2:])
        verbose.append(hex(self.dest_pan_id & 0xff)[2:])
        verbose.append('/')
      verbose.append(human_readable_address(self.destination,1))

    verbose.append("\nSec = ")
    verbose.append(str(self.fcf_security))
    verbose.append(", Pend = ")
    verbose.append(str(self.fcf_pending))
    verbose.append(", ACK = ")
    verbose.append(str(self.fcf_ack_requested))
    verbose.append(", iPAN = ")
    verbose.append(str(self.fcf_intra_pan))
    verbose.append(", DestAddr = ")
    verbose.append(IEEE802154Header.addrModeNames[self.fcf_dest_addr_mode])
    verbose.append(", Vers. = ")
    verbose.append(str(self.fcf_frame_version))
    verbose.append(", SrcAddr = ")
    verbose.append(IEEE802154Header.addrModeNames[self.fcf_src_addr_mode])
    verbose.append("\033[0m")

    return ''.join(verbose)

  def __repr__(self):
    verbose = []
    verbose.append("\033[38;5;34m")
    verbose.append("802.15.4 ")
    verbose.append(IEEE802154Header.typeVerbose[self.fcf_type] if self.fcf_type < len(IEEE802154Header.typeVerbose) else "?")
    verbose.append(" #")
    verbose.append(str(self.seq_number).ljust(3))
    if self.source != None or self.destination != None:
      verbose.append(" :")
    if self.source != None:
      verbose.append(" "+human_readable_address(self.source[-2:],1))
    if self.source != None or self.destination != None:
      verbose.append(" ->")
    if self.destination != None:
      verbose.append(" "+human_readable_address(self.destination[-2:],1))
    verbose.append("\033[0m")

    return ''.join(verbose)
