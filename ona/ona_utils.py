import discord
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
    def plural(word, value):
        return f"one {word}" if value == 1 else f"{value:,} {word}s"

    async def log(self, content):
        print(content)
        logs = self.get_channel(self.config.logs)
        await logs.send(embed=self.quick_embed(content, title="OnaLogger"))


# Various command checks

def is_staff(ctx):
    if hasattr(ctx.author, "roles"):
        return any(role.id in (ctx.config.admin, ctx.config.mod) for role in ctx.author.roles)
    else:
        return ctx.author.id == ctx.application_info().owner


def is_admin(ctx):
    if hasattr(ctx.member, "roles"):
        return any(role.id == ctx.config.admin for role in ctx.member.roles)
    else:
        return ctx.member.id == ctx.config.owner
