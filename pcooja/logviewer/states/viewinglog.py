import curses
import math

from .. import Shortcut
from . import State
from .. import Log
        
_colors = [2,3,4,5,6]+list(range(9,16))+[80,35,39,126,95,227,195,250,203]

def state_viewing_log(context):

    update_log(context)

    if not context["entering_command"]:
        match context["pressed"]:
            case 5: # scroll down
                move_view(context, 4)
            case 25: # scroll up
                move_view(context, -4)
            case curses.KEY_DOWN:
                move_cursor(context, 1)
            case curses.KEY_UP:
                move_cursor(context, -1)
            case (curses.KEY_NPAGE|32): # Next page or Space key
                move_view(context, context["viewer_height"] -1)
            case (curses.KEY_PPAGE|curses.KEY_BACKSPACE):
                move_view(context, -(context["viewer_height"]-1))
            case 126: # END key
                set_cursor(context, -1)
            case curses.KEY_LEFT:
                move_view(context, x_increment=-10)
            case curses.KEY_RIGHT:
                move_view(context, x_increment=10)
            case _:
                """"""
    draw_viewinglog(context)

def set_cursor(context, y):
    old_y_offset = context["viewing_log__offset"]
    
    if y == -1:
        y = len(context["viewing_log__messages"])-1

    y = min(max(0,y), len(context["viewing_log__messages"])-1)
    
    if context["viewing_log__messages"][y][Log.NODE_ID] == None and context["viewing_log__pos"] != None:
        y = move_cursor(context, 1)

    if y == None:
        return
    
    if y >= old_y_offset+context["viewer_height"]:
        y_offset = y-context["viewer_height"]+1
    elif y < old_y_offset:
        y_offset = y
    else:
        y_offset = old_y_offset

    y_offset = min(max(0,y_offset), len(context["viewing_log__messages"])-1)

    context["viewing_log__offset"] = y_offset
    context["viewing_log__pos"] = y 
    context["parent"]["last_selected_message"] = context["viewing_log__messages"][context["viewing_log__pos"]]

def move_cursor(context, y_increment):
    old_y_pos = context["viewing_log__pos"]
    if old_y_pos == None:
        old_y_pos = context["viewing_log__offset"]
    step = (1 if y_increment > 0 else -1)

    messages = context["viewing_log__messages"]

    y_pos = old_y_pos + y_increment
    y_pos = min(max(0,y_pos), len(messages)-1)

    if messages[y_pos][Log.NODE_ID] == None:
        back_tracking = True
        # Try to find the first formatted message after/before the cursor
        while y_pos != 0 and y_pos != len(messages) - 1:
            y_pos += step 
            if messages[y_pos][Log.NODE_ID] != None:
                back_tracking = False
                break
        # If no formatted message found, find the first message between
        # the desired position and the position before move
        if back_tracking:
            y_pos = old_y_pos + y_increment
            y_pos = min(max(0,y_pos), len(messages)-1)
            for y in range(y_pos, old_y_pos-step, -step):
                if messages[y][Log.NODE_ID] != None:
                    y_pos = y
                    move_view(context, step)
                    break
    
    if messages[y_pos][Log.NODE_ID] != None:
        set_cursor(context, y_pos)
        return y_pos
    else:
        move_view(context, y_increment)
        return None

def move_view(context, y_increment=0, x_increment=0):
    y_offset = context["viewing_log__offset"] + y_increment
    y_offset = min(max(0,y_offset), len(context["viewing_log__messages"])-context["viewer_height"])
    context["viewing_log__offset"] = y_offset

    context["viewing_log__horizontal_offset"] += x_increment
    context["viewing_log__horizontal_offset"] = max(0,context["viewing_log__horizontal_offset"]) 
    
    y_pos = context["viewing_log__pos"]

    if y_pos != None:
        if y_pos >= y_offset+context["viewer_height"]:
            context["viewing_log__pos"] = y_offset+context["viewer_height"]-1
        elif y_pos < y_offset:
            context["viewing_log__pos"] = y_offset

def draw_viewinglog(context):
    width = context["width"]
    messages = context["viewing_log__messages"]
    h_offset = context["viewing_log__horizontal_offset"]
    y_offset = 1

    # Calculating width of timestamp field
    max_timestamp = 1000000 # at least 1 digit, i.e 1 second
    for i in range(context["viewing_log__offset"], 
                   min(context["viewing_log__offset"]+context["viewer_height"],len(messages))):
        t = messages[i][Log.TIME]
        if t != None and t > max_timestamp: # if formatted message
            max_timestamp = t
    timestamp_width = math.ceil(math.log10(max_timestamp/1000000))+4

    for i in range(context["viewing_log__offset"], 
                   min(context["viewing_log__offset"]+context["viewer_height"],len(messages))):
        if messages[i][Log.TIME] == None: # if unformatted message
            message = messages[i][Log.MESSAGE]
            if message.startswith("^"):
                line = f"{message[1:]:^{width-1}}"
            else: 
                line = message[h_offset:h_offset+width-1]
            context["stdscr"].addstr(y_offset+i-context["viewing_log__offset"], 0, line, curses.color_pair(4))
        else:
            x = 0
            node_id = messages[i][Log.NODE_ID]
            timestamp = messages[i][Log.TIME]/1000000
            time_line = f"{timestamp:.3f}"
            time_line = f"{time_line:>{timestamp_width}}s "
            color = curses.color_pair(1)
            if i == context["command_search_pos"]:
                color = curses.color_pair(2)
            elif i == context["viewing_log__pos"]:
                color = curses.color_pair(get_color_highlight(node_id))
            context["stdscr"].addstr(y_offset+i-context["viewing_log__offset"], 0, time_line, color)
            x += len(time_line)

            if i == context["viewing_log__pos"]:
                color = curses.color_pair(get_color_highlight(node_id))
            else:
                color = curses.color_pair(get_color_normal(node_id))
            node = f"{'#'+str(node_id)+'|':>4}"
            context["stdscr"].addstr(y_offset+i-context["viewing_log__offset"], x, node, color)
            x += len(node)
            module = f"{Log.revert_modules[messages[i][Log.LOG_MODULE]]:^{context['viewing_log__logger'].max_modulename_length}}| "
            context["stdscr"].addstr(y_offset+i-context["viewing_log__offset"], x, module, color)
            x += len(module)
            message = messages[i][Log.MESSAGE][h_offset:width+h_offset-1-x]
            context["stdscr"].addstr(y_offset+i-context["viewing_log__offset"], x, f"{message:<{width-x-1}}", color)


def init_colors(context):
        for node_id in context["viewing_log__logger"].node_ids:
            #curses.init_pair(get_color_normal(node_id), _colors[node_id%len(_colors)], -1)
            #curses.init_pair(get_color_highlight(node_id), -1, _colors[node_id%len(_colors)], )
            curses.init_pair(get_color_normal(node_id), 16, _colors[node_id%len(_colors)], )
            curses.init_pair(get_color_highlight(node_id), _colors[node_id%len(_colors)], curses.COLOR_BLACK, )

def get_color_normal(node_id):
    return 4+(node_id)*2

def get_color_highlight(node_id):
    return 4+(node_id)*2-1

def update_log(context):
    if context["viewing_log__logger"] == None:
        filepath = context["log_filepaths"][context["selecting_log__selected_log"]]
        log = Log(filepath)
        context["viewing_log__logger"] = log 
        init_colors(context)
    if context["viewing_log__reload_log"]:
        log = context["viewing_log__logger"]
        context["viewing_log__messages"] = log.get_messages(node_id=context["command_filter_nodes"],
                                                            contain=context["command_filter_contain"],
                                                            time=context["command_filter_time"],
                                                            log_module=context["command_filter_module"],
                                                            log_level=context["command_filter_level"])
        context["viewing_log__reload_log"] = False
        context["viewing_log__offset"] = 0 
        # TODO : conserve position from before (i.e. match message) 
        context["viewing_log__pos"] = 0 
        if context["parent"]["last_selected_message"] == None:
            context["parent"]["last_selected_message"] = context["viewing_log__messages"][context["viewing_log__pos"]]
        from ..context import change_view
        change_view(context["parent"], 0)

def populate_messages(context, function, messages):
    def script_print(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0:
            if type(args[0]) == list and len(args[0]) > 0 \
                    and type(args[0][0]) == tuple \
                    and len(args[0][0])==5:
                messages.extend(args[0])
            elif type(args[0]) == tuple and len(args[0])==5:
                messages.append(args[0])
            else:
                messages.append(context["viewing_log__logger"].parse_message(None, None, str(args[0])))
        else:
            buffer = io.StringIO()
            kwargs["file"] = buffer
            print(*args, **kwargs)
            messages.append(buffer.getvalue().split("\n"))

    function.__globals__['print'] = script_print
    enable = True
    try:
        enable = function(context["viewing_log__logger"])
    except Exception:
        tb = traceback.format_exc()
        for line in tb.split("\n"):
            messages.append(context["viewing_log__logger"].parse_message(None, None, line))
    del(function.__globals__['print'])
