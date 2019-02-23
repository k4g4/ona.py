from asyncio import get_event_loop
from ona.ona_bot import Ona

if __name__ == '__main__':
    loop = get_event_loop()
    loop.run_until_complete(Ona().run())
    loop.close()
