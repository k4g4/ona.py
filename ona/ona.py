from datetime import datetime
from discord.ext import commands
from .db import OnaDB
from .config_parser import OnaConfigParser
from .help_formatter import OnaHelpFormatter
from .utils import OnaUtilsMixin, not_blacklisted, not_silenced

__author__ = 'kaga'

config_files = ["config.ini", "secrets.ini", "guild.ini", "user.ini"]


class Ona(commands.Bot, OnaUtilsMixin):
    '''A multipurpose Discord bot developed by Kaga#0690.'''

    def __init__(self):
        self.uptime = datetime.utcnow()
        (self.config, self.secrets,
         self.guild_template, self.user_template) = map(OnaConfigParser, config_files)
        formatter = OnaHelpFormatter(self, width=self.config.help_width)

        def get_prefix(ona, message):   # The prefix is chosen depending on the server's settings
            return ona.guild_db.get_doc(message.guild.id if message.guild else 0).prefix
        super().__init__(command_prefix=get_prefix, formatter=formatter)

        self.add_command(self.reload)
        self.remove_command("help")
        self.add_check(not_blacklisted)
        self.add_check(not_silenced)

        for extension in self.config.extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(e)

    async def process_commands(self, message):
        await self.invoke(await self.get_context(message, cls=self.OnaContext))

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

    def run(self):
        super().run(self.secrets.token)
