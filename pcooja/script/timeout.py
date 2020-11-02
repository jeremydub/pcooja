from pcooja.script.runner import ScriptRunner

class TimeoutScript(ScriptRunner):
  """ Load the default script: log all transmited message:
      time:id:message
  """
  def __init__(self, timeout, with_gui=False):
    super().__init__(timeout, with_gui)


  def to_xml(self, xb, gui_enabled):
    """
      Write the configuration of the ScriptRunner in a XML file xb.
    """
    #check if we can enable the script
    if(not gui_enabled or self.with_gui):
      xb.write("<plugin>")
      xb.indent()
      xb.write("org.contikios.cooja.plugins.ScriptRunner")
      xb.write("<plugin_config>")
      xb.indent()
      xb.write("<script>")
      xb.indent()
      xb.write("TIMEOUT("+str(1000*self.timeout)+",log.testOK());")
      
      #default: write the time, the id and the message for each messages
      text="""
while (true) {
  log.log(time + ":" + id + ":" + msg + "\\n");
  YIELD()
  }
"""
      xb.write(text)

      xb.unindent()
      xb.write("</script>")
      xb.write("<active>true</active>")
      xb.unindent()
      xb.write("</plugin_config>")
      xb.write("<width>600</width>")
      xb.write("<z>3</z>")
      xb.write("<height>700</height>")
      xb.write("<location_x>1120</location_x>")
      xb.write("<location_y>180</location_y>")
      xb.unindent()
      xb.write("</plugin>")
