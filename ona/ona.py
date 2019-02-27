from datetime import datetime
from discord.ext import commands
from .context import OnaContext
from .configparser import OnaConfigParser
from .helpformatter import OnaHelpFormatter
from .utils import OnaUtilsMixin, is_owner

__author__ = 'kaga'


class Ona(commands.Bot, OnaUtilsMixin):
    '''A multipurpose Discord bot developed by Kaga#0690.'''

    def __init__(self):
        self.uptime = datetime.utcnow()
        self.config = OnaConfigParser("config.ini")
        self.secrets = OnaConfigParser("secrets.ini")
        formatter = OnaHelpFormatter(self, width=self.config.help_width)
        super().__init__(command_prefix=self.config.command_prefix, formatter=formatter)
        self.add_command(self.reload)
        self.remove_command("help")
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
    async def reload(self, ctx):
        '''Update code for all commands, reload config settings, and refresh all cooldowns.'''
        self.config = OnaConfigParser("config.ini")
        try:
            for cog in self.config.cogs:
                self.unload_extension(cog)
                self.load_extension(cog)
        except Exception as e:
            raise self.OnaError(f"Error in {cog}: {e}")
        else:
            await ctx.clean_up(await ctx.send("All commands were reloaded successfully."))

    def run(self):
        super().run(self.secrets.token)
