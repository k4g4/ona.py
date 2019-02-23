import asyncio
import discord
from discord.ext import commands


class Events:
    '''Event coroutines are kept in this class to reduce clutter.'''

    def __init__(self, ona):
        self.ona = ona

    async def on_ready(self):
        await self.ona.log("I am now logged in!")

    async def on_message(self, message):
        if message.author.bot:
            return

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance(error, commands.CommandOnCooldown):
            cooldown = round(error.retry_after) + 1
            error_text = f"You need to wait {cooldown} more {ctx.ona.plural('second', cooldown)}."
        elif isinstance(error, commands.CheckFailure):
            error_text = "You don't have permission to do that!"
        elif isinstance(error, ctx.ona.OnaError):
            error_text = error
        else:
            await ctx.ona.log(error)
            return

        error_message = await ctx.send(f"{error_text} {ctx.ona.get_emoji(ctx.config.error)}")
        await asyncio.sleep(ctx.config.error_delete_timer)
        try:
            await ctx.channel.delete_messages([ctx.message, error_message])
        except discord.Forbidden:
            pass


def setup(ona):
    ona.add_cog(Events(ona))
