from enum import Enum

class RadioMedium:
  """Abstract class of a radio medium"""
  Types = []

  def is_in_range(self, mote1, mote2):
    """ Return if the mote 2 can receive message from the mote 1."""
    raise NotImplementedError('is_in_range not implemented')

  def __str__(self):
    raise NotImplementedError('__str__ not implemented')

  def __repr__(self):
    raise NotImplementedError('__repr__ not implemented')
  def get_type(self):
    raise NotImplementedError('get_type() not implemented')

  def get_event_time_s(self):
    """ Send time of event in the radio medium (modification of some value """
    return []

  @staticmethod
  def from_xml(xml):
    """ Return a Radio Medium object from the XML."""
    for t in RadioMedium.Types:
        radio_medium = t.from_xml(xml)
        if radio_medium != None:
            return radio_medium
    raise Exception("Unsupported Format for the radiomedium " + xml.text)

  class RadioMediumType(Enum):
    UDGM = 1
    DGRM = 2
