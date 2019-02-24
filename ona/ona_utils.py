import discord
from datetime import timedelta, datetime
from discord.ext import commands


class OnaUtilsMixin:
    '''Various bot utilities are kept in this class.'''

    # All errors that are displayed to the user instead of being logged
    class OnaError(commands.CommandError):
        pass

    def get(self, iterable, **attrs):
        return discord.utils.get(iterable, **attrs)

    def get_emoji_named(self, name):
        return self.get(self.emojis, name=name)

    def quick_embed(self, content, *, title=None, author=None):
        embed = discord.Embed(description=content, title=title, color=self.config.ona_color)
        if author:
            embed.set_author(name=author.display_name, icon_url=author.avatar_url)
        return embed

    @staticmethod
    def plural(value, word):
        value = int(value) if float(value).is_integer() else value  # Remove .0 if it exists
        return f"one {word}" if value == 1 else f"{value:,} {word}s"

    async def log(self, content):
        print(content)
        logs = self.get_channel(self.config.logs)
        await logs.send(embed=self.quick_embed(content, title="OnaLogger"))


# Various command checks

def is_staff(ctx):
    if hasattr(ctx.author, "roles"):
        return any(role.id in [ctx.config.admin, ctx.config.mod] for role in ctx.author.roles)


def is_admin(ctx):
    if hasattr(ctx.author, "roles"):
        return any(role.id == ctx.config.admin for role in ctx.author.roles)


def is_owner(ctx):
    return ctx.ona.is_owner(ctx.author)


async def image_throttle(ctx):
    if ctx.message.id not in ctx.config.image_throttle or is_admin(ctx):
        return True
    last_ten = await ctx.history(limit=10).flatten()
    if sum(len(message.attachments) for message in last_ten) > 2:
        raise OnaError("There are too many images here. Try again later!")


async def chat_throttle(ctx):
    if ctx.message.id not in ctx.config.chat_throttle or is_admin(ctx):
        return True
    async for message in ctx.history(limit=10):
        oldest = message
    if oldest.timestamp + timedelta(0, 40) > datetime.utcnow():
        raise OnaError("The chat is too active. Try again later!")
