class OnaEventsMixin:
    '''Event coroutines are kept in this class to reduce clutter.'''

    async def on_ready(self):
        await self.log("I am now logged in!")
