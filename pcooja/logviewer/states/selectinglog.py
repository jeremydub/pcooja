import curses
import io
import traceback

from . import State
from .viewinglog import state_viewing_log
from ..context import add_view
from .. import Log

def state_selecting_log(context):
    match context["pressed"]:
        case curses.KEY_DOWN:
            context["selecting_log__list_pos"] = (context["selecting_log__list_pos"] + 1) % len(context["log_filepaths"])
        case curses.KEY_UP:
            context["selecting_log__list_pos"] = (context["selecting_log__list_pos"] - 1) % len(context["log_filepaths"])
        case 10: # ENTER key
            context["selecting_log__selected_log"] = context["selecting_log__list_pos"]
            context["current_state"] = State.VIEWING_LOG
            state_viewing_log(context)
            for f in context["viewing_log__presets"]:
                messages = []
                def script_print(*args, **kwargs):
                    if len(args) == 1 and len(kwargs) == 0:
                        if type(args[0]) == list:
                            messages.extend(args[0])
                        elif type(args[0]) == str:
                            messages.append(context["viewing_log__logger"].parse_message(None, None, args[0]))
                        else:
                            messages.append(args[0])
                    else:
                        buffer = io.StringIO()
                        kwargs["file"] = buffer
                        print(*args, **kwargs)

                f.__globals__['print'] = script_print
                enable = True
                try:
                    enable = f(context["viewing_log__logger"])
                except Exception:
                    tb = traceback.format_exc()
                    for line in tb.split("\n"):
                        messages.append(context["viewing_log__logger"].parse_message(None, None, line))
                del(f.__globals__['print'])
                if enable != False:
                    view_name = f.__doc__.strip()[:20]
                    new_context = add_view(context["parent"], view_name)
                    new_context["viewing_log__messages"] = messages
                    new_context["viewing_log__logger"] = Log(messages=messages)
                    new_context["viewing_log__preset"] = f
                    new_context["entering_command"] = False
                    new_context["command_type"] = None
                    new_context["command"] = ""
                    new_context["viewing_log__reload_log"] = False
            return

    x_offset = 1
    for i,log_filepath in enumerate(context['log_filepaths']):
        if i == context["selecting_log__list_pos"]:
            color = curses.color_pair(3)
        else:
            color = curses.color_pair(4)
        context["stdscr"].addstr(x_offset+i, 0, log_filepath, color)

