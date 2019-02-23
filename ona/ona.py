import sys
from discord.ext import commands
from ona_context import OnaContext


class Ona(commands.Bot):
    """A multipurpose Discord bot."""

    def __init__(self):
        self.config = None
        self.secrets = None
        super().__init__(command_prefix=self.config.command_prefix)
        for cog in self.config.cogs:
            try:
                self.load_extension(cog)
            except Exception as e:
                pass

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=OnaContext)
        await self.invoke(ctx)

    @commands.command()
    async def reload(self, ctx: Context):
        for cog in self.config.cogs:
            try:
                self.unload_extension(cog)
                self.load_extension(cog)
            except Exception as e:
                pass    # failed
            else:
                pass    # succeeded

    def run(self):
        super().run(self.secrets.token)
