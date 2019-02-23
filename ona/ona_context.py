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

    async def send(self, content, **kwargs):
        # split the message into two messages if it's longer than the Discord character limit
        if len(content) > char_limit:
            super().send(content[:char_limit])
            content = content[char_limit:]
        await super().send(content, **kwargs)
