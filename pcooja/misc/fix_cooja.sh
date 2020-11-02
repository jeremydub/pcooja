COOJAFOLDER=$CONTIKI_PATH/tools/cooja/java/org/contikios/cooja
CONFIGFILE=$CONTIKI_PATH/tools/cooja/config/cooja_default.config
grep " org.contikios.cooja.plugins.PcapLogger" $CONFIGFILE 2> /dev/null > /dev/null
TEST=$?
if [ "$TEST" == 1 ] ; then
    cp $CONFIGFILE $CONFIGFILE.back
    LINE=`grep -n "org.contikios.cooja.Cooja.PLUGINS =" $CONFIGFILE | awk 'BEGIN{FS=":"} {print $1}'`
    sed -i "${LINE}s/$/ org.contikios.cooja.plugins.PcapLogger org.contikios.cooja.plugins.DGRMConfigurator org.contikios.cooja.plugins.BaseRSSIconf/" $CONFIGFILE
fi
if [ ! -f "$COOJAFOLDER/plugins/PcapLogger.java" ] ; then
    cp $MODULE_PATH/PcapLogger.java $MODULE_PATH/DGRMEvent.java $COOJAFOLDER/plugins/
    cp $COOJAFOLDER/plugins/analyzers/PcapExporter.java $COOJAFOLDER/plugins/analyzers/PcapExporter.java.back
    cp $COOJAFOLDER/radiomediums/DirectedGraphMedium.java $COOJAFOLDER/radiomediums/DirectedGraphMedium.java.back
    cp $MODULE_PATH/PcapExporter.java $COOJAFOLDER/plugins/analyzers/
    cp $MODULE_PATH/DirectedGraphMedium.java $COOJAFOLDER/radiomediums/
fi
