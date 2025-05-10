def chatloop(chat_name):
    def _decorator(func):
        async def _wrapper(*args, **kwargs):
            while True:
                try:
                    arguments = (input(f"<{chat_name}> "),) + args
                    result = await func(*arguments, **kwargs)

                    hr = "\n" + "-" * 50 + "\n"
                    print(hr, f"<Response> {result}", hr)
                except Exception as e:
                    print(f"Error: {e}")
                except KeyboardInterrupt:
                    print("\nBye!")
                    break
        return _wrapper
    return _decorator