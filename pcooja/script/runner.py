class ScriptRunner():
  def __init__(self, timeout, with_gui=False):
    """
      Define the script runner for the command prompt mode.
    """
    self.timeout = timeout
    self.with_gui = with_gui


  def to_xml(self, xb, gui_enabled):
    """
      Write the configuration of the ScriptRunner in a XML file xb.
    """
    raise NotImplementedError('to_xml not implemented')
