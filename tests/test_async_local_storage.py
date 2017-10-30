import asyncio
import random

from aws_xray_sdk.core.async_context import TaskLocalStorage


def test_localstorage_isolation(loop):
    local_storage = TaskLocalStorage(loop=loop)

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

            await asyncio.sleep(0.0, loop=loop)

            current_random_int = local_storage.randint
            assert random_int == current_random_int

            return True
        except:
            return False

    # Run loads of concurrent tasks
    results = loop.run_until_complete(
        asyncio.wait([_test() for _ in range(0, 100)], loop=loop)
    )
    results = [item.result() for item in results[0]]

    # Double check all is good
    assert all(results)
