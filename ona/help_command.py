import discord
from itertools import groupby
from discord.ext import commands

no_desc = "*No description provided.*"


class OnaHelpCommand(commands.HelpCommand):
    '''A custom help command formatter that uses embeds instead of codeblocks.'''

    async def prepare_help_command(self, ctx, command=None):
        self.context = ctx
        self.help_embed = ctx.ona.quick_embed(title=ctx.me.name)
        self.help_embed.set_thumbnail(url=ctx.me.avatar_url)

    async def send_command_help(self, command):
        self.help_embed.title = self.get_command_signature(command)
        self.help_embed.description = command.help or no_desc
        cd = command._buckets._cooldown
        if cd:
            value = (f"{self.context.ona.plural(cd.rate, 'time').capitalize()} "
                     f"every {self.context.ona.plural(cd.per, 'second')}.")
            self.help_embed.add_field(name="Cooldown", value=value)
        await self.context.send(embed=self.help_embed)

    async def send_bot_help(self, mapping):
        ona = self.context.ona
        self.help_embed.description = ona.__doc__

        def get_cog_name(command):
            return command.cog.qualified_name if command.cog else "\u200bNo Category"

        def command_format(command):
            width = 47
            desc = command.short_doc or no_desc
            return f"**{command.name}**: {desc[:width] + '...' if len(desc) > width else desc}"

        to_iterate = groupby(await self.filter_commands(ona.commands, sort=True, key=get_cog_name), key=get_cog_name)
        for cog_name, commands in to_iterate:
            formatted_commands = "\n".join(command_format(command) for command in commands)
            self.help_embed.add_field(name=cog_name, value=formatted_commands)

        self.help_embed.set_footer(text=f"Use {self.clean_prefix}help [command] for details on any command.")
        await self.context.whisper(embed=self.help_embed)


def setup(ona):
    ona.help_command = OnaHelpCommand()
