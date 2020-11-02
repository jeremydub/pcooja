from math import *
from enum import Enum

class DGRMEvent():
  def __init__(self, eventEdges=[]):
    """
        Define a DGRM radio medium based on edges or on a list of motes \
            and a transmitting range.
    """
    self.eventEdges = eventEdges;

  def add_event(self, event):
    "Add an event to the event list"
    self.eventEdges.append(event)

  def to_xml(self, xb):
    """
      Write the configuration of the radio medium in a XML file xb.
    """
    xb.write('<plugin>')
    xb.indent()
    xb.write('org.contikios.cooja.plugins.DGRMEvent')
    xb.write('<plugin_config>')
    xb.indent()

    for eventEdge in self.eventEdges:
      eventEdge.to_xml(xb)

    xb.unindent()
    xb.write('</plugin_config>')
    xb.write('<width>300</width>')
    xb.write('<z>5</z>')
    xb.write('<height>100</height>')
    xb.write('<location_x>710</location_x>')
    xb.write('<location_y>30</location_y>')
    xb.unindent()
    xb.write('</plugin>')

  @staticmethod
  def from_xml(xml):
    """ 
      Return a Radio Medium object from the XML.
    """
    eventEdges = []
    for eventEdge in xml.xpath("DGRMEventEdge"):
      self.eventEdges.append(DGRMEvent.DGRMEventEdge.from_xml(eventEdges))
    return DGRMEvent(eventEdges=eventEdges)

  def __str__(self):
    output = 'DGRMEvent: '+str(len(self.eventEdges)) + " event edges.\n"
    for edge in self.eventEdges:
      output += str(edge) + "\n"
    return output

  def __repr__(self):
    return self.__str__()

  class Action(Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    MODIFY = "MODIFY"

  class DGRMEventEdge:
    def __init__(self, action, time, edge):
      """ Initialise an Event Edge in the DGRM graph.
          @param action is an action : add, remove, modify
          @param time is the Execution time is in micro second.
                   A value of 1'000'000 is for one second.
          @param edge is a DGRM Edge.
      """
      self.action = action
      self.time = time
      self.edge = edge

    def to_xml(self, xb):
      """
        Write the configuration of the radio medium in a XML file xb.
      """
      xb.write('<DGRMEventEdge>')
      xb.indent()
      xb.write('<action>'+str(self.action.name)+'</action>')
      xb.write('<time>'+str(self.time)+'</time>')
      self.edge.to_xml(xb)
      xb.unindent()
      xb.write('</DGRMEventEdge>')

    def __str__(self):
      return 'DGRMEvent.DGRMEventEdge '+ str(self.action) + " at " + \
            str(self.time) + " " + str(self.edge)

    def __repr__(self):
      return self.__str__()

    def get_time_s(self):
      "Return the time in second"
      return float(self.time)/(1000*1000)

    @staticmethod
    def from_xml(xml):
      """ 
        Return a Radio Medium object from the XML.
      """
      action = DGRMEvent.Action(str(xml.xpath("action/text()")[0]))
      time = int(dest[0].xpath("time/text()")[0])
      edge = RadioMediumDGRM.DGRMEdge.from_xml(xml.xpath("edge"))
      return DGRMEvent.DGRMEventEdge(action, time, edge)
