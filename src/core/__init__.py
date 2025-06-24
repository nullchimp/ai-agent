import json
import inspect
import datetime

from typing import Dict, Any
from colorama import Fore, Style, init

init(autoreset=True)

class Debugger:
    def __init__(self, debug: bool = False):
        self._debug = debug

    def set_debug(self, debug: bool):
        self._debug = debug

    def is_debug(self) -> bool:
        return self._debug

debugger = Debugger()

is_debug = debugger.is_debug
set_debug = debugger.set_debug

# Import debug_capture after the debugger is set up to avoid circular imports
def get_debug_capture(session_id: str = "default"):
    try:
        from core.debug_capture import get_debug_capture_instance
        return get_debug_capture_instance(session_id)
    except ImportError:
        return None

def mainloop(func):
    async def _decorator(*args, **kwargs):
        while True:
            await func(*args, **kwargs)
    return _decorator

def graceful_exit(func):
    if inspect.iscoroutinefunction(func):
        async def _async_decorator(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except KeyboardInterrupt:
                print("\nBye!")
                exit(0)
            except Exception as e:
                print(f"Error: {e}")
                return None
        return _async_decorator
    else:
        def _sync_decorator(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                print("\nBye!")
                exit(0)
            except Exception as e:
                print(f"Error: {e}")
                return None
        return _sync_decorator

def chatutil(chat_name):
    def _decorator(func):
        async def _wrapper(*args, **kwargs):
            arguments = (input(f"<{chat_name}> "),) + args
            await func(*arguments, **kwargs)
        return _wrapper
    return _decorator

def pretty_print(name: str, data, color = None):
    from core import prettify

    hr = "#" * 50
    header = f"\n{hr} <{name}> {hr}\n"
    footer = f"\n####{hr * 2}{"#" * len(name)}"
    if color:
        header = colorize_text(header, color)
        footer = colorize_text(footer, color)

    print(header, prettify(data), footer)

def recursive_unescape(value):
    """
    Recursively unescape a string or objects containing strings.
    Handles JSON strings that might be escaped multiple times.
    """
    if isinstance(value, str):
        # Try to detect and parse JSON strings
        try:
            parsed = json.loads(value)
            return recursive_unescape(parsed)
        except json.JSONDecodeError:
            # If it's not valid JSON, just return the original string
            pass
        return value
    elif isinstance(value, dict):
        # Process each key-value pair in dictionaries
        return {k: recursive_unescape(v) for k, v in value.items()}
    elif isinstance(value, list):
        # Process each item in lists
        return [recursive_unescape(item) for item in value]
    elif isinstance(value, datetime.datetime):
        # Convert datetime objects to ISO format strings
        return value.isoformat()
    else:
        # Return other types unchanged
        return value

def complex_handler(obj):
    """Handle complex objects for JSON serialization"""
    if hasattr(obj, '__dict__'):
        return recursive_unescape(obj.__dict__)
    else:
        raise TypeError(f'Object of type {type(obj)} is not JSON serializable')
    
def colorize_text(text: str, color: str) -> str:
    colors = {
        "red": Fore.RED,
        "blue": Fore.BLUE,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "cyan": Fore.CYAN,
        "magenta": Fore.MAGENTA,
        "white": Fore.WHITE,
        "black": Fore.BLACK,
        "grey": Fore.LIGHTBLACK_EX
    }

    if color in colors:
        color = colors[color]

    return f"{color}{text}{Style.RESET_ALL}"

def colorize_json(json_str: Dict[Any, Any], indent: int = 2) -> str:
    color_map = {
        "messages": Fore.BLUE,
        "message": Fore.BLUE,
        "role": Fore.CYAN,

        "function": Fore.GREEN,
        "name": Fore.YELLOW,
        "properties": Fore.GREEN,
        "arguments": Fore.GREEN,
        "parameters": Fore.GREEN,
        "description": Fore.GREEN,

        "tools": Fore.YELLOW,
        "tool_calls": Fore.YELLOW,
        "tool_name": Fore.YELLOW,
        "results": Fore.YELLOW,
        "result": Fore.YELLOW,

        "required": Fore.RED,
        "error": Fore.RED,

        "content": Fore.MAGENTA,
        "text": Fore.MAGENTA,
        # Add more keys and colors as needed
    }
    
    # Default color for keys not in the map (grey)
    default_color = Fore.LIGHTBLACK_EX
    
    # Process the JSON string to add colors
    lines = json_str.split('\n')
    colored_lines = []
    
    for line in lines:
        # Find the key if this line contains one
        if ':' in line:
            key_part = line.split(':', 1)[0].strip(' "')
            
            # Determine color for this key
            color = color_map.get(key_part, default_color)
            
            # Colorize the key part
            colored_line = line.replace(f'"{key_part}":', colorize_text(key_part, color))
            colored_lines.append(colored_line)
        else:
            colored_lines.append(line)
    
    return "\n".join(colored_lines)

def prettify(data):
    import json
    
    try:
        data = recursive_unescape(data)
    except Exception as e:
        pass
    
    try:
        formatted_data = data
        if not isinstance(data, str):
            formatted_data = json.dumps(data, indent=1, default=complex_handler)
    except TypeError:
        formatted_data = str(data)

    return colorize_json(formatted_data)