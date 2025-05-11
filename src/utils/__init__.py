import inspect

from .pretty import colorize_text

DEBUG = False
def set_debug(debug):
    global DEBUG
    DEBUG = debug

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
    from .pretty import prettify

    hr = "#" * 50
    header = f"\n{hr} <{name}> {hr}\n"
    footer = f"\n####{hr * 2}{"#" * len(name)}"
    if color:
        header = colorize_text(header, color)
        footer = colorize_text(footer, color)

    print(header, prettify(data), footer)