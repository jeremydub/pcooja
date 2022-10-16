"""Cooja Log Viewer
Usage:
  logviewer.py [-s SCRIPT_FILE]... [LOG_FILE]
  logviewer.py -h | --help
Options:
  -h --help       Show help message.
  -s SCRIPT_FILE  add scripts from given Python module to viewer.
"""

from .main import main
from docopt import docopt
import os
import sys
import importlib.util
import inspect
import json

args = docopt(__doc__, version="compress 0.1")

def get_local_config():
    path = ".pcooja.logviewer.conf"
    config = None
    if os.path.exists(path):
        with open(path, "r") as f:
            config = json.load(f)
    return config

def importCode(code, name):
    """ code can be any object containing code -- string, file object, or
       compiled code object. Returns a new module object initialized
       by dynamically importing the given code and optionally adds it
       to sys.modules under the given name.
    """
    import imp
    module = imp.new_module(name)

    exec(code) in module.__dict__

    return module

if __name__ == "__main__":
    script_files = args["-s"]
    functions = []
    views = []

    local_config = get_local_config()
    if local_config != None:
        if "scripts" in local_config:
            script_files.extend(local_config["scripts"])

    for i, script_file in enumerate(script_files):
        if not os.path.exists(script_file):
            print(f"Script file '{script_file}' does not exist",file=sys.stderr)
            exit()
        spec = importlib.util.spec_from_file_location(f"logviewerscript{i}", script_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"logviewerscript{i}"] = module
        spec.loader.exec_module(module)
        for name in module.__dict__:
            elem = module.__dict__[name]
            if inspect.isfunction(elem) and elem.__name__.startswith("view") and inspect.getfullargspec(elem).args == ["log"]:
                views.append(elem)
            elif inspect.isfunction(elem) and inspect.getfullargspec(elem).args == ["log"]:
                functions.append(elem)

    path = args["LOG_FILE"]
    if path == None:
        path = "."
    if not os.path.exists(path):
        print(f"'{path}' does not exist",file=sys.stderr)
        exit()

    main(path, functions, views)
