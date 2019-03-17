import discord
from datetime import datetime
from discord.ext import commands
from .db import OnaDB
from .config_parser import OnaConfigParser
from .utils import OnaUtilsMixin, not_blacklisted, not_silenced

__author__ = 'kaga'

config_files = ["config.ini", "secrets.ini", "guild.ini", "user.ini"]


class Ona(commands.Bot, OnaUtilsMixin):
    '''A multipurpose Discord bot developed by Kaga#0690.'''

    def __init__(self):
        self.uptime = datetime.utcnow()
        (self.config, self.secrets,
         self.guild_template, self.user_template) = map(OnaConfigParser, config_files)

        def get_prefix(ona, message):
            return ona.guild_db.get_doc(message.guild).prefix   # The prefix is chosen based on the server's settings

        activity = discord.Activity(type=discord.ActivityType.listening, name=self.config.activity)
        super().__init__(command_prefix=get_prefix, activity=activity)

        self.add_command(self.reload)
        self.add_check(not_blacklisted)
        self.add_check(not_silenced)

        for extension in self.config.extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(e)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=self.OnaContext)
        await self.invoke(ctx)
        return ctx if ctx.valid else None   # For use in on_message if needed

    @commands.command()
    @commands.is_owner()
    async def reload(ctx):
        '''Update code, reload config settings, and refresh all cooldowns.'''
        (ctx.ona.config, ctx.ona.secrets,
         ctx.ona.guild_template, ctx.ona.user_template) = map(OnaConfigParser, config_files)
        try:
            for extension in ctx.ona.config.extensions:
                ctx.ona.unload_extension(extension)
                ctx.ona.load_extension(extension)
        except Exception as e:
            raise ctx.ona.OnaError(f"Error in {extension}: {e}")
        else:
            print("Reload completed successfully.")
            await ctx.clean_up(await ctx.send("All commands were reloaded successfully."))

    async def on_message(self, message):
        pass    # Override the call to process_commands, we'll call it in the Events cog instead

    def run(self):
        super().run(self.secrets.token)
