import os.path
from ..runner import ScriptRunner

class LoadScript(ScriptRunner):
  def __init__(self, timeout, with_gui=False, script_file=None):
    """
      Define a script for cooja included in a file.
      The timeout value will be add by python at the start of the file.
      If the script file need some plugins, these plugins should be 
      loaded in the simulation.
    """
    super().__init__(timeout, with_gui)
    self.script_file = script_file

    if not os.path.exists(script_file):
      raise Exception("Script file doesn't exists.")

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

      #We add the timeout value
      xb.write("TIMEOUT("+str(1000*self.timeout)+");")
      
      #We have already check if the file exist.
      script_file = open(self.script_file, 'r')
      for line in script_file:
        xb.write(line)

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
