import curses

from . import Shortcut
from .states import State

def draw_view_bar(context):
    if context["current_state"] == State.SELECTING_LOG:
        return
    width = context["width"]
    active_view = context["parent"]["active_view"]
    x = 1
    text = "  Views :  "
    context["stdscr"].addstr(0, x, text, curses.color_pair(4))
    x += len(text)
    for i, view in enumerate(context["parent"]["views"]):
        label = f"  {view['view_name']}  "
        if i == active_view:
            color = curses.color_pair(3)
        else:
            color = curses.color_pair(4)
        context["stdscr"].addstr(0, x, label, color)
        x+=len(label)

def draw_status_bar(context):
    width = context["width"]
    if context["entering_command"]:
        if context["command_type"] == Shortcut.SCRIPT_COMMAND:
            y = context["viewer_height"] - len(context["script_command__functions"])
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
                case Shortcut.NEW_VIEW_COMMAND:
                    prompt = "NEW VIEW NAME"
                case _:
                    prompt = ""
            if prompt != "":
                prompt = f"[{prompt}]"
            line = f"{prompt} {context['command']}"
            context["stdscr"].addstr(context["viewer_height"], 0, prompt, curses.color_pair(3))
            context["stdscr"].addstr(context["viewer_height"], len(prompt), f" {context['command']:<{context['width']-len(prompt)-2}}", 4)
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
        context["stdscr"].addstr(1+context["viewer_height"], 0, f"{line:<{width-1}}", curses.color_pair(3))
        if len(context["viewing_log__messages"]) > 0:
            if context["viewing_log__pos"] != None:
                line = f"{context['viewing_log__pos']}/{len(context['viewing_log__messages'])} {(context['viewing_log__pos']/len(context['viewing_log__messages'])*100):.0f}%"
            else:
                line = f"???/{len(context['viewing_log__messages'])}"
            context["stdscr"].addstr(1+context["viewer_height"], width-len(line)-1, line, curses.color_pair(3))

