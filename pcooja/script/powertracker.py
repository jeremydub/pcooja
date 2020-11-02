from ..runner import ScriptRunner

class PowerTrackerScript(ScriptRunner):
  """ Load the default script add some the powertracker trace at the end
      of the simulation: log all transmited message:
      time:id:message
  """
  def __init__(self, timeout, with_gui=False):
    super(self.__class__, self).__init__(timeout, with_gui)


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

      #we always write the timeout value
      xb.write("TIMEOUT("+str(1000*self.timeout)+");")
      
      script = """
/*
 * Initialise the PowerTracker plugin and write all messages in the log file.
 */

plugin=0;

/* This function is called at the timeout */
timeout_function = function my_fun() {
  if(plugin == 0){
    /* Extract PowerTracker statistics */
    plugin = mote.getSimulation().getCooja().getStartedPlugin("PowerTracker");
  }
  if (plugin != null) {
      stats = plugin.radioStatistics();
      log.log(time + ":PowerTracker:Extracted statistics:start\\n");
      log.log(stats + "\\n");
      log.log(time + ":PowerTracker:Extracted statistics:end\\n");
    }
  log.testOK()
}

while (true) {
  log.log(time + ":" + id + ":" + msg +"\\n");
  YIELD();
}
"""
      xb.write(script)
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

      #Add the PowerTracker plugin
      xb.write("<plugin>")
      xb.indent()
      xb.write("PowerTracker")
      xb.write("<width>518</width>")
      xb.write("<z>3</z>")
      xb.write("<height>400</height>")
      xb.write("<location_x>493</location_x>")
      xb.write("<location_y>29</location_y>")
      xb.unindent()
      xb.write("</plugin>")
