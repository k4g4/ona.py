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
        if isinstance(self.command, commands.Command):
            embed.title = self.get_command_signature()
            return embed

        def key(cmd):
            return cmd[1].cog_name
        for cog, cmds in groupby(sorted(await self.filter_command_list(), key=key), key=key):
            cmds = list(cmds)
            if cmds:
                subcmds = "\n".join(f"**{name}**: {cmd.help}" for name, cmd in cmds)
                embed.add_field(name=cog.upper(), value=subcmds)

        return embed
