import asyncio

import agent, chat

async def process_one():
    while True:
        print("Processing one...")
        await asyncio.sleep(1)

async def process_two():
    await agent.run_conversation()

async def main():
    # Run both coroutines concurrently
    await asyncio.gather(
        process_one(), 
        process_two()
    )

if __name__ == "__main__":
    asyncio.run(main())