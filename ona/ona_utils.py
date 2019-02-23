import discord


class OnaUtilsMixin:
    '''Various bot utilities are kept in this class.'''

    def get(self, iterable, **attrs):
        return discord.utils.get(iterable, **attrs)

    def get_emoji_named(self, name):
        return self.get(self.emojis, name=name)

    def quick_embed(self, content, *, title=None, author=None):
        embed = discord.Embed(description=content, title=title, color=self.config.color)
        if author:
            embed.set_author(name=author.display_name, icon_url=author.avatar_url)
        return embed

    async def log(self, content):
        print(content)
        logs = self.get_channel(self.config.logs)
        await logs.send(embed=self.quick_embed(content))


# Various command checks

def is_staff(ctx):
    return any(role.id in (ctx.config.admin, ctx.config.mod) for role in ctx.member.roles)


def is_admin(ctx):
    return any(role.id == ctx.config.admin for role in ctx.member.roles)
