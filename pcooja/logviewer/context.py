import glob
import copy

from . import Log
from .states import State
from .states.viewinglog import set_cursor, move_view

def init_context(stdscr):
    global scripts, views
    context = {}
    context["stdscr"] = stdscr

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
    context["viewing_log__presets"] = []
    context["viewing_log__preset"] = None
    # ENTERING_COMMAND
    context["entering_command__prompt"] = ""
    context["entering_command__history"] = []
    # SCRIPT COMMAND
    context["script_command__functions"] = []
    context["script_command__select_pos"] = 0
    context["viewing_script__offset"] = 0
    context["viewing_script__pos"] = 0
    context["viewing_script__lines"] = []
    context["viewing_script__horizontal_offset"] = 0

    return context

def add_view(parent, name):
    if len(parent["views"]) == 0:
        context = init_context(parent["stdscr"])
        context["parent"] = parent
    else:
        i = parent["active_view"]
        while parent["views"][i]["viewing_log__preset"] != None:
            i -= 1

        context = copy.copy(parent["views"][i])
    context["view_name"] = name
    parent["views"].append(context)
    return context

def change_view(parent, increment):

    current_view = parent["views"][parent["active_view"]]

    parent["active_view"] = (parent["active_view"]+increment)%len(parent["views"])
    new_view = parent["views"][parent["active_view"]]

    match_pos = None
    # We try to match the selected message in the new view
    current_message = parent["last_selected_message"]
    # We only try to match a formatted message (not a simple string)
    if current_message[Log.NODE_ID] != None:
        messages = new_view["viewing_log__messages"]
        # If it is a script-generated view, we cannot try to find the
        # message using dichotomy search since no guarantee is given
        # about order of packets
        if new_view["viewing_log__preset"] != None:
            for i, message in enumerate(messages):
                if message == current_message:
                    match_pos = i 
                    break
        else: # non script-genrated view => guarantee on order => dichotomy
            start = 0
            end = len(messages)-1
            while start < end:
                middle = start+(end-start)//2
                if middle == start or middle == end:
                    break
                if messages[middle][Log.TIME] < current_message[Log.TIME]:
                    start = middle
                else:
                    end = middle
            middle+=1

            while middle < len(messages)-1 and messages[middle] != current_message \
                                           and messages[middle][Log.TIME] == current_message[Log.TIME]:
                middle += 1
            if messages[middle] == current_message:
                match_pos = middle

    if match_pos != None:
        set_cursor(new_view, match_pos)
        if new_view["viewing_log__pos"] == new_view["viewing_log__offset"]:
            move_view(new_view, -new_view["viewer_height"]//2)
        elif new_view["viewing_log__pos"] == new_view["viewing_log__offset"]+new_view["viewer_height"]-1:
            move_view(new_view, new_view["viewer_height"]//2)
    else:
        new_view["viewing_log__pos"] = None

def get_log_filepaths():
    global path
    paths = glob.glob("./*.log")
    return paths
