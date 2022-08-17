from .simulation import CoojaSimulation, CoojaSimulationWorker
from .topology import Topology
from .projectconf import ProjectConf
from .motes.z1 import Z1MoteType, Z1Mote
from .motes.sky import SkyMoteType, SkyMote
from .motes.cooja import CoojaMoteType, CoojaMote
from .log import Log
from .parser.csc import CSCParser
import pcooja.radio as radio

import os
import logging

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(30,38)

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

COLORS = {
    'WARNING': YELLOW,
    'INFO': BLUE,
    'DEBUG': MAGENTA,
    'CRITICAL': RED,
    'ERROR': RED
}

class ColoredFormatter(logging.Formatter):
    def __init__(self, msg="%(message)s", use_color = True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        msg = record.msg
        if not msg.endswith("\r"):
            msg = msg+"\n"
        if self.use_color and levelname in COLORS:
            message_color = f"[PCooja][{record.levelname}] {COLOR_SEQ % COLORS[levelname]}{msg}{RESET_SEQ}"
            record.msg = message_color

        return logging.Formatter.format(self, record)

logger = logging.getLogger("pcooja")
ch = logging.StreamHandler()
ch.terminator = ""
ch.setLevel(logging.DEBUG)
formatter = ColoredFormatter()
ch.setFormatter(formatter)
logger.addHandler(ch)

