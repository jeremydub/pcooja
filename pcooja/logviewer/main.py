import curses

from . import Log
from .command import check_command
from .bars import draw_status_bar, draw_view_bar
from .states import State
from .states.viewinglog import state_viewing_log
from .states.viewingscript import state_viewing_script
from .states.selectinglog import state_selecting_log
from .context import add_view 

path = None
parent = None

views = []
scripts = []

def handler(stdscr):
    global parent, views, scripts
    parent = {"active_view":0, "views":[], "stdscr":stdscr, "last_selected_message":None}

    cursor_x = 0
    cursor_y = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, 246, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)

    curses.curs_set(0)
    """
    curses.mousemask(1)
    curses.mouseinterval(50)
    """
    add_view(parent, "Main")

    context = parent["views"][parent["active_view"]]
    context["viewing_log__presets"] = views
    context["script_command__functions"] = scripts


    # Loop where k is the last character pressed
    while (context["pressed"] != ord('q') or context["entering_command"]):
        # Initialization
        stdscr.clear()
        
        check_command(context)
        context = parent["views"][parent["active_view"]]
        draw_context(context)

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        context["pressed"] = stdscr.getch()

def draw_context(context):
    context["height"], context["width"] = context["stdscr"].getmaxyx()
    context["viewer_height"] = context["height"] - 2
    context["viewer_width"] = context["width"]

    match context["current_state"]:
        case State.SELECTING_LOG:
            state_selecting_log(context)
        case State.VIEWING_LOG:
            state_viewing_log(context)
        case State.VIEWING_SCRIPT:
            state_viewing_script(context)

    draw_status_bar(context)
    draw_view_bar(context)

def main(_path, _scripts, _views):
    global path, scripts, views
    path = _path
    scripts = _scripts
    views = _views
    curses.wrapper(handler)
