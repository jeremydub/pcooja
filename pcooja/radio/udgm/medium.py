from pcooja.radio.medium import RadioMedium
from math import *

class UDGM(RadioMedium):
  def __init__(self, transmitting_range=100, interference_range=120, \
            success_ratio_tx=1.0, success_ratio_rx=1.0, motes=None):
    #RadioMedium.__init__(self)

    self.transmitting_range = transmitting_range
    self.interference_range = interference_range
    self.success_ratio_tx = success_ratio_tx
    self.success_ratio_rx = success_ratio_rx
    self.motes=motes

    if success_ratio_tx < 0 or success_ratio_tx > 1:
        raise Exception("'success_ratio_tx' must be in range [0,1]")
    
    if success_ratio_rx < 0 or success_ratio_rx > 1:
        raise Exception("'success_ratio_rx' must be in range [0,1]")


  def change_ranges(transmitting_range=None, interference_range=None):
    if transmitting_range != None:
      self.transmitting_range=transmitting_range
    
    if interference_range != None:
      self.interference_range=interference_range

  def is_in_range(self, mote1, mote2):
    return sqrt((mote1.x - mote2.x) ** 2 + (mote1.y - mote2.y) ** 2)<=self.transmitting_range

  def to_xml(self, xb):
    """
      Write the configuration of the radio medium in a XML file xb.
    """
    xb.write('<radiomedium>')
    xb.indent()
    xb.write('se.sics.cooja.radiomediums.UDGM')
    if self.motes != None:
      for mote in self.motes:
        mote.basseRSSI_to_xml(xb)
    xb.write('<transmitting_range>'+str(self.transmitting_range)+'</transmitting_range>')
    xb.write('<interference_range>'+str(self.interference_range)+'</interference_range>')
    xb.write('<success_ratio_tx>'+str(self.success_ratio_tx)+'</success_ratio_tx>')
    xb.write('<success_ratio_rx>'+str(self.success_ratio_rx)+'</success_ratio_rx>')
    xb.unindent()
    xb.write('</radiomedium>')

  def __str__(self):
    return 'UDGM '+str(self.transmitting_range) + ' ' + \
            str(self.interference_range) + ' ' + str(self.success_ratio_tx) + \
            ' ' + str(self.success_ratio_rx)

  def __repr__(self):
    return self.__str__()

  def get_type(self):
    return RadioMedium.RadioMediumType.UDGM

  @staticmethod
  def from_xml(xml):
    """ 
      Return a Radio Medium object from the XML.
    """
    if "org.contikios.cooja.radiomediums.UDGM" not in xml.text:
        return None
    transmitting_range = float(xml.xpath("transmitting_range/text()")[0])
    interference_range = float(xml.xpath("interference_range/text()")[0])
    success_ratio_tx = float(xml.xpath("success_ratio_tx/text()")[0])
    success_ratio_rx = float(xml.xpath("success_ratio_rx/text()")[0])
    return UDGM(transmitting_range, interference_range, \
            success_ratio_tx, success_ratio_rx)

RadioMedium.Types.append(UDGM)
