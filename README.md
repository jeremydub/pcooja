# pcooja
Pyhon 3 wrapper for Cooja Simulator. 

For now, it is only tested/working from inside [Contiki-NG docker container](https://hub.docker.com/r/contiker/contiki-ng/).

## Requirements

### Python
```bash
pip3 install -r requirements.txt
```

### Patching Cooja

In order to use Cooja motes with this module (i.e. mote that use JNI), you first need to patch Cooja simulator to allow for direct passing of the existing Cooja mote firmware (instead of requiring compilation before launch)
``` bash
cd path/to/contiki-ng/tools/cooja
git apply /path/to/pcooja/cooja.patch
```

## Installation
```
pip3 install -U .
```

# ToDo's

- Remove dependency from docker container by handling cooja execution command (instead of calling 'cooja' command which is an alias defined in the container)
- Refactor XML file generation (use dedicated module) instead of custom ugly class
- Use f-string instead of concatenation
- extract shell related command from Simulation class to a new SimulationRunner class 
- Remove RSSI part from node done by Maximilien C.

## Known problems

- You cannot set a motetype of target A (e.g. SkyMoteType) to a mote of different target B (e.g. Z1MoteType). This is a problem when loading a topology of nodes from a .csc file where you want a different target that the one specified in the topology.
- Start-up delay: not working anymore in Cooja
- Cleaning of some generated files (firmwares/error logs)
