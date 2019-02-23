from os import path
from discord.ext import commands
from .ona_context import OnaContext
from .ona_configparser import OnaConfigParser
from .ona_events import OnaEventsMixin
from .ona_utils import OnaUtilsMixin


class Ona(commands.Bot, OnaEventsMixin, OnaUtilsMixin):
    '''A multipurpose Discord bot.'''

    def __init__(self):
        self.config = OnaConfigParser("config.ini")
        self.secrets = OnaConfigParser("secrets.ini")
        super().__init__(command_prefix=self.config.command_prefix)
        self.add_command(self.reload)
        for cog in self.config.cogs:
            try:
                self.load_extension(cog)
            except Exception as e:
                print(e)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=OnaContext)
        await self.invoke(ctx)

    @commands.command()
    async def reload(self, ctx):
        for cog in self.config.cogs:
            try:
                self.unload_extension(cog)
                self.load_extension(cog)
            except Exception as e:
                ctx.send(f"An error occurred: {e}")
            else:
                ctx.send(f"All commands were reloaded successfully.")

    def run(self):
        super().run(self.secrets.token)
