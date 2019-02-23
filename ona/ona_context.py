import asyncio
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
        # split the message into two messages if it's longer than the Discord character limit
        if len(content) > char_limit:
            super().send(content[:char_limit])
            content = content[char_limit:]
        if not yes_or_no:
            return await super().send(content, **kwargs)

        # return True or False depending on which reaction the user chooses
        message = await super().send(content, **kwargs)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(reaction, user):
            return reaction.message.id == message.id and user == self.member and reaction.emoji in "✅❌"
        try:
            reaction, _ = await self.ona.wait_for('reaction_add', timeout=self.config.response_timeout, check=check)
        except asyncio.TimeoutError:
            raise self.ona.OnaError("You took too long to react with ✅ or ❌.")
        finally:
            await message.delete()
        return reaction.emoji == "✅"
