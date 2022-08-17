from pcooja.radio.medium import RadioMedium
from .event import *
from math import *

CC2420_CONF_CCA_THRESH = -45 #From CC2420 contiki
CC2420_RSSI_OFFSET = -45 #from the cc2420 datasheet
CC2420_MIN_RX_POWER = -94 # from the z1 datasheet
CC2420_MIN_CCA_POWER = -77 # cc2420 default value from the cc2420 datasheet
CC2420_CONTIKI_CCA_POWER = CC2420_CONF_CCA_THRESH+CC2420_RSSI_OFFSET #contiki CCA sensibility

#RX power = RSSI_VAL + RSSI_OFFSET
class DGRM(RadioMedium):
  def __init__(self, edges=None, motes=None,event=None):
    """
        Define a DGRM radio medium based on edges or on a list of motes \
            and a transmitting range.
    """
    #RadioMedium.__init__(self)

    if(edges != None):
      self.edges = edges
    else:
      self.edges = []
    self.motes = motes
    self.event = event

  def is_in_range(self, mote1, mote2):
    """ Only check if there are an edge between mote1 and 2. """
    for edge in self.edges:
      if (edge.source_id == mote1.id and edge.dest_id == mote2.id):
        return True
    return False

  def gen_edges(self, motes, transmitting_range, interference_range=0, ratio=1.0):
    """ Generates edges for each mote in the transmitting range. """
    for mote1 in motes:
      for mote2 in motes:
        if (mote1.id != mote2.id):
          if(mote1.euclidian_distance(mote2) <= transmitting_range):
            self.edges.append(DGRM.DGRMEdge(mote1.id, mote2.id, ratio=ratio))
          elif(mote1.euclidian_distance(mote2) <= interference_range):
            self.edges.append(DGRM.DGRMEdge(mote1.id, mote2.id, ratio=0))

  def get_edges(self, mote_id):
    """ Get all edge with source or dest the mote id mote_id. """
    edges = []
    for edge in self.edges:
      if(edge.source_id == mote_id or edge.dest_id == mote_id):
        edges.append(edge)
    return edges  

  def get_edge(self, source_id, dest_id):
    """ Get edge with source and dest the mote id mote_id. """
    edges = []
    for edge in self.edges:
      if(edge.source_id == source_id and edge.dest_id == dest_id):
        edges.append(edge)
    return edges

  def add_edge(self, edge, symetric=False):
    """ Add an edge to the edges list."""
    self.edges.append(edge)
    if symetric:
      edge_sym = edge.clone()
      edge_sym.source_id = edge.dest_id
      edge_sym.dest_id = edge.source_id
      self.edges.append(edge_sym)

  def add_event(self, event):
    if(self.event == None):
      self.event = DGRMEvent([])
    self.event.add_event(event)

  def get_event_time_s(self):
    """Return a list a time in second of modification event """
    event_time = []
    if self.event != None:
      for eventEdge in self.event.eventEdges:
        event_time.append(eventEdge.get_time_s())
    return list(set(event_time))

  def gen_edges_cc2420(self, motes, rx_ratio=1.0, path_loss_exponant=2.3, channel=-1):
    """ Generates edges for each mote in the transmitting range. """
    for mote1 in motes:
      for mote2 in motes:
        if (mote1.id != mote2.id):
          distance = mote1.euclidian_distance(mote2)
          rx_power = DGRM.rxpower_cc2420(distance,path_loss_exponant=path_loss_exponant)
          if(rx_power > CC2420_CONTIKI_CCA_POWER): #based on the minimal CCA power
            self.edges.append(DGRM.DGRMEdge(mote1.id, mote2.id, \
                    ratio=rx_ratio, signal=rx_power, channel=channel))
          elif(rx_power > CC2420_MIN_RX_POWER ): #based on the minimal rx power
            self.edges.append(DGRM.DGRMEdge(mote1.id, mote2.id, \
                    ratio=0, signal=rx_power, channel=channel))

  def get_type(self):
    return RadioMedium.RadioMediumType.DGRM

  def to_xml(self, xb):
    """
      Write the configuration of the radio medium in a XML file xb.
    """
    xb.write('<radiomedium>')
    xb.indent()
    xb.write('org.contikios.cooja.radiomediums.DirectedGraphMedium')
    if self.motes != None:
      for mote in self.motes:
        mote.basseRSSI_to_xml(xb)
    for edge in self.edges:
      edge.to_xml(xb)
    xb.unindent()
    xb.write('</radiomedium>')

  def event_to_xml(self, xb):
    if(self.event != None):
      self.event.to_xml(xb)

  @staticmethod
  def from_xml(xml):
    """ 
      Return a Radio Medium object from the XML.
    """

    if "org.contikios.cooja.radiomediums.DirectedGraphMedium" not in xml.text:
        return None
    radiomedium_xml = xml.xpath("radiomedium")
    edges = []
    for edge in radiomedium_xml.xpath("edge"):
      edges.append(DGRM.DGRMEdge.from_xml(edge))
    if "org.contikios.cooja.plugins.DGRMEvent" in xml.text:
      self.event = self.event.from_xml(xml.find(".//plugin[@name='org.contikios.cooja.plugins.DGRMEvent']"))
    return DGRM(edges=edges)

  def __str__(self):
    output = 'DGRM: '+str(len(self.edges)) + " edges.\n"
    for edge in self.edges:
      output += str(edge) + "\n"
    return output

  def __repr__(self):
    return self.__str__()

  @staticmethod
  def dBmTomW(power):
    '''Convert a input in dBm to an output in mW.'''
    return pow(10, float(power)/10)

  @staticmethod
  def mWTodBm(power):
    '''Convert a input in mW to an output in dBm.'''
    return 10 * log10(power)

  @staticmethod
  def rxPowerFriis(distance, F_c=2.4, tx_power=0, G=0, path_loss_exponant=2):
    ''' Compute the theorical receive power for a giving distance based 
      on the channel and the distance according the Friis formula gived
      in the ASP011 (p.11) distance is in meter
      F_c is the frequency center in Ghz
      tx_power is the Transtion power in dBm
      G is the sum of the receiver and transmitter gain
      path_loss_exponant is the exponant used according the environnement:
        Free space            2
        Urban area            2.7 to 3.5
        Suburban area         3 to 5
        Indoor (line-of-sight) 1.6 to 1.8
      return the receive power in dBm'''

    c = 299792458 #speed of light
    R = distance #radius
    F_c = F_c * pow(10, 9) #convert the frequency channel center from Ghz to Hz

    R = max(R, 0.0001)
    return tx_power + G + (20*log10(c / F_c)) - (10 * log10(4 * pi * R) * path_loss_exponant)
    # sigma = c / F_c
    # return tx_power + G + (20 * log10(sigma/ (4 * pi * R)))
  
  @staticmethod
  def rxpower_cc2420(distance, path_loss_exponant=2.4):
    ''' Return if a message is received by the cc2420 according a distance.
        Based on the CC2420 datasheet and Zolertia Z1 datasheet
        cc2420 can receive message with a power of -100 dBm
        but cc2420 can only detect message with a power of -77 dBm (CCA)'''
    return DGRM.rxPowerFriis(distance, F_c=2.4, tx_power=0, G=0, path_loss_exponant=path_loss_exponant)

  @staticmethod
  def is_received_cc2420(distance, path_loss_exponant=2.4):
    ''' Return if a message is received by the cc2420 according a distance.
        Based on the CC2420 datasheet and Zolertia Z1 datasheet
        cc2420 can receive message with a power of -100 dBm
        but cc2420 can only detect message with a power of -77 dBm (CCA)'''
    return DGRM.rxpower_cc2420(distance, path_loss_exponant) > CC2420_CONTIKI_CCA_POWER

  @staticmethod
  def get_max_cc2420_range(path_loss_exponant=2, minimal_sensibility=CC2420_MIN_RX_POWER):
    ''' Return the maximum range of a message for a gived path loss exponant and
    and minimal sensibility. '''
    distance = 0
    while DGRM.rxpower_cc2420(distance+1, path_loss_exponant) > minimal_sensibility:
      distance += 1
    return distance


  @staticmethod
  def rxpower_cc1310(distance, path_loss_exponant=2.4):
    ''' Return the power received by the cc1310 according a distance in dBm.
        Based on the CC1310 datasheet
        Excellent Receiver Sensitivity -124 dBm Using  Long-Range Mode, 
        -110 dBm at 50 kbps (Sub-1 GHz)
        -115 dBm 4.8 kbps, OOK, 40-kHz RX bandwidth, BER = 10-2 868 MHz and 915 MHz
        Programmable Output Power up to +15 dBm, TX at +10 dBm: 13.4 mA
        868 MHz
        '''
    return DGRM.rxPowerFriis(distance, F_c=0.868, tx_power=10, G=0, path_loss_exponant=path_loss_exponant)


  class DGRMEdge:
    def __init__(self, source_id, dest_id, ratio=1.0, signal=-10.0, lqi=105, \
                  delay=0, channel=-1):
      """ Initialise an Edge in the DGRM graph.
          source_id and dest_id are the ID of the source and the dest mote.
      """
      self.source_id = source_id
      self.dest_id = dest_id
      self.ratio = ratio
      self.signal = signal
      self.lqi = lqi
      self.delay = delay
      self.channel = channel

    def to_xml(self, xb):
      """
        Write the configuration of the radio medium in a XML file xb.
      """
      xb.write('<edge>')
      xb.indent()
      xb.write('<source>'+str(self.source_id)+'</source>')
      xb.write('<dest>')
      xb.indent()
      xb.write('org.contikios.cooja.radiomediums.DGRMDestinationRadio')
      xb.write('<radio>'+str(self.dest_id)+'</radio>')
      xb.write('<ratio>'+str(round(self.ratio, 2))+'</ratio>')
      xb.write('<signal>'+str(round(self.signal, 2))+'</signal>')
      xb.write('<lqi>'+str(self.lqi)+'</lqi>')
      xb.write('<delay>'+str(self.delay)+'</delay>')
      xb.write('<channel>'+str(self.channel)+'</channel>')
      xb.unindent()
      xb.write('</dest>')
      xb.unindent()
      xb.write('</edge>')

    def __str__(self):
      return 'DGRM.DGRMEdge '+ str(self.source_id) + " > " + \
            str(self.dest_id) + " Ratio " + str(self.ratio) + " Signal " + \
            str(self.signal) + " delay " + str(self.delay) + " LQI " + \
            str(self.lqi) + " channel " + str(self.channel)

    def __repr__(self):
      return self.__str__()

    def clone(self):
      return DGRM.DGRMEdge(self.source_id, self.dest_id, self.ratio, self.signal, \
        self.lqi, self.delay, self.channel)


    @staticmethod
    def from_xml(xml):
      """ 
        Return a Radio Medium object from the XML.
      """
      source_id = int(xml.xpath("source/text()")[0])
      # dest
      dest = xml.xpath("dest")
      dest_id = int(dest[0].xpath("radio/text()")[0])
      ratio = float(dest[0].xpath("ratio/text()")[0])
      signal = float(dest[0].xpath("signal/text()")[0])
      lqi = int(dest[0].xpath("lqi/text()")[0])
      delay = int(dest[0].xpath("delay/text()")[0])
      channel = int(dest[0].xpath("channel/text()")[0])
      return DGRM.DGRMEdge(source_id, dest_id, ratio, signal, \
                lqi, delay, channel)

RadioMedium.REGISTERED_MEDIUMS.append(DGRM)
