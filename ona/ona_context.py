import asyncio
import discord
from discord.ext import commands

char_limit = 2000


class OnaContext(commands.Context):
    '''Custom Context class with some quality of life attributes.'''

    @property
    def ona(self):
        return self.bot

    @property
    def config(self):
        return self.bot.config

    def get_role_named(self, name):
        '''Return a role in the context's guild if it exists, otherwise None.'''
        if self.guild:
            return self.ona.get(self.guild.roles, name=name)

    async def send(self, content="", yes_or_no=False, **kwargs):
        '''This custom send method adds special functionality such as sending messages over
        the Discord character limit and asking the user a yes/no question.'''
        # split the message into separate messages if it's longer than the Discord character limit
        while len(content) > char_limit:
            await super().send(content[:char_limit])
            content = content[char_limit:]
        if not yes_or_no:
            message = await super().send(content, **kwargs)
            return message

        # return True or False depending on which reaction the user chooses
        message = await super().send(content, **kwargs)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(reaction, user):
            return reaction.message.id == message.id and user == self.author and reaction.emoji in "✅❌"
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
        if self.channel.permissions_for(self.me).manage_messages:
            messages += (self.message,)
        await asyncio.sleep(self.config.short_delete_timer)
        await self.channel.delete_messages(messages)

    async def whisper(self, *args, **kwargs):
        """DM a user instead of sending a message to the chat."""
        if isinstance(self.channel, discord.TextChannel):
            await self.clean_up(await self.send(f"{self.author.mention} Check your DM!"))
        return await self.author.send(*args, **kwargs)

    def ona_assert(self, *assertions, error):
        '''Assert that all provided assertions are True. If one is False, raise an OnaError.'''
        if not all(assertions):
            raise self.ona.OnaError(error)
