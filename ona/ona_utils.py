import discord


class OnaUtilsMixin:
    '''Various bot utilities are kept in this class.'''

    def get(self, iterable, **attrs):
        return discord.utils.get(iterable, **attrs)

    def get_emoji_named(self, name):
        return self.get(self.emojis, name=name)

    async def log(self, content):
        print(content)
        logs = self.get_channel(self.config.logs)
        await logs.send(content)
