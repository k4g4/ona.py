import random
import discord
from io import BytesIO
from discord.ext import commands
from PIL import Image, ImageFilter, ImageOps


class Fun(commands.Cog):
    '''Interesting and fun commands to play with.'''

    def __init__(self, ona):
        self.ona = ona

    @commands.command()
    async def ask(self, ctx):
        '''Ask a yes or no question.'''
        await ctx.send(random.choice(self.ona.config.replies))

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def ship(self, ctx, *members: discord.Member):
        '''Create a ship between two (or more) members.'''
        members = members or [(await ctx.history(before=ctx.message).next()).author]
        members = [*members, ctx.author] if len(members) == 1 else members  # Include the author if only one member
        self.ona.assert_(len(members) <= 10, error="That ship is too big!")
        ship_name = "".join(name[i * (len(name) // len(members)): (i+1) * -(-len(name) // len(members))]
                            for i, name in enumerate(member.display_name for member in members))    # Combine names
        avatar_size = 128
        image = Image.new("RGBA", (len(members) * avatar_size, avatar_size))
        urls = (member.avatar_url_as(static_format="png", size=avatar_size) for member in members)
        avatars = map(Image.open, map(BytesIO, [await self.ona.request(url) for url in urls]))
        for i, avatar in enumerate(avatars):
            image.alpha_composite(avatar.convert(mode="RGBA"), dest=(avatar_size * i, 0))   # Combine avatars
        ship_image = BytesIO()
        image.save(ship_image, format="PNG")
        ship_image.seek(0)
        await ctx.send(f"Your ship's name is **{ship_name}!** {self.ona.config.heart_eyes}",
                       file=discord.File(ship_image, f"{ctx.message.id}.png"))

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def filter(self, ctx, filter="blur", url=None):
        '''Apply a filter to an image.
        The available filters are: blur, contour, detail, edge_enhance, edge_enhance_more, emboss,
        find_edges, sharpen, smooth, and smooth_more.'''
        try:
            filter = getattr(ImageFilter, filter.upper())
        except AttributeError:
            raise self.ona.OnaError(f"That filter isn't recognized. Use `{ctx.prefix}help filter` to see all filters.")
        url = url or await ctx.get_attachment()
        image = Image.open(BytesIO(await self.ona.request(url)))
        filtered_image = BytesIO()
        try:
            image.filter(filter).save(filtered_image, format="PNG")
        except ValueError:
            raise self.ona.OnaError("That image format is not accepted.")
        filtered_image.seek(0)
        await ctx.send(file=discord.File(filtered_image, self.ona.filename_from_url(url)))


def setup(ona):
    ona.add_cog(Fun(ona))
