from asyncio import get_event_loop
from ona.ona import Ona

loop = get_event_loop()
loop.run_until_complete(Ona().run())
loop.close()
