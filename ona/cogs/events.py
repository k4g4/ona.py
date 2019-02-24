import asyncio
import discord
from discord.ext import commands


class Events:
    '''Event coroutines are kept in this class to reduce clutter.'''

    def __init__(self, ona):
        self.ona = ona

    async def on_ready(self):
        listening = discord.ActivityType.listening
        listening_to_help = discord.Activity(type=listening, name=f"{self.ona.config.command_prefix}help")
        await self.ona.change_presence(activity=listening_to_help)
        await self.ona.log("Ona has logged in.")

    async def on_message(self, message):
        if message.author.bot:
            return

    async def on_message_edit(self, before, after):
        if after.author.bot:
            return
        await self.ona.process_commands(after)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance(error, commands.CommandOnCooldown):
            cooldown = round(error.retry_after) + 1
            error_text = f"This command is on cooldown for {self.ona.plural(cooldown, 'second')}."
        elif isinstance(error, commands.CheckFailure):
            error_text = "You don't have permission to do that!"
        elif isinstance(error, self.ona.OnaError):
            error_text = str(error)
        else:
            await self.ona.log(str(error))
            return
        await ctx.clean_up(await ctx.send(f"{error_text} {self.ona.get_emoji(ctx.config.error)}"))


def setup(ona):
    ona.add_cog(Events(ona))
