import copy

class PacketAnalyzer:
  ANALYSIS_FAILED = -1
  ANALYSIS_OK_CONTINUE = 1
  ANALYSIS_OK_FINAL = 2

  RADIO_LEVEL = 0
  MAC_LEVEL = 1
  NETWORK_LEVEL = 2
  APPLICATION_LEVEL = 3

  PROTO_UDP = 17
  PROTO_TCP = 6
  PROTO_ICMP = 58

class Packet :

  INFINITE_TIME = 1000000000

  def __init__(self, data, level=PacketAnalyzer.MAC_LEVEL):

    if type(data) == str:
      self.data=bytes.fromhex(data)
    elif type(data) == bytearray:
      self.data=data
    else:
      print(data)
      raise TypeError("Data type must be either str or bytes")

    self.level = level
    self.size = len(data)
    self.pos=0
    self.lastDispatch = 0

    self.headers = []

    self.next_hop_frame = None
    self.previous_hop_frame = None
    self.ack_frame = None
    self.duplicate_counter = 0

  def consume_bytes_start(self, n_bytes):
    self.pos += n_bytes

  def consume_bytes_end(self, n_bytes):
    self.size -= n_bytes

  def hasMoreData(self):
    return self.size > self.pos

  def get_payload_size(self):
    ''' Return the size of the payload '''
    return self.size - self.pos

  def get_packet_size(self):
    ''' Return the size of the packet (the payload + the header(s).'''
    return len(self.data)
    
  def get(self,index):
    if (index >= self.size) :
      return 0
    elif index < 0:
      return self.get((self.size+index)%self.size)
    else:
      return self.data[self.pos + index]

  def __getitem__(self, index):
    return self.get(index)

  def getInt(self, index, size):
    value = 0
    for i in range(size):
      value = (value << 8) + (self.get(index + i) & 0xFF)
    return value

  def get_payload(self, hex_view=False):
    if hex_view:
      return Packet.hex_view(self.data[self.pos:self.size])
    else:
      return copy.copy(self.data[self.pos:self.size])

  def copy(self, srcpos, arr, pos, length):
    for i in range(length):
      arr[pos + i] = self.get(srcpos + i)

  def add_header(self, header):
    self.headers.append(header)

  def get_header(self, header_class):
    for header in self.headers:
      if isinstance(header, header_class):
        return header
    return None

  def has_header(self, header_class):
    for header in self.headers:
      if isinstance(header, header_class):
        return True
    return False

  def hopcount(self):
    count = 1
    current_hop = self.next_hop_frame
    while current_hop != None:
      current_hop = current_hop.next_hop_frame
      count += 1
    return count

  def latency(self):
    send_time = self.timestamp
    current_hop = self
    while current_hop.next_hop_frame != None:
      current_hop = current_hop.next_hop_frame

    lost=current_hop.headers[0].destination[-1] != current_hop.headers[2].destination[-1]

    if lost:
      #print "lost: ", repr(current_hop)
      return Packet.INFINITE_TIME

    if current_hop.ack_frame == None:
      if current_hop.headers[0].fcf_ack_requested:
        #print "no ack:", repr(current_hop)
        return Packet.INFINITE_TIME
      else:
        received_time = current_hop.timestamp
    else:
      received_time = current_hop.ack_frame.timestamp
    return received_time - send_time

  def __eq__(self, other):
    if type(other) == Packet:
      return self.data == other.data
    else:
      return False

  def __hex__(self):
    data = self.data
    return Packet.hex_view(data)

  def __str__(self):
    hline = '-'*40
    verbose = [hline,"\n"]
    verbose.append("Time: "+str(self.timestamp))
    verbose.append("\n")
    verbose.append(hline)
    for header in self.headers:
      verbose.append("\n"+str(header))
      verbose.append("\n"+hline)
    payload=self.get_payload(hex_view=True)
    if len(payload)>0:
      verbose.append("\n"+str(payload))
      verbose.append("\n"+hline)

    return "".join(verbose)

  def __repr__(self):
    verbose = []
    i=0
    verbose.append("["+(str(self.timestamp)+"s").ljust(11)+"] ")
    for header in self.headers:
      repr_str=repr(header)
      if len(repr_str) > 0:
        if i > 0: verbose.append(" | ")
        verbose.append(repr_str)
        i += 1
    printable_payload = bytes(filter(lambda x : x > 31 and x <123, self.get_payload()))
    if len(printable_payload) > 0:
      verbose.append(" | ")
      verbose.append(printable_payload.decode())

    return "".join(verbose)

  @staticmethod
  def hex_view(data):
    verbose=[]
    for i in range(len(data)):
      if i % 16 == 0 and i > 0:
        verbose.append("  |  ")
        clean_data = bytes(map(lambda x : x if x >= 32 and x <127 else 46,data[i-16:i]))
        verbose.append((clean_data[:8]+clean_data[8:]).decode())
        verbose.append("\n")
      elif i % 8 == 0 and i > 0:
        verbose.append(" ")
      verbose.append(hex(data[i])[2:].zfill(2)+" ")
    if len(verbose) > 0:
      clean_data = bytes(map(lambda x : x if x >= 32 and x <127 else 46,data[-(len(data)%16):]))
      space_count = (16 - len(clean_data)) * 3
      if len(clean_data) < 8 :
        space_count += 1
      verbose.append((space_count*" ")+"  |  ")
      verbose.append((clean_data[:8]+clean_data[8:]).decode())
    return "".join(verbose)
