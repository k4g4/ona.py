import discord
from itertools import groupby
from discord.ext import commands


class OnaHelpFormatter(commands.HelpFormatter):
    '''A custom help formatter that uses Embeds.'''

    def __init__(self, ona, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ona = ona

    async def format(self):
        description = self.command.help if hasattr(self.command, "help") else self.command.__doc__
        embed = discord.Embed(description=description, color=self.ona.config.ona_color)
        embed.set_author(name=self.ona.user.name, icon_url=self.ona.user.avatar_url)
        # The help page for a single command
        if isinstance(self.command, commands.Command):
            embed.title = self.get_command_signature()
            cooldown = self.command._buckets._cooldown
            if cooldown:
                embed.description += (f"\n\nThis command can be used {self.ona.plural(cooldown.rate, 'time')} " +
                                      f"every {self.ona.plural(cooldown.per, 'second')}.")
            return embed

        # The help page for all commands
        def key(cmd):
            return cmd[1].cog_name

        def cmd_format(name, cmd):
            return f"**{name}**: {self.shorten(cmd.help)}"

        for cog, cmds in groupby(sorted(await self.filter_command_list(), key=key), key=key):
            cmds = list(cmds)
            if cmds:
                subcmds = "\n".join(cmd_format(name, cmd) for name, cmd in cmds if name not in cmd.aliases)
                embed.add_field(name=cog, value=subcmds)
        embed.set_footer(text=f"Use {self.ona.config.command_prefix}help [command] for details on a single command.")
        return embed
