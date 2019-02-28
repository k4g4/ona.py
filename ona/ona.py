from datetime import datetime
from discord.ext import commands
from .db import OnaDB
from .context import OnaContext
from .config_parser import OnaConfigParser
from .help_formatter import OnaHelpFormatter
from .utils import OnaUtilsMixin, is_owner, not_blacklisted, not_silenced

__author__ = 'kaga'


class Ona(commands.Bot, OnaUtilsMixin):
    '''A multipurpose Discord bot developed by Kaga#0690.'''

    def __init__(self):
        self.uptime = datetime.utcnow()
        self.config = OnaConfigParser("config.ini")
        self.secrets = OnaConfigParser("secrets.ini")
        formatter = OnaHelpFormatter(self, width=self.config.help_width)

        super().__init__(command_prefix=self.config.command_prefix, formatter=formatter)

        self.guild_db = OnaDB(self, "guilds")
        self.user_db = OnaDB(self, "users")

        self.add_command(self.reload)
        self.remove_command("help")
        self.add_check(not_blacklisted)
        self.add_check(not_silenced)

        for cog in self.config.cogs:
            try:
                self.load_extension(cog)
            except Exception as e:
                print(e)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=OnaContext)
        await self.invoke(ctx)

    @commands.command()
    @commands.check(is_owner)
    async def reload(ctx):
        '''Update code for all commands, reload config settings, and refresh all cooldowns.'''
        ctx.ona.config = OnaConfigParser("config.ini")
        try:
            for cog in ctx.ona.config.cogs:
                ctx.ona.unload_extension(cog)
                ctx.ona.load_extension(cog)
        except Exception as e:
            raise ctx.ona.OnaError(f"Error in {cog}: {e}")
        else:
            await ctx.clean_up(await ctx.send("All commands were reloaded successfully."))

    def run(self):
        super().run(self.secrets.token)
