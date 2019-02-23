from discord.ext import commands
from .ona_context import OnaContext
from .ona_configparser import OnaConfigParser
from .ona_utils import OnaUtilsMixin, is_staff


class Ona(commands.Bot, OnaUtilsMixin):
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
    @commands.check(is_staff)
    async def reload(self, ctx):
        '''Update code for all commands, reload config settings, and refresh all cooldowns.'''
        self.config = OnaConfigParser("config.ini")
        try:
            for cog in self.config.cogs:
                self.unload_extension(cog)
                self.load_extension(cog)
        except Exception as e:
            raise self.OnaError(str(e))
        else:
            await ctx.send("All commands were reloaded successfully.")

    def run(self):
        super().run(self.secrets.token)
