import curses
import io
import traceback

from . import Shortcut
from . import Log
from .states import State
from .states.viewinglog import update_log, set_cursor, move_view
from .context import add_view, change_view

def check_command(context):
    if context["current_state"] == State.SELECTING_LOG:
        return
    if context["entering_command"]:
        match context["command_type"], context["pressed"]:
            case Shortcut.SCRIPT_COMMAND, curses.KEY_DOWN:
                context["script_command__select_pos"] = (context["script_command__select_pos"] + 1)
                context["script_command__select_pos"] = min(len(context["script_command__functions"])-1, 
                                                            max(0, context["script_command__select_pos"]))
            case Shortcut.SCRIPT_COMMAND, curses.KEY_UP:
                context["script_command__select_pos"] = (context["script_command__select_pos"] - 1)
                context["script_command__select_pos"] = min(len(context["script_command__functions"])-1, 
                                                            max(0, context["script_command__select_pos"]))
            case _, 10: # ENTER key
                process_command(context)
                context["command"] = ""
                context["entering_command"] = False
                context["command_type"] = None
            case _, curses.KEY_BACKSPACE: # BACKSPACE key
                context["command"] = context["command"][:-1]
            case _, (curses.KEY_LEFT|curses.KEY_RIGHT):
                """"""
            case _, _:
                context["command"] += chr(context["pressed"])
    else:
        context["entering_command"] = True
        context["command_type"] = context["pressed"]
        match context["pressed"]:
            case Shortcut.FILTER_NODE_COMMAND:
                """"""
            case Shortcut.FILTER_CONTAIN_COMMAND:
                """"""
            case Shortcut.FILTER_TIME_COMMAND:
                """"""
            case Shortcut.FILTER_MODULE_COMMAND:
                """"""
            case Shortcut.FILTER_LEVEL_COMMAND:
                """"""
            case Shortcut.RESET_FILTERS:
                context["command_filter_nodes"] = None
                context["command_filter_time"] = None
                context["command_filter_contain"] = None
                context["command_filter_module"] = None
                context["command_filter_level"] = None
                context["command_search_pos"] = None
                context["command_search_text"] = None
                context["viewing_log__reload_log"] = True
                update_log(context)
                context["entering_command"] = False
                context["command_type"] = None
            case Shortcut.SCRIPT_COMMAND:
                """"""
            case Shortcut.SEARCH_COMMAND:
                """"""
            case Shortcut.NEW_VIEW_COMMAND:
                """"""
            case Shortcut.NEXT_VIEW|Shortcut.PREVIOUS_VIEW:
                process_command(context)
                context["entering_command"] = False
                context["command_type"] = None
            case curses.KEY_MOUSE:
                _, _, my, _, state = curses.getmouse()
                if state & curses.BUTTON1_PRESSED != 0: 
                    line = context["viewing_log__offset"] + my - 1
                    set_cursor(context, line)
                    context["entering_command"] = False
                    context["command_type"] = None
            case _:
                context["entering_command"] = False
                context["command_type"] = None

def process_command(context):
    command = context["command"].strip()
    match context["command_type"]:
        case Shortcut.FILTER_NODE_COMMAND:
            if command in ["*", ""]:
                nodes = None
            else:
                command = command.replace(","," ")
                command_node_ids = command.split()
                nodes = []
                for command_node_id in command_node_ids:
                    if "-" in command_node_id:
                        start, end = command_node_id.split("-")
                        nodes.extend(range(int(start), int(end)+1))
                    else:
                        nodes.append(int(command_node_id))
            context["command_filter_nodes"] = nodes
            context["viewing_log__reload_log"] = True

        case Shortcut.FILTER_CONTAIN_COMMAND:
            text = command
            if text in ["", "*"]:
                text = None
            context["command_filter_contain"] = text
            context["viewing_log__reload_log"] = True
        case Shortcut.FILTER_TIME_COMMAND:
            time = int(command)*1000000
            pos = None
            if command.isdigit():
                if context["viewing_log__preset"] != None:
                    for i, message in enumerate(context["viewing_log__messages"]):
                        if message[Log.TIME] != None and message[Log.TIME] >= time:
                            pos = i 
                            break
                else:
                    start = 0
                    messages = context["viewing_log__messages"]
                    end = len(messages)-1
                    while start < end:
                        middle = start+(end-start)//2
                        if middle == start or middle == end:
                            break
                        if messages[middle][Log.TIME] < time:
                            start = middle
                        else:
                            end = middle
                    pos = int(middle)

                set_cursor(context, pos)
                return
            if command=='':
                command = None
            context["command_filter_time"] = command
            context["viewing_log__reload_log"] = True
        case Shortcut.FILTER_LEVEL_COMMAND:
            level = None
            command = command.upper()
            match command:
                case ("DBG"|"DEBUG"):
                    level = Log.LEVEL_DBG
                case "INFO":
                    level = Log.LEVEL_INFO
                case ("WARN"|"WARNING"):
                    level = Log.LEVEL_WARN
                case ("ERR"|"ERROR"):
                    level = Log.LEVEL_ERR
                case _:
                    level = None
            context["command_filter_level"] = level
            context["viewing_log__reload_log"] = True
        case Shortcut.FILTER_MODULE_COMMAND:
            if command=='':
                command = None
            context["command_filter_module"] = command
            context["viewing_log__reload_log"] = True
        case Shortcut.SCRIPT_COMMAND:
            if len(context["script_command__functions"]) > 0:
                f = context["script_command__functions"][context["script_command__select_pos"]]
                
                buffer = io.StringIO()
                def script_print(*args,**kwargs):
                    kwargs["file"] = buffer
                    print(*args, **kwargs)

                f.__globals__['print'] = script_print
                try:
                    f(Log(messages=context["viewing_log__messages"]))
                    context["viewing_script__lines"] = buffer.getvalue().split("\n")
                except Exception:
                    tb = traceback.format_exc()
                    context["viewing_script__lines"] = tb.split("\n")
                del(f.__globals__['print'])
                context["current_state"] = State.VIEWING_SCRIPT
                context["pressed"] = 0
        case Shortcut.SEARCH_COMMAND:
            text = command
            if text in ["", "*"]:
                text = None
            pos = None
            for i, message in enumerate(context["viewing_log__messages"]):
                if text in message[Log.MESSAGE]:
                    pos = i+1
                    break
            if pos != None:
                set_cursor(context, pos)
                move_view(context, context["viewer_height"]//2)
            context["command_search_pos"] = pos
        case Shortcut.NEW_VIEW_COMMAND:
            if command =="":
                return
            view_name = command
            context = add_view(context["parent"], view_name)
            context["parent"]["active_view"] = len(context["parent"]["views"])-1
            context["entering_command"] = False
            context["command_type"] = None
            context["command"] = ""
            context["viewing_log__reload_log"] = False
            return
        case Shortcut.NEXT_VIEW:
            change_view(context["parent"], 1)
        case Shortcut.PREVIOUS_VIEW:
            change_view(context["parent"], -1)
        case _:
            """"""
    if context["current_state"] == State.VIEWING_LOG:
        update_log(context)


