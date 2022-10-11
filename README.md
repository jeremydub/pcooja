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

## Usage

See `examples/examples.py`

## ToDo's

- Remove dependency from docker container by handling cooja execution command (instead of calling 'cooja' command which is an alias defined in the container)
- Refactor XML file generation (use dedicated module) instead of custom ugly class
- Use f-string instead of concatenation
- extract shell related command from Simulation class to a new SimulationRunner class 
- Remove RSSI part from node done by Maximilien C.

## Known problems

- You cannot set a motetype of target A (e.g. SkyMoteType) to a mote of different target B (e.g. Z1MoteType). This is a problem when loading a topology of nodes from a .csc file where you want a different target that the one specified in the topology.
- Start-up delay: not working anymore in Cooja
- Cleaning of some generated files (firmwares/error logs)


# Cooja Log Viewer

This package has a built-in TUI Cooja log viewer compatible with Contiki-NG. In order to use it, simply pass a `.log` file :

```bash
python3 -m pcooja.logviewer simulation.log
```

It is also possible to specify a folder containing multiple `.log` files and the viewer will let you choose which one to view :

```bash
python3 -m pcooja.logviewer path/to/folder/containing/logs
```

... or pass nothing to use current directory :

```bash
python3 -m pcooja.logviewer
```

## Key bindings

When viewing a Cooja log, you can navigate using up/down/left/right arrows. Several commands/filters are also available when typing specific keys :

|       **Name**      | **Key Binding** | **Command format** |
|:-------------------:|:-------:|:---------------:|
| Filter nodes        |    n    | Space separated integers/range :`1 2 5-8` |
| Messages containing |    c    | Sentence to match : `Hello World` |
| Filter time         |    t    | Time constraints as : `>30<50` (after 30sec and before 50sec) |
| Filter log module   |    m    | name of log module: `RPL` |
| Filter log level    |    l    | name of log level: `error` |
| Reset filters       |    r    | Remove every filter |
| Script              |    s    | Select a script to apply on log |
| Search              |    /    | Sentence to search : `Hello World` |

## Scripts

The viewer support scripting, allowing for running python functions on the current log. This is useful for computing metrics and shows simulation summaries.

All you need to do is creating a python module in which you define one or multiple functions that take `log` as a unique parameter. The log viewer will only match functions that have that single parameter with that name. Docstring is used in log viewer as a description of the script.

For instance, let say we want to display, for each node, the amount of serial messages that contain the word "Received response" :

```python
def count_received_messages(log):
    """
    List, for each node, the count of serial messages containing "Received response"
    """

    for node_id in log.get_node_ids():
        count = log.get_messages(node_id=node_id, contain="Received response")
        print(f"Node #{node_id} : {len(count)} messages")
```

To import your scripts, simply pass it to the command using one (or multiple) `-s` flag.

```bash
python3 -m pcooja.logviewer -s ~/pcooja/examples/logviewer_script.py
```


