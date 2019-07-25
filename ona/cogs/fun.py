import random
import discord
from io import BytesIO
from typing import Optional
from discord.ext import commands
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageSequence, ImageOps


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
        image = Image.new("RGBA", ((len(members) * 2 - 1) * avatar_size, avatar_size))
        assets = (member.avatar_url_as(static_format="png", size=avatar_size) for member in members)
        avatars = map(Image.open, map(BytesIO, [await asset.read() for asset in assets]))
        heart = Image.open(self.ona.resources["heart"])
        for i, avatar in enumerate(avatars):
            image.alpha_composite(avatar.convert(mode="RGBA"), dest=(avatar_size * i * 2, 0))   # Attach avatar
            if i != 0:
                image.alpha_composite(heart, dest=(avatar_size * (i * 2 - 1), 0))                 # Attach heart
        ship_image = BytesIO()
        image.save(ship_image, format="PNG")
        ship_image.seek(0)
        await ctx.send(f"Your ship's name is **{ship_name}!** {self.ona.config.heart_eyes}",
                       file=discord.File(ship_image, f"{ctx.message.id}.png"))

    async def edit_image(self, url, get_edited, get_data=None):
        '''Abstract the image editing process. get_edited takes an image/frame and returns a new image.
        Data returned by get_data will also be passed to get_edited. This way, gifs will have minimal
        calculations happening per frame.'''
        new_image = BytesIO()
        with Image.open(BytesIO(await self.ona.request(url))) as image:
            data = get_data(image) if get_data else None
            if ".gif" in url:
                image_iter = ImageSequence.Iterator(image)
                first = get_edited(next(image_iter), data)
                first.info = image.info
                frames = [get_edited(frame, data) for frame in image_iter]
                first.save(new_image, format="GIF", save_all=True, append_images=frames, optimize=True, loop=0)
            else:
                get_edited(image, data).save(new_image, format="PNG")
        new_image.seek(0)
        return discord.File(new_image, self.ona.filename_from_url(url))

    @commands.command(aliases=["size", "scale"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def resize(self, ctx, magnification: Optional[float]):
        '''Resize an image.
        The magnification value can be any value, including a decimal.'''
        try:
            magnification = magnification or float(await ctx.ask("Give a value to resize the image by:"))
        except ValueError:
            raise self.ona.OnaError("Not a valid magnification value.")

        def get_resized(image, data):
            new_size = (int(image.width * magnification), int(image.height * magnification))
            max_size = 5000
            self.ona.assert_(new_size[0] < max_size, new_size[1] < max_size, error="This image is too large.")
            return image.resize(new_size, Image.LANCZOS)

        await ctx.send(file=await self.edit_image(await ctx.get_last_url(), get_resized))

    @commands.command(aliases=["spin"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def rotate(self, ctx, degrees: Optional[int]):
        '''Rotate an image by any number of degrees.'''
        try:
            degrees = degrees or int(await ctx.ask("Give a value to rotate the image by:"))
        except ValueError:
            raise self.ona.OnaError("Not a valid rotation value.")

        resample = Image.BICUBIC
        await ctx.send(file=await self.edit_image(await ctx.get_last_url(),
                                                  lambda image, data: image.rotate(degrees, resample=resample)))

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def filter(self, ctx, filter="blur"):
        '''Apply a filter to an image.
        The available filters are: blur, contour, detail, edge_enhance, edge_enhance_more, emboss,
        find_edges, sharpen, smooth, and smooth_more.'''
        filter = filter or await ctx.ask("Give a filter to apply:")
        try:
            filter = getattr(ImageFilter, filter.upper())
        except AttributeError:
            raise self.ona.OnaError((f"That filter isn't recognized."
                                     f"Use `{ctx.prefix}help filter` to see all filters."))
        await ctx.send(file=await self.edit_image(await ctx.get_last_url(),
                                                  lambda image, data: image.convert("RGBA").filter(filter)))

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def invert(self, ctx):
        '''Invert an image.'''
        await ctx.send(file=await self.edit_image(await ctx.get_last_url(),
                                                  lambda image, data: ImageOps.invert(image.convert("RGB"))))

    @commands.command(aliases=["caption"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def meme(self, ctx, *, caption: commands.clean_content = None):
        '''Make a meme using any image and a caption.
        Separate top from bottom text using the " | " character.'''
        caption = caption or await ctx.ask("Provide a caption for the image:")
        url = await ctx.get_last_url()
        caption = caption.replace(url, "")      # If the url is in the command, remove it

        def get_caption_data(image):
            top, bottom = {}, {}
            top["text"], bottom["text"] = caption.upper().split("|") if "|" in caption else (caption.upper(), "")
            top["text"], bottom["text"] = top["text"].strip(), bottom["text"].strip()

            def get_text_info(text):    # Returns font, outline thickness, and x position
                if not text:
                    return ImageFont.load_default(), 1, 1
                size = 2
                while True:
                    font = ImageFont.truetype(self.ona.resources["impact"], size=size)
                    size += 2
                    font_width, font_height = font.getsize(text)
                    if font_width > image.width - 20 or font_height > image.height / 5:
                        return font, font_height // 20 + 1, (image.width - font_width) // 2

            top["font"], top["thickness"], top["x"] = *get_text_info(top["text"]),
            bottom["font"], bottom["thickness"], bottom["x"] = *get_text_info(bottom["text"]),
            top["pos"] = (top["x"], 5)
            bottom["pos"] = (bottom["x"], image.height - bottom["font"].getsize(bottom["text"])[1] - 10)
            return top, bottom

        def draw_outlined_text(draw, *, pos, text, font, thickness, **_):
            outline = (0, 0, 0, 255)
            fill = (255, 255, 255, 255)
            for x in [-thickness, 0, thickness]:
                for y in [-thickness, 0, thickness]:
                    draw.text((pos[0] + x, pos[1] + y), text, fill=outline, font=font)
            draw.text(pos, text, fill=fill, font=font)

        def get_captioned(image, data):
            top, bottom = data
            image = image.convert(mode="RGBA")
            draw = ImageDraw.Draw(image)
            draw_outlined_text(draw, **top)
            draw_outlined_text(draw, **bottom)
            return image

        await ctx.send(file=await self.edit_image(url, get_captioned, get_caption_data))

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def gif(self, ctx, count: int = 10):
        '''Create a gif from the last few images in the channel.'''
        new_gif = BytesIO()
        images = [Image.open(BytesIO(await self.ona.request(url))) for url in await ctx.get_last_url(count=count)]
        new_size = max(image.size for image in images)  # Returns the size with either the largest height or width
        images = [frame.resize(new_size, Image.LANCZOS) for image in images for frame in ImageSequence.Iterator(image)]
        images[0].save(new_gif, format="GIF", save_all=True, append_images=images[1:], optimize=True, loop=0)
        new_gif.seek(0)
        await ctx.send(file=discord.File(new_gif, f"{ctx.message.id}.gif"))

    @commands.command()
    @commands.cooldown(3, 20, commands.BucketType.user)
    async def quote(self, ctx, member: discord.Member, number: Optional[int]):
        '''Bring up quotes from another member.
        To add a new quote, react to a message with 📌 if quoting is enabled in the server.'''
        member_doc = self.ona.user_db.get_doc(member)
        number = number or random.randrange(len(member_doc.quotes))
        self.ona.assert_(member_doc.quotes, error=f"{member.display_name} has no quotes added.")
        self.ona.assert_(number <= len(member_doc.quotes),
                         error=(f"{member.display_name} only has "
                                f"{self.ona.plural(len(member_doc.quotes), 'quote')}."))
        quotes = []
        for i, quote in enumerate(member_doc.quotes, 1):
            embed = self.ona.embed(quote["content"])
            embed.set_image(url=quote["attachment"]).timestamp = quote["timestamp"]
            name = f"{self.ona.ordinal(i)} quote from {member.display_name}"
            embed.set_author(name=name, icon_url=member.avatar_url)
            quotes.append(embed)
        await ctx.embed_browser(quotes, pos=number-1 or 0)

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def add_quote_listener(self, payload):
        guild = self.ona.get_guild(payload.guild_id)    # unpack the raw payload data
        if not guild:
            return
        if payload.emoji.name != "📌" or not self.ona.guild_db.get_doc(guild).quoting:
            return
        member = guild.get_member(payload.user_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.author == member:
            await channel.send(f"You can't quote yourself. {self.ona.config.error}",
                               delete_after=self.ona.config.delete_timer)
            return
        if message.id in (quote["id"] for quote in self.ona.user_db.get_doc(message.author).quotes):
            await channel.send(f"This quote has already been added. {self.ona.config.error}",
                               delete_after=self.ona.config.delete_timer)
            return
        quote = {
            "id": message.id, "timestamp": message.created_at, "content": message.content,
            "attachment": message.attachments[0].url if message.attachments else ""
        }
        with self.ona.user_db.doc_context(message.author) as quoted_member_doc:
            quoted_member_doc.quotes.append(quote)
            quote_number = len(quoted_member_doc.quotes)
        content = (f"{message.author.display_name} had their {self.ona.ordinal(quote_number)} "
                   f"quote added by {member.display_name}.")
        await channel.send(content)
        fields = [("Number", str(quote_number)), ("Channel", channel.mention)]
        embed = self.ona.embed(quote["content"], title=content, timestamp=True, author=message.author, fields=fields)
        embed.set_image(url=quote["attachment"])
        await guild.get_channel(self.ona.guild_db.get_doc(guild).logs).send(embed=embed)


def setup(ona):
    ona.add_cog(Fun(ona))
