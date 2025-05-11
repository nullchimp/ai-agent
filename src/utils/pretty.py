from typing import Dict, Any
import json
from colorama import Fore, Style, init

init(autoreset=True)

def colorize_json(json_str: Dict[Any, Any], indent: int = 2) -> str:
    color_map = {
        "messages": Fore.BLUE,
        "message": Fore.BLUE,
        "role": Fore.CYAN,

        "function": Fore.GREEN,
        "name": Fore.GREEN,
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
            colored_line = line.replace(f'"{key_part}":', f'{color}"{key_part}":{Style.RESET_ALL}')
            colored_lines.append(colored_line)
        else:
            colored_lines.append(line)
    
    return "\n".join(colored_lines)


def prettify(data):
    import json
    
    def recursive_unescape(value):
        """
        Recursively unescape a string or objects containing strings.
        Handles JSON strings that might be escaped multiple times.
        """
        if isinstance(value, str):
            # Try to detect and parse JSON strings
            try:
                # Only attempt to parse if it looks like JSON
                if (value.startswith('{') and value.endswith('}')) or \
                   (value.startswith('[') and value.endswith(']')) or \
                   (value.startswith('"') and value.endswith('"')):
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
        else:
            # Return other types unchanged
            return value
    
    def complex_handler(obj):
        """Handle complex objects for JSON serialization"""
        if hasattr(obj, '__dict__'):
            return recursive_unescape(obj.__dict__)
        else:
            raise TypeError(f'Object of type {type(obj)} is not JSON serializable')
    
    # Apply recursive unescaping if data is a string
    if isinstance(data, str):
        try:
            data = recursive_unescape(data)
        except Exception as e:
            # If unescaping fails, use original data
            pass
    else:
        # For non-string data, still process it to handle nested structures
        data = recursive_unescape(data)
    
    # Dump the processed data to JSON
    try:
        formatted_data = json.dumps(data, indent=1, default=complex_handler)
    except TypeError:
        # Fallback for objects that can't be serialized
        formatted_data = str(data)

    return colorize_json(formatted_data)