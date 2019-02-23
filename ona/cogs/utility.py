import time
import asyncio
from datetime import datetime, timedelta
from discord.ext import commands


class Utility:
    '''These commands perform a variety of useful tasks.'''

    def __init__(self, ona):
        self.ona = ona

    @commands.command()
    async def ping(self, ctx):
        '''Check Ona's response time.'''
        start = time.time()
        message = await ctx.send("My ping is...")
        await asyncio.sleep(3)
        end = time.time()
        await message.edit(content=f"My ping is... **{round((end-start-3) * 1000, 2)}** milliseconds.")
        await ctx.clean_up(message)

    @commands.command()
    async def uptime(self, ctx):
        '''Check how long Ona has been running for.'''
        delta = datetime.utcnow() - self.ona.uptime
        uptime = self.ona.plural('day', delta.days) if delta.days else self.ona.plural('second', delta.seconds)
        await ctx.clean_up(await ctx.send(f"I've been running for {uptime}."))


def setup(ona):
    ona.add_cog(Utility(ona))
