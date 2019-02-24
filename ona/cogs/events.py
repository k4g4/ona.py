import asyncio
import discord
from discord.ext import commands


class Events:
    '''Event coroutines are kept in this class to reduce clutter.'''

    def __init__(self, ona):
        self.ona = ona

    async def on_ready(self):
        await self.ona.log("I am now logged in!")
        virgin = next(role for role in self.ona.guilds[0].roles if "1. Virgin" == role.name)
        sinner = next(role for role in self.ona.guilds[0].roles if "Ⅰ) SINNER" == role.name)
        for user in self.ona.guilds[0].members:
            if sinner not in user.roles and virgin in user.roles:
                await user.add_roles(sinner)
                print(user)
                await asyncio.sleep(.5)

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
            error_text = f"This command is on cooldown for {self.ona.plural('second', cooldown)}."
        elif isinstance(error, commands.CheckFailure):
            error_text = "You don't have permission to do that!"
        elif isinstance(error, self.ona.OnaError):
            error_text = error
        else:
            await self.ona.log(str(error))
            return

        error_message = await ctx.send(f"{error_text} {self.ona.get_emoji(ctx.config.error)}")
        await asyncio.sleep(ctx.config.short_delete_timer)
        await ctx.clean_up(error_message)


def setup(ona):
    ona.add_cog(Events(ona))
