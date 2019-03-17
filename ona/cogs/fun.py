import discord
from io import BytesIO
from discord.ext import commands
from PIL import Image, ImageFilter


class Fun(commands.Cog):
    '''Interesting and fun commands to play with.'''

    def __init__(self, ona):
        self.ona = ona

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def filter(self, ctx, filter: str = "blur", url: str = None):
        '''Apply a filter to an image.
        The available filters are: blur, contour, detail, edge_enhance, edge_enhance_more, emboss,
        find_edges, sharpen, smooth, and smooth_more.'''
        try:
            filter = getattr(ImageFilter, filter.upper())
        except AttributeError:
            raise self.ona.OnaError(f"That filter isn't recognized. Use `{ctx.prefix}help filter` to see all filters.")
        url = url or await ctx.get_attachment()
        image = Image.open(BytesIO(await self.ona.request(url)))
        blurred_image = BytesIO()
        try:
            image.filter(filter).save(blurred_image, format="PNG")
        except ValueError:
            raise self.ona.OnaError("That image format is not accepted.")
        blurred_image.seek(0)
        await ctx.send(file=discord.File(blurred_image, self.ona.filename_from_url(url)))


def setup(ona):
    ona.add_cog(Fun(ona))
