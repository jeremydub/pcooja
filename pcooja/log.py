import os.path
import math
import re
    
def contiki_ng_default_parser(time, node_id, message):
    i_end = message.find("]")
    if message[0] == "[" and i_end != -1:
        i2 = message.find(':')
        log_level = message[1:i2].strip()
        if log_level == "DBG":
            log_level = Log.LEVEL_DBG
        elif log_level == "INFO":
            log_level = Log.LEVEL_INFO
        elif log_level == "DBG":
            log_level = Log.LEVEL_ERR
        elif log_level == "WARN":
            log_level = Log.LEVEL_WARN
        else:
            log_level = None
        log_module = message[i2+1:i_end].strip()
        log_module_id = Log.get_module_id(log_module)
    else:
        log_level = None
        log_module_id = None
    return (time, node_id, log_level, log_module_id, message[i_end+1:].strip())

class Log:
    LEVEL_ERR = 1
    LEVEL_WARN = 2
    LEVEL_INFO = 3
    LEVEL_DBG = 4

    TIME = 0
    NODE_ID = 1
    LOG_LEVEL = 2
    LOG_MODULE = 3
    MESSAGE = 4

    modules = {}
    revert_modules = {None: "-"}
    module_idx = 0

    def __init__(self, log_file=None, messages=None):
        if log_file != None:
            if os.path.exists(log_file):
                self.log_file=log_file
                self.parse_message = contiki_ng_default_parser
                self.parse_file(log_file)
            else:
                raise IOError("Log file does not exists !")
        elif messages != None:
            self.from_messages(messages)

    def parse_file(self, file):
        messages = []
        with open(file, 'r') as f:
            for line in f:
                    i_start = 0
                    i_end = line.find(":")
                    i_end2 = line.find(":", i_end+1)
                    if i_end == -1 or i_end2 == -1:
                        continue
                    time = int(line[:i_end])
                    i_start = i_end+1
                    node_id=int(line[i_start:i_end2])
                    i_start = i_end2+1

                    message = self.parse_message(time, node_id, line[i_start:])
                    if message != None:
                        messages.append(message)
        self.from_messages(messages)
    
    def from_messages(self, messages):
        max_modulename_length = 0
        nid_to_messages = {}
        for message in messages:
            nid_to_messages.setdefault(message[Log.NODE_ID], []).append(message)
            module_name = Log.revert_modules[message[Log.LOG_MODULE]]
            if len(module_name) > max_modulename_length:
                max_modulename_length = len(module_name)
        self.max_modulename_length=max_modulename_length
        self.messages = messages
        self.dico = nid_to_messages
        self.node_ids = list(nid_to_messages.keys())


    def get_messages(self, contain=None, log_level=None, log_module=None, node_id=None, time=None):
        result = self.messages
        if type(node_id) == int:
            result = self.dico.get(node_id, result)
        elif type(node_id) == list:
            result = filter(lambda message: message[Log.NODE_ID] in node_id, result) 
        if log_level != None:
            result = filter(lambda message: message[Log.LOG_LEVEL] != None and message[Log.LOG_LEVEL] <= log_level, result) 
        if log_module != None:
            result = filter(lambda message: message[Log.LOG_MODULE] == Log.get_module_id(log_module), result) 
        if contain != None:
            if type(contain) == str:
                f = lambda text: contain in text
            else:
                f = contain
            result = filter(lambda message: f(message[Log.MESSAGE]), result) 
        if time != None:
            conditions = time.replace(",", " ").replace("<", " <").replace(">", " >").split()
            import sys
            for condition in conditions:
                if condition == "":
                    continue
                if condition.startswith(">="):
                    result = list(filter(lambda message: message[Log.TIME] >= int(float(condition[2:])*1000000), result))
                elif condition.startswith(">"):
                    result = list(filter(lambda message: message[Log.TIME] > int(float(condition[1:])*1000000), result))
                elif condition.startswith("<="):
                    result = list(filter(lambda message: message[Log.TIME] <= int(float(condition[2:])*1000000), result))
                elif condition.startswith("<"):
                    result = list(filter(lambda message: message[Log.TIME] < int(float(condition[1:])*1000000), result))
        return list(result)

    def get_node_ids(self):
        ids = list(self.dico.keys())
        ids.sort()
        return ids

    @staticmethod
    def get_module_id(module_name):
        module_id = Log.modules.get(module_name, None)
        if module_id == None:
            module_id = Log.module_idx
            Log.modules[module_name] = module_id
            Log.revert_modules[module_id] = module_name
            Log.module_idx += 1
        return module_id
    
    @staticmethod
    def print_message(message):
        levels = {1:'ERR', 2:'WARN', 3:'INFO', 4:'DBG', None:''}
        print(f"\033[38;5;166m{message[Log.TIME]/1000000:8.3f}s\033[0m|\033[38;5;34mID:{message[Log.NODE_ID]:2d}\033[0m|\033[38;5;3m{levels[message[Log.LOG_LEVEL]]}:{Log.revert_modules[message[Log.LOG_MODULE]]}\033[0m| {message[Log.MESSAGE]}")
