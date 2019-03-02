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
        config_files = ["config.ini", "secrets.ini", "guild.ini", "user.ini"]
        self.config, self.secrets, guild_template, user_template = map(OnaConfigParser, config_files)
        self.guild_db = OnaDB(self, self.config.guild_db, guild_template.to_dict())
        self.user_db = OnaDB(self, self.config.user_db, user_template.to_dict())
        formatter = OnaHelpFormatter(self, width=self.config.help_width)

        def get_prefix(ona, message):
            return ona.guild_db.get_doc(message.guild.id if message.guild else 0).prefix
        super().__init__(command_prefix=get_prefix, formatter=formatter)

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
        await self.invoke(await self.get_context(message, cls=OnaContext))

    @commands.command()
    @commands.check(is_owner)
    async def reload(ctx):
        '''Update code for all commands, reload config settings, and refresh all cooldowns.'''
        config_files = ["config.ini", "secrets.ini", "guild.ini", "user.ini"]
        ctx.ona.config, ctx.ona.secrets, guild_template, user_template = map(OnaConfigParser, config_files)
        ctx.ona.guild_db = OnaDB(ctx.ona, ctx.ona.config.guild_db, guild_template.to_dict())
        ctx.ona.user_db = OnaDB(ctx.ona, ctx.ona.config.user_db, user_template.to_dict())

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
