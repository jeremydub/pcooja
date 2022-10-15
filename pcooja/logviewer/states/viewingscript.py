import curses

from . import State
from .viewinglog import state_viewing_log
from .. import Log

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
    x_offset = 1
    for i in range(context["viewing_script__offset"], 
                   min(context["viewing_script__offset"]+context["viewer_height"],len(lines))):
        line = lines[i][Log.MESSAGE][h_offset:width+h_offset-1]
        context["stdscr"].addstr(x_offset+i-context["viewing_script__offset"], 0, line, curses.color_pair(4))

