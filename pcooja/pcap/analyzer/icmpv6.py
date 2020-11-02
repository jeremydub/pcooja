from ..packet import *
from ..utils import human_readable_address

class ICMPv6Analyzer:

  def matchPacket(self, packet):
    return packet.level == PacketAnalyzer.APPLICATION_LEVEL and packet.lastDispatch == PacketAnalyzer.PROTO_ICMP

  def analyzePacket(self, packet):
    type = packet[0] & 0xff
    code = packet[1] & 0xff

    # remove type, code, crc
    packet.consume_bytes_start(4)

    header = ICMPv6Header()

    header.type = type
    header.code = code

    if type == 155:
      if code == ICMPv6Header.RPL_CODE_DIS:
        packet.consume_bytes_start(2)
      elif code == ICMPv6Header.RPL_CODE_DIO:
        instance_id = packet[0] & 0xff
        version = packet[1] & 0xff
        rank = ((packet[2] & 0xff) << 8) + (packet[3] & 0xff)
        mop = (packet[4] >> 3) & 0x07
        dtsn = packet[5] & 0xFF
        """
        flags = packets[6]
        reserved = packets[7]
        """
        dodag_id = []
        for i in range(16):
          dodag_id.append(packet[8+i])

        packet.consume_bytes_start(8+16)

        header.instance_id = instance_id
        header.version = version
        header.rank = rank
        header.mop = mop
        header.dtsn = dtsn
        header.dodag_id = dodag_id

        # RPL Options

        while packet.get_payload_size() > 0:
          type=packet[0]
          length=packet[1]
          packet.consume_bytes_start(2)

          if type == ICMPv6Header.RPL_OPTION_DODAG_CONF:
            ocp = ((packet[8] & 0xff) << 8) + (packet[9] & 0xff)

            header.ocp = ocp
          """
          elif type == ICMPv6Header.RPL_OPTION_PREFIX_INFO:
            prefix = []
            for i in range(16):
              prefix.append(packet[i])
            packet.prefix_info = prefix
          """
          packet.consume_bytes_start(length)

      elif code == ICMPv6Header.RPL_CODE_DAO:
        instance_id = packet[0] & 0xff
        header.instance_id = instance_id
        is_dodagid_present = (packet[1] & 0x40) != 0

        if is_dodagid_present:
          dodag_id = []
          for i in range(16):
            dodag_id.append(packet[4+i])
          header.dodag_id = dodag_id

        # RPL Options

        while packet.get_payload_size() > 0:
          type=packet[0]
          length=packet[1]
          packet.consume_bytes_start(2)

          if type == ICMPv6Header.RPL_OPTION_RPL_TARGET:
            prefix_length = packet[1]
            prefix = []
            for i in range(prefix_length//8):
              prefix.append(packet[2+i])
            header.target_prefix = prefix

        """
        TODO
        """

      elif code == ICMPv6Header.RPL_CODE_DAO_ACK:
        """
        TODO
        """
    packet.add_header(header)

    return PacketAnalyzer.ANALYSIS_OK_FINAL

class ICMPv6Header:

  ECHO_REQUEST = 128
  ECHO_REPLY = 129
  GROUP_QUERY = 130
  GROUP_REPORT = 131
  GROUP_REDUCTION = 132
  ROUTER_SOLICITATION = 133
  ROUTER_ADVERTISEMENT = 134
  NEIGHBOR_SOLICITATION = 135
  NEIGHBOR_ADVERTISEMENT = 136

  RPL_TYPE = 155

  RPL_CODE_DIS = 0 
  RPL_CODE_DIO = 1 
  RPL_CODE_DAO = 2
  RPL_CODE_DAO_ACK = 3

  RPL_OPTION_DODAG_CONF = 4
  RPL_OPTION_PREFIX_INFO = 8
  RPL_OPTION_RPL_TARGET = 5

  FLAG_ROUTER = 0x80
  FLAG_SOLICITED = 0x40
  FLAG_OVERRIDE = 0x20

  ON_LINK = 0x80
  AUTOCONFIG = 0x40

  SOURCE_LINKADDR = 1
  TARGET_LINKADDR = 2
  PREFIX_INFO = 3
  MTU_INFO = 5

  TYPE_NAME = [
    "Echo Request", "Echo Reply", \
    "Group Query", "Group Report", "Group Reduction", \
    "Router Solicitation", "Router Advertisement", \
    "Neighbor Solicitation", "Neighbor Advertisement", "Redirect", \
    "Router Renumber", "Node Information Query", "Node Information Response"]

  BRIEF_TYPE_NAME=[
    "ECHO REQ", "ECHO RPLY", \
    "GRP QUERY", "GRP REPORT", "GRP REDUCTION", \
    "RS", "RA", \
    "NS", "NA", "REDIRECT", \
    "ROUTER RENUMBER", "NODE INFO QUERY", "NODE INFO RESP"]

  def __str__(self):
    verbose = []
    verbose.append("\033[38;5;3m")
    verbose.append("ICMPv6")
    if self.type >= 128 and (self.type - 128) < len(ICMPv6Header.TYPE_NAME):
      verbose.append(" Type: ")
      verbose.append(str(ICMPv6Header.TYPE_NAME[self.type - 128]))
      verbose.append(", Code:")
      verbose.append(str(self.code))
    elif self.type == ICMPv6Header.RPL_TYPE:
      verbose.append(" Type: RPL, Code: ")
      if self.code == ICMPv6Header.RPL_CODE_DIS:
        verbose.append("DIS")
      elif self.code == ICMPv6Header.RPL_CODE_DIO:
        verbose.append("DIO\n")

        verbose.append("InstanceID: ")
        verbose.append(str(self.instance_id))
        verbose.append(", Version: ")
        verbose.append(str(self.version))
        verbose.append(", Rank: ")
        verbose.append(str(self.rank))
        verbose.append(", MOP: ")
        verbose.append(str(self.mop))
        verbose.append(", DTSN: ")
        verbose.append(str(self.dtsn))

        # RPL Options
        if hasattr(self,"ocp"):
          verbose.append(", OCP: ")
          verbose.append(str(self.ocp))

        verbose.append("\nDODAG ID: ")
        verbose.append(human_readable_address(self.dodag_id))

      elif self.code == ICMPv6Header.RPL_CODE_DAO:
        verbose.append("DAO")
      elif self.code == ICMPv6Header.RPL_CODE_DAO_ACK:
        verbose.append("DAO ACK")
      else:
        verbose.append(str(self.code))
    verbose.append("\033[0m")
    return ''.join(verbose)

  def is_DIO(self):
    """ Return if the packet is an RPL packet and a DIO packet """
    return self.type == ICMPv6Header.RPL_TYPE and self.code == ICMPv6Header.RPL_CODE_DIO

  def is_DAO(self):
    """ Return if the packet is an RPL packet and a DAO packet """
    return self.type == ICMPv6Header.RPL_TYPE and self.code == ICMPv6Header.RPL_CODE_DAO
  
  def is_DIS(self):
    """ Return if the packet is an RPL packet and a DIS packet """
    return self.type == ICMPv6Header.RPL_TYPE and self.code == ICMPv6Header.RPL_CODE_DIS


  def __repr__(self):
    verbose = []
    verbose.append("\033[38;5;3m")
    verbose.append("ICMPv6 ")
    if self.type >= 128 and (self.type - 128) < len(ICMPv6Header.TYPE_NAME):
      verbose.append(str(ICMPv6Header.TYPE_NAME[self.type - 128]))
      verbose.append(" Code:")
      verbose.append(str(self.code))
    elif self.type == 155:
      verbose.append(" RPL")
      if self.code == ICMPv6Header.RPL_CODE_DIS:
        verbose.append(" DIS")
      elif self.code == ICMPv6Header.RPL_CODE_DIO:
        verbose.append(" DIO")

        verbose.append(", Inst.: ")
        verbose.append(str(self.instance_id))
        verbose.append(", Vers.: ")
        verbose.append(str(self.version))
        verbose.append(", Rank: ")
        verbose.append(str(self.rank))

      elif self.code == ICMPv6Header.RPL_CODE_DAO:
        verbose.append(" DAO")
      elif self.code == ICMPv6Header.RPL_CODE_DAO_ACK:
        verbose.append(" DAO ACK")
      else:
        verbose.append(str(self.code))
    verbose.append("\033[0m")
    return ''.join(verbose)
