import time
import asyncio
from discord.ext import commands


class Utility:
    '''These commands perform a variety of useful tasks.'''

    def __init__(self, ona):
        self.ona = ona

    @commands.command()
    async def ping(self, ctx):
        '''Check the bot's response time.'''
        start = time.time()
        message = await ctx.send("My ping is...")
        await asyncio.sleep(3)
        end = time.time()
        await message.edit(content=f"My ping is... **{round((end-start-3) * 1000, 2)}** milliseconds.")
        await ctx.clean_up(message)


def setup(ona):
    ona.add_cog(Utility(ona))
