import asyncio
import discord
from discord.ext import commands

event = commands.Cog.listener()


class Events(commands.Cog):
    '''Event coroutines are kept in this class to reduce clutter.'''

    def __init__(self, ona):
        self.ona = ona

    @event
    async def on_ready(self):
        listening = discord.ActivityType.listening
        listening_to_help = discord.Activity(type=listening, name=f"{self.ona.guild_db.get_doc(0).prefix}help")
        await self.ona.change_presence(activity=listening_to_help)
        content = "Ona has logged in."
        print(content)
        await self.ona.log(self.ona.get_guild(self.ona.config.main_guild), content)

    @event
    async def on_message(self, message):
        if message.author.bot:
            return

    @event
    async def on_message_edit(self, before, after):
        if after.author.bot:
            return
        await self.ona.process_commands(after)
        # await self.ona.log(before.guild, )

    @event
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance(error, commands.CommandOnCooldown):
            cooldown = round(error.retry_after) + 1
            error_text = f"This command is on cooldown for {self.ona.plural(cooldown, 'second')}."
        elif isinstance(error, commands.MissingPermissions):
            if ctx.guild:
                error_text = f"You need the `{error.missing_perms[0].title()}` permission."
            else:
                error_text = "You need to be in a server to use this command."
        elif isinstance(error, commands.CheckFailure):
            error_text = "You don't have permission to do that!"
        elif isinstance(error, self.ona.OnaError):
            error_text = str(error)
        else:
            print(error)
            await self.ona.log(self.ona.config.main_guild, f"Error: {error}")
            return
        await ctx.clean_up(await ctx.send(f"{error_text} {self.ona.config.error}"))


def setup(ona):
    ona.add_cog(Events(ona))
