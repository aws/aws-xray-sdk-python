import asyncio
import random
import sys

from aws_xray_sdk.core.async_context import TaskLocalStorage


def test_localstorage_isolation(event_loop):
    local_storage = TaskLocalStorage(loop=event_loop)

    async def _test():
        """
        Compute a random number
        Store it in task local storage
        Suspend task so another can run
        Retrieve random number from task local storage
        Compare that to the local variable
        """
        try:
            random_int = random.random()
            local_storage.randint = random_int

            if sys.version_info >= (3, 8):
                await asyncio.sleep(0.0)
            else:
                await asyncio.sleep(0.0, loop=event_loop)

            current_random_int = local_storage.randint
            assert random_int == current_random_int

            return True
        except:
            return False

    # Run loads of concurrent tasks
    if sys.version_info >= (3, 8):
        results = event_loop.run_until_complete(
            asyncio.wait([event_loop.create_task(_test()) for _ in range(0, 100)])
        )
    else:
        results = event_loop.run_until_complete(
            asyncio.wait(
                [event_loop.create_task(_test()) for _ in range(0, 100)],
                loop=event_loop,
            )
        )
    results = [item.result() for item in results[0]]

    # Double check all is good
    assert all(results)
