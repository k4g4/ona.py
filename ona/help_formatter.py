import discord
from itertools import groupby
from discord.ext import commands


class OnaHelpFormatter(commands.HelpFormatter):
    '''A custom help formatter that uses Embeds.'''

    def __init__(self, ona, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ona = ona

    async def format(self):
        no_desc = "*No description provided.*"
        embed = self.ona.quick_embed(title=self.ona.user.name)
        embed.set_thumbnail(url=self.ona.user.avatar_url)
        # The help page for a single command
        if isinstance(self.command, commands.Command):
            embed.title = self.context.guild_doc.prefix + self.command.signature
            embed.description = self.command.help if self.command.help else no_desc
            cd = self.command._buckets._cooldown
            if cd:
                value = f"{self.ona.plural(cd.rate, 'time').capitalize()} every {self.ona.plural(cd.per, 'second')}."
                embed.add_field(name="Cooldown", value=value)
            return embed

        # The help page for all commands
        embed.description = self.command.__doc__

        def key(cmd):
            return cmd[1].cog_name if cmd[1].cog_name else ""

        def cmd_format(name, cmd):
            return f"**{name}**: {self.shorten(cmd.help) if cmd.help else no_desc}"

        for cog, cmds in groupby(sorted(await self.filter_command_list(), key=key), key=key):
            cmds = list(cmds)
            if cmds:
                subcmds = "\n".join(cmd_format(name, cmd) for name, cmd in cmds if name not in cmd.aliases)
                embed.add_field(name=cog if cog else "Other", value=subcmds)
        embed.set_footer(text=f"Use {self.context.guild_doc.prefix}help [command] for details on any command.")
        return embed
