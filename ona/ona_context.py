import asyncio
import discord
from discord.ext import commands

char_limit = 2000


class OnaContext(commands.Context):

    @property
    def ona(self):
        return self.bot

    @property
    def config(self):
        return self.bot.config

    @property
    def member(self):
        return self.message.author

    @property
    def channel(self):
        return self.message.channel

    @property
    def guild(self):
        return self.message.guild if hasattr(self.message, "guild") else None

    async def send(self, content, yes_or_no=False, **kwargs):
        '''This custom send method adds special functionality such as sending messages over
        the Discord character limit and asking the user a yes/no question.'''
        # split the message into separate messages if it's longer than the Discord character limit
        messages = []
        while len(content) > char_limit:
            messages.append(await super().send(content[:char_limit]))
            content = content[char_limit:]
        if not yes_or_no:
            messages.append(await super().send(content, **kwargs))
            return messages[-1]

        # return True or False depending on which reaction the user chooses
        message = await super().send(content, **kwargs)
        messages.append(message)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(reaction, user):
            return reaction.message.id == message.id and user == self.member and reaction.emoji in "✅❌"
        try:
            reaction, _ = await self.ona.wait_for('reaction_add', timeout=self.config.response_timeout, check=check)
        except asyncio.TimeoutError:
            raise self.ona.OnaError("You took too long to react with ✅ or ❌.")
        finally:
            if isinstance(self.channel, discord.TextChannel):
                await self.channel.delete_messages(messages)
        return reaction.emoji == "✅"

    async def clean_up(self, *messages):
        '''When done with a command, call clean_up with an argument-list of messages to delete them all
        as well as the initial command message if Ona has permission.'''
        if not isinstance(self.channel, discord.TextChannel):
            return
        if self.channel.permissions_for(self.guild.me).manage_messages:
            messages += (self.message,)
        await asyncio.sleep(self.config.short_delete_timer)
        await self.channel.delete_messages(messages)
