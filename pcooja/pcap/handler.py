import collections
import struct
import math
import pickle
import os
import hashlib

from .packet import *
from .analyzer.ieee802154 import *
from .analyzer.fraghead import *
from .analyzer.iphc import *
from .analyzer.ipv6 import *
from .analyzer.icmpv6 import *
from .utils import address_from_str

class PcapHandler:
  def __init__(self, filepath, remove_duplicate=True, relative_time=True, use_pickle=True):
    self.filepath = filepath
    self.remove_duplicate = remove_duplicate
    self.relative_time = relative_time
    self.pcap_file_hash = self.get_pcap_file_hash()
    self.frames = []

    parts = self.filepath.split('.')
    pickle_file = ".".join(parts[:-1])+".pickle"

    if use_pickle and os.path.exists(pickle_file):
      handler = pickle.load(open(pickle_file, "rb"))
      if handler.pcap_file_hash == self.pcap_file_hash:
        self.frames = handler.frames

    if len(self.frames) == 0:
      self.process_file()
      self.link_frames()

      if use_pickle:
        if not os.path.exists(pickle_file):
          pickle.dump( self, open(pickle_file,"wb"))
        else:
          handler = pickle.load(open(pickle_file, "rb"))
          if handler.pcap_file_hash != self.pcap_file_hash:
            pickle.dump( self, open(pickle_file,"wb"))

  def process_file(self):
    # 4 bytes pcap header
    pcap_cooja_header = bytearray([161,178,195,212])
    # Delay (in sec) within 2 packets with same LL sender address and Seq Numb are considered duplicated
    delay = 30.0

    f=open(self.filepath, 'rb')

    # get file size in bytes
    f.seek(0, 2)
    eof = f.tell()

    f.seek(0, 0)
    pos=0

    # skip pcap file header
    header=bytearray(f.read(24))

    if header[:4] != pcap_cooja_header:
      raise Exception("Pcap header not found in file")
    pos += 24

    packets=[]
    timestamp=None

    # Each entry of the dictionary : LL sender address + Frame Seq Number => packet
    # Used to detect duplicated frame at LL level
    if self.remove_duplicate:
      id_to_packets = {}

    while pos < eof:
      # Read pcap packet header
      current_timestamp=struct.unpack_from(">I", f.read(4))[0]
      milliseconds=struct.unpack_from(">I", f.read(4))[0]
      if milliseconds > 0:
        current_timestamp += float(milliseconds) / 1000000
      length=struct.unpack_from(">I", f.read(4))[0]

      if self.relative_time:
        if timestamp == None:
          timestamp=current_timestamp
        current_timestamp -= timestamp

      # Skip duplicated length
      f.read(4)
      # Read packet
      packet_bytes=bytearray(f.read(length))
      # create packet object
      packet = Packet(packet_bytes)

      packet.timestamp = current_timestamp
      self.analyse_packet(packet)

      if self.remove_duplicate:
        # Defining unique key representing the frame: LL sender address + Frame Seq Num.
        key = ""
        if hasattr(packet.get_header(IEEE802154Header), 'source'):
          key += str(packet.get_header(IEEE802154Header).source) + "_"
        if hasattr(packet.get_header(IEEE802154Header), 'seq_number'):
          key += str(packet.get_header(IEEE802154Header).seq_number)

        # Check if packet ID/key is in dictionary, meaning it is a duplicate
        if key not in id_to_packets or ( key in id_to_packets and \
            current_timestamp-id_to_packets[key].timestamp > delay) or \
            packet.get_header(IEEE802154Header).fcf_type == IEEE802154Header.ACKFRAME:
          id_to_packets[key] = packet
          packets.append(packet)
        else:
          id_to_packets[key].duplicate_counter += 1
      else:
        packets.append(packet)
      pos += 16 + length
    f.close()

    # Frames have now been read and stored as objects
    self.frames=packets

  def analyse_packet(self, packet):
    analyzers = [IEEE802154Analyzer(), FragHeadPacketAnalyzer(),\
                 IPHCPacketAnalyzer(), IPv6PacketAnalyzer(), ICMPv6Analyzer()]
    analyze = True
    while analyze:
      analyze = False
      for i in range(len(analyzers)):
        analyzer = analyzers[i]
        if analyzer.matchPacket(packet):
          res = analyzer.analyzePacket(packet)
          if res != PacketAnalyzer.ANALYSIS_OK_CONTINUE:
            # this was the final or the analysis failed - no analyzable payload possible here...
            return 1

          # continue another round if more bytes left
          analyze = packet.hasMoreData()
          break
    return 1

  def get_pcap_file_hash(self):
    hasher = hashlib.md5()
    with open(self.filepath, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()

  def group_frames_by_attribute(self, frames, key_selector):
    attribute_to_frames = {}
    for packet in frames:
      key = key_selector(packet)
      
      # check if key is hashable, if not use string representation
      if not(isinstance(key, collections.Hashable)):
        key = str(key)

      if not(attribute_to_frames.has_key(key)):
        attribute_to_frames[key]=[]
      attribute_to_frames[key].append(packet)
    return attribute_to_frames

  def link_frames(self):
    # filter functions
    contains_app_message = lambda packet : packet.has_header(UDPHeader)

    messages = list(filter(contains_app_message, self.frames))
    n = len(messages)
    queue = []

    for packet in messages:
      new_message = True
      for i in range(len(queue)):
        if self.is_nexthop_packet(packet, queue[i]):
          new_message = False
          queue[i].next_hop_frame = packet
          packet.previous_hop_frame = queue[i]
          queue[i] = packet
          break
      if new_message :
        queue.append(packet)

    seqnum_to_packets = {}

    # Link ack frames to corresponding frames
    for packet in self.frames:
      header = packet.get_header(IEEE802154Header)
      seq_number = header.seq_number
      if header.fcf_type == IEEE802154Header.ACKFRAME:
        if seq_number in seqnum_to_packets:
          seqnum_to_packets[seq_number].ack_frame = packet
          del(seqnum_to_packets[seq_number])
      elif header.fcf_ack_requested:
        seqnum_to_packets[seq_number] = packet

  def is_nexthop_packet(self,packet2, packet1):
    """
    Return True if packet2 immediately follows packet1 in term of hop in the path.
    """
    ll_header1 = packet1.get_header(IEEE802154Header)
    ll_header2 = packet2.get_header(IEEE802154Header)
    ip_header1 = packet1.get_header(IPv6Header)
    ip_header2 = packet2.get_header(IPv6Header)

    # True if packet1 and packet2 have same ip address information
    # and if packet2 LL address is packet1 nexthop
    cond1 = ll_header1.destination ==ll_header2.source and \
           ip_header1.source == ip_header2.source and \
           ip_header1.destination == ip_header2.destination

    # True if application messages are identical
    cond2 = False
    if packet1.has_header(UDPHeader) and packet2.has_header(UDPHeader):
      app_header1 = packet1.get_header(UDPHeader)
      app_header2 = packet2.get_header(UDPHeader)
      cond2 = app_header1.src_port == app_header2.src_port and \
              app_header1.dest_port == app_header2.dest_port and \
              str(packet1.getPayload()) == str(packet2.getPayload())
    return cond1 and cond2

  def get_frames(self):
    return self.frames

  def get_datagrams(self, ll_source=None):
    # filter frames that contain udp datagrams
    is_udp_datagram = lambda packet : packet.has_header(UDPHeader) and \
                             packet.previous_hop_frame == None
    datagrams = filter(is_udp_datagram, self.frames)

    if ll_source != None:
      # Convert address if string representation is given
      if type(ll_source) == str:
        ll_source = address_from_str(ll_source, 8)
      source_filter = lambda p : p.get_header(IEEE802154Header).source == ll_source
      datagrams = filter(source_filter, datagrams)

    datagrams = list(filter(lambda d: not d.get_header(IPHCHeader).nhc, datagrams))

    return datagrams
  
