import sys,os
import curses
import glob
import io
import traceback

from ..log import Log

from enum import Enum

path = None
scripts = []

class State(Enum):
    SELECTING_LOG = 1
    VIEWING_LOG = 2
    VIEWING_SCRIPT = 3

class Shortcut():
    FILTER_NODE_COMMAND = ord("n")
    FILTER_CONTAIN_COMMAND = ord("c")
    FILTER_TIME_COMMAND = ord("t")
    FILTER_MODULE_COMMAND = ord("m")
    FILTER_LEVEL_COMMAND = ord("l")
    RESET_FILTERS = ord("r")
    SCRIPT_COMMAND = ord("s")
    SEARCH_COMMAND = ord("/")

def init_context():
    global scripts
    context = {}

    context["current_state"] = State.SELECTING_LOG
    context["log_filepaths"] = get_log_filepaths()
    context["pressed"] = 0
    context["entering_command"] = False
    context["command"] = ""
    context["command_filter_nodes"] = None
    context["command_filter_contain"] = None
    context["command_filter_time"] = None
    context["command_filter_module"] = None
    context["command_filter_level"] = None
    context["command_search_text"] = None
    context["command_search_pos"] = None

    # SELECTING_LOG
    context["selecting_log__list_pos"] = 0
    context["selecting_log__selected_log"] = None
    # VIEWING_LOG
    context["viewing_log__offset"] = 0
    context["viewing_log__pos"] = 0
    context["viewing_log__messages"] = []
    context["viewing_log__reload_log"] = True
    context["viewing_log__logger"] = None
    context["viewing_log__horizontal_offset"] = 0
    # ENTERING_COMMAND
    context["entering_command__prompt"] = ""
    context["entering_command__history"] = []
    # SCRIPT COMMAND
    context["script_command__functions"] = scripts
    context["script_command__select_pos"] = 0
    context["viewing_script__offset"] = 0
    context["viewing_script__pos"] = 0
    context["viewing_script__lines"] = []
    context["viewing_script__horizontal_offset"] = 0

    return context

def state_selecting_log(context):
    match context["pressed"]:
        case curses.KEY_DOWN:
            context["selecting_log__list_pos"] = (context["selecting_log__list_pos"] + 1) % len(context["log_filepaths"])
        case curses.KEY_UP:
            context["selecting_log__list_pos"] = (context["selecting_log__list_pos"] - 1) % len(context["log_filepaths"])
        case 10: # ENTER key
            context["selecting_log__selected_log"] = context["selecting_log__list_pos"]
            context["current_state"] = State.VIEWING_LOG
            return state_viewing_log(context)
    for i,log_filepath in enumerate(context['log_filepaths']):
        if i == context["selecting_log__list_pos"]:
            color = curses.color_pair(3)
        else:
            color = curses.color_pair(4)
        context["stdscr"].addstr(i, 0, log_filepath, color)

def check_command(context):
    if context["entering_command"]:
        match context["pressed"]:
            case curses.KEY_DOWN:
                if context["command_type"] == Shortcut.SCRIPT_COMMAND:
                    context["script_command__select_pos"] = (context["script_command__select_pos"] + 1)
                    context["script_command__select_pos"] = min(len(context["script_command__functions"])-1, 
                                                                max(0, context["script_command__select_pos"]))
            case curses.KEY_UP:
                if context["command_type"] == Shortcut.SCRIPT_COMMAND:
                    context["script_command__select_pos"] = (context["script_command__select_pos"] - 1)
                    context["script_command__select_pos"] = min(len(context["script_command__functions"])-1, 
                                                                max(0, context["script_command__select_pos"]))
            case 10: # ENTER key
                process_command(context)
                context["command"] = ""
                context["entering_command"] = False
                context["command_type"] = None
            case curses.KEY_BACKSPACE: # BACKSPACE key
                context["command"] = context["command"][:-1]
            case (curses.KEY_LEFT|curses.KEY_RIGHT):
                """"""
            case _:
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
                    pos = i
                    break
            if pos != None:
                context["viewing_log__offset"] = pos
                context["viewing_log__pos"] = pos
                context["viewing_log__offset"] = min(max(0,context["viewing_log__offset"]), 
                                                     len(context["viewing_log__messages"]))
                context["viewing_log__pos"] = min(max(0,context["viewing_log__pos"]), 
                                              len(context["viewing_log__messages"]))
            context["command_search_pos"] = pos

        case _:
            """"""
    update_log(context)

def update_log(context):
    if context["viewing_log__logger"] == None:
        filepath = context["log_filepaths"][context["selecting_log__selected_log"]]
        log = Log(filepath)
        context["viewing_log__logger"] = log 
        colors = [2,3,4,5,6]+list(range(9,16))+[80,35,40,125,200,227,196,100,203]
        for node_id in log.node_ids:
            #curses.init_pair(4+node_id, colors[node_id%len(colors)], -1)
            curses.init_pair(4+node_id, 16, colors[node_id%len(colors)], )
    if context["viewing_log__reload_log"]:
        log = context["viewing_log__logger"]
        context["viewing_log__messages"] = log.get_messages(node_id=context["command_filter_nodes"],
                                                            contain=context["command_filter_contain"],
                                                            time=context["command_filter_time"],
                                                            log_module=context["command_filter_module"],
                                                            log_level=context["command_filter_level"])
        context["viewing_log__reload_log"] = False
        context["viewing_log__offset"] = 0 
        context["viewing_log__pos"] = 0 

def state_viewing_log(context):

    update_log(context)

    if not context["entering_command"]:
        match context["pressed"]:
            case 5: # scroll down
                context["viewing_log__offset"] = (context["viewing_log__offset"] + 4)
                context["viewing_log__pos"] = (context["viewing_log__pos"] + 4)
            case 25: # scroll up
                context["viewing_log__offset"] = (context["viewing_log__offset"] - 4)
                context["viewing_log__pos"] = (context["viewing_log__pos"] - 4)
            case curses.KEY_DOWN|5:
                context["viewing_log__offset"] = (context["viewing_log__offset"] + 1)
                context["viewing_log__pos"] = (context["viewing_log__pos"] + 1)
            case curses.KEY_UP|25:
                context["viewing_log__offset"] = (context["viewing_log__offset"] - 1)
                context["viewing_log__pos"] = (context["viewing_log__pos"] - 1)
            case (curses.KEY_NPAGE|32): # Next page or Space key
                context["viewing_log__offset"] = (context["viewing_log__offset"] + context["viewer_height"] -1)
                context["viewing_log__pos"] = (context["viewing_log__pos"] + context["viewer_height"] -1)
            case (curses.KEY_PPAGE|curses.KEY_BACKSPACE):
                context["viewing_log__offset"] = (context["viewing_log__offset"] - context["viewer_height"] +1)
                context["viewing_log__pos"] = (context["viewing_log__pos"] - context["height"] +1)
            case 126: # END key
                context["viewing_log__offset"] = len(context["viewing_log__messages"])-context["viewer_height"]
                context["viewing_log__pos"] = len(context["viewing_log__messages"])-context["viewer_height"]
            case curses.KEY_LEFT:
                context["viewing_log__horizontal_offset"] = (context["viewing_log__horizontal_offset"] - 10)
            case curses.KEY_RIGHT:
                context["viewing_log__horizontal_offset"] = (context["viewing_log__horizontal_offset"] + 10)
            case _:
                """"""
        context["viewing_log__offset"] = min(max(0,context["viewing_log__offset"]), 
                                             len(context["viewing_log__messages"]))
        context["viewing_log__horizontal_offset"] = max(0,context["viewing_log__horizontal_offset"]) 
        context["viewing_log__pos"] = min(max(0,context["viewing_log__pos"]), 
                                          len(context["viewing_log__messages"]))

    width = context["width"]
    messages = context["viewing_log__messages"]
    h_offset = context["viewing_log__horizontal_offset"]
    for i in range(context["viewing_log__offset"], 
                   min(context["viewing_log__offset"]+context["viewer_height"],len(messages))):
        y = 0
        timestamp = messages[i][Log.TIME]/1000000
        time_line = f"{timestamp:.3f}s "
        color = curses.color_pair(4)
        if i == context["command_search_pos"]:
            color = curses.color_pair(2)
        context["stdscr"].addstr(i-context["viewing_log__offset"], 0, time_line, color)
        y += len(time_line)

        node_id = messages[i][Log.NODE_ID]
        color = curses.color_pair(4+node_id)
        node = f"{'#'+str(node_id)+'|':>4}"
        context["stdscr"].addstr(i-context["viewing_log__offset"], y, node, color)
        y += len(node)
        module = f"{Log.revert_modules[messages[i][Log.LOG_MODULE]]:^{context['viewing_log__logger'].max_modulename_length}}| "
        context["stdscr"].addstr(i-context["viewing_log__offset"], y, module, color)
        y += len(module)
        message = messages[i][Log.MESSAGE][h_offset:width+h_offset-1-y]
        context["stdscr"].addstr(i-context["viewing_log__offset"], y, f"{message:<{width-y-1}}", color)

def state_viewing_script(context):

    match context["pressed"]:
        case curses.KEY_DOWN:
            if not context["entering_command"]:
                context["viewing_script__offset"] = (context["viewing_script__offset"] + 1)
                context["viewing_script__pos"] = (context["viewing_script__pos"] + 1)
        case curses.KEY_UP:
            if not context["entering_command"]:
                context["viewing_script__offset"] = (context["viewing_script__offset"] - 1)
                context["viewing_script__pos"] = (context["viewing_script__pos"] - 1)
        case (curses.KEY_NPAGE|32): # Next page or Space key
            context["viewing_script__offset"] = (context["viewing_script__offset"] + context["viewer_height"] -1)
            context["viewing_script__pos"] = (context["viewing_script__pos"] + context["viewer_height"] -1)
        case (curses.KEY_PPAGE|curses.KEY_BACKSPACE):
            context["viewing_script__offset"] = (context["viewing_script__offset"] - context["viewer_height"] +1)
            context["viewing_script__pos"] = (context["viewing_script__pos"] - context["height"] +1)
        case curses.KEY_LEFT:
            context["viewing_script__horizontal_offset"] = (context["viewing_script__horizontal_offset"] - 10)
        case curses.KEY_RIGHT:
            context["viewing_script__horizontal_offset"] = (context["viewing_script__horizontal_offset"] + 10)
        case 10: # ENTER key
            context["viewing_script__lines"] = []
            context["viewing_script__offset"] = 0 
            context["viewing_script__pos"] = 0 
            context["current_state"] = State.VIEWING_LOG
            state_viewing_log(context)
            return
        case _:
            """"""
    context["viewing_script__offset"] = min(max(0,context["viewing_script__offset"]), 
                                         len(context["viewing_script__lines"]))
    context["viewing_script__horizontal_offset"] = max(0,context["viewing_script__horizontal_offset"]) 
    context["viewing_script__pos"] = min(max(0,context["viewing_script__pos"]), 
                                      len(context["viewing_script__lines"]))

    width = context["width"]
    lines = context["viewing_script__lines"]
    h_offset = context["viewing_script__horizontal_offset"]
    for i in range(context["viewing_script__offset"], 
                   min(context["viewing_script__offset"]+context["viewer_height"],len(lines))):
        line = lines[i][h_offset:width+h_offset-1]
        context["stdscr"].addstr(i-context["viewing_script__offset"], 0, line, curses.color_pair(4))

def draw_status_bar(context):
    width = context["width"]
    if context["entering_command"]:
        if context["command_type"] == Shortcut.SCRIPT_COMMAND:
            y = context["viewer_height"] - len(context["script_command__functions"]) - 1
            prompt = "Select a script to run :"
            context["stdscr"].addstr(y, 0, f"{prompt:<{width-1}}", curses.color_pair(3))
            for i, function in enumerate(context["script_command__functions"]):
                if i == context["script_command__select_pos"]:
                    color = curses.color_pair(4)
                    name = f"* {function.__name__}"
                else:
                    color = curses.color_pair(4)
                    name = f"  {function.__name__}"
                context["stdscr"].addstr(y+i+1, 0, f"{name:<{width-1}}", curses.color_pair(1))
                description = ""
                if function.__doc__ != None:
                    description = f" --- {function.__doc__.strip()}"
                context["stdscr"].addstr(y+i+1, len(name), f"{description:<{width-len(name)-1}}", color)

        else:
            prompt = ""
            match context["command_type"]:
                case Shortcut.FILTER_NODE_COMMAND:
                    prompt = "FILTER NODES"
                case Shortcut.FILTER_CONTAIN_COMMAND:
                    prompt = "CONTAINS"
                case Shortcut.FILTER_TIME_COMMAND:
                    prompt = "FILTER TIME"
                case Shortcut.FILTER_MODULE_COMMAND:
                    prompt = "FILTER LOG MODULE"
                case Shortcut.FILTER_LEVEL_COMMAND:
                    prompt = "FILTER LOG LEVEL"
                case Shortcut.SEARCH_COMMAND:
                    prompt = "SEARCH"
                case _:
                    prompt = ""
            if prompt != "":
                prompt = f"[{prompt}]"
            line = f"{prompt} {context['command']}"
            context["stdscr"].addstr(context["viewer_height"], 0, prompt, curses.color_pair(3))
            context["stdscr"].addstr(context["viewer_height"], len(prompt)+1, f"{context['command']:<{context['width']-len(prompt)-2}}", 4)
    else:
        line = "Filters:"
        filters = []
        if context["command_filter_nodes"] != None:
            nodes = context['command_filter_nodes']
            filters.append(f" Nodes={nodes}")
        if context["command_filter_contain"] != None:
            filters.append(f" Contains '{context['command_filter_contain']}'")
        if context["command_filter_time"] != None:
            filters.append(f" Time='{context['command_filter_time']}'")
        if context["command_filter_module"] != None:
            filters.append(f" Module='{context['command_filter_module']}'")
        if context["command_filter_level"] != None:
            levels = {1:'ERR', 2:'WARN', 3:'INFO', 4:'DBG', None:''}
            filters.append(f" Level='{levels[context['command_filter_level']]}'")
        line += " | ".join(filters)
        context["stdscr"].addstr(context["viewer_height"], 0, f"{line:<{width-1}}", curses.color_pair(3))
        if len(context["viewing_log__messages"]) > 0:
            line = f"{context['viewing_log__offset']}/{len(context['viewing_log__messages'])} {(context['viewing_log__offset']/len(context['viewing_log__messages'])*100):.0f}%"
            context["stdscr"].addstr(context["viewer_height"], width-len(line)-1, line, curses.color_pair(3))

def draw_menu(stdscr):
    context = init_context()
    context["stdscr"] = stdscr
    cursor_x = 0
    cursor_y = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)

    curses.curs_set(0)

    # Loop where k is the last character pressed
    while (context["pressed"] != ord('q') or context["entering_command"]):
        # Initialization
        stdscr.clear()
        context["height"], context["width"] = stdscr.getmaxyx()
        context["viewer_height"] = context["height"] - 1
        context["viewer_width"] = context["width"]

        check_command(context)

        match context["current_state"]:
            case State.SELECTING_LOG:
                state_selecting_log(context)
            case State.VIEWING_LOG:
                state_viewing_log(context)
            case State.VIEWING_SCRIPT:
                state_viewing_script(context)

        draw_status_bar(context)

        """
        if k == curses.KEY_DOWN:
            cursor_y = cursor_y + 1
        elif k == curses.KEY_UP:
            cursor_y = cursor_y - 1
        elif k == curses.KEY_RIGHT:
            cursor_x = cursor_x + 1
        elif k == curses.KEY_LEFT:
            cursor_x = cursor_x - 1

        cursor_x = max(0, cursor_x)
        cursor_x = min(width-1, cursor_x)

        cursor_y = max(0, cursor_y)
        cursor_y = min(height-1, cursor_y)

        # Declaration of strings
        title = "Curses example"[:width-1]
        subtitle = "Written by Clay McLeod"[:width-1]
        keystr = "Last key pressed: {}".format(k)[:width-1]
        statusbarstr = "Press 'q' to exit | STATUS BAR | Pos: {}, {}".format(cursor_x, cursor_y)
        if k == 0:
            keystr = "No key press detected..."[:width-1]

        # Centering calculations
        start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
        start_x_subtitle = int((width // 2) - (len(subtitle) // 2) - len(subtitle) % 2)
        start_x_keystr = int((width // 2) - (len(keystr) // 2) - len(keystr) % 2)
        start_y = int((height // 2) - 2)

        # Rendering some text
        whstr = "Width: {}, Height: {}".format(width, height)
        stdscr.addstr(0, 0, whstr, curses.color_pair(1))

        # Render status bar
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-1, 0, statusbarstr)
        stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))

        # Turning on attributes for title
        stdscr.attron(curses.color_pair(2))
        stdscr.attron(curses.A_BOLD)

        # Rendering title
        stdscr.addstr(start_y, start_x_title, title)

        # Turning off attributes for title
        stdscr.attroff(curses.color_pair(2))
        stdscr.attroff(curses.A_BOLD)

        # Print rest of text
        stdscr.addstr(start_y + 1, start_x_subtitle, subtitle)
        stdscr.addstr(start_y + 3, (width // 2) - 2, '-' * 4)
        stdscr.addstr(start_y + 5, start_x_keystr, keystr)
        stdscr.move(cursor_y, cursor_x)
        """

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        context["pressed"] = stdscr.getch()

def main(_path, _scripts):
    global path, scripts
    path = _path
    scripts = _scripts
    curses.wrapper(draw_menu)

def get_log_filepaths():
    global path
    paths = glob.glob("./*.log")
    return paths
