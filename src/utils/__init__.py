import inspect

def mainloop(func):
    async def _decorator(*args, **kwargs):
        while True:
            await func(*args, **kwargs)
    return _decorator

def graceful_exit(func):
    if inspect.iscoroutinefunction(func):
        def _decorator(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                print("\nBye!")
                exit(0)
            except Exception as e:
                print(f"Error: {e}")
                return None
        return _decorator
    
    async def _async_decorator(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except KeyboardInterrupt:
            print("\nBye!")
            exit(0)
        except Exception as e:
            print(f"Error: {e}")
    return _async_decorator

def chatutil(chat_name):
    def _decorator(func):
        async def _wrapper(*args, **kwargs):
            arguments = (input(f"<{chat_name}> "),) + args
            result = await func(*arguments, **kwargs)

            hr = "\n" + "-" * 50 + "\n"
            print(hr, f"<Response> {result}", hr)
        return _wrapper
    return _decorator