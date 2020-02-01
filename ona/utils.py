import os
import random
import itertools
import discord
from aiohttp import ClientSession
from contextlib import contextmanager
from datetime import timedelta, datetime
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


class OnaUtilsMixin:
    '''Various bot utilities are kept in this class.'''

    # All errors that are displayed to the user instead of being logged
    class OnaError(commands.CommandError):
        pass

    def assert_(self, *assertions, error):
        '''Assert that all provided assertions are True. If one is False, raise an OnaError.'''
        if not all(assertions):
            raise self.OnaError(error)
        return True

    def get(self, iterable, **attrs):
        return discord.utils.get(iterable, **attrs)

    def embed(self, content="", *, title=None, timestamp=False, thumbnail=None, author=None, fields=[]):
        '''An embed factory method.'''
        embed = discord.Embed(description=str(content), title=title, color=int(self.config.ona_color, 16))
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if timestamp:
            embed.timestamp = datetime.utcnow()
        if author:
            embed.set_author(name=author.display_name, icon_url=author.avatar_url)
        for field in fields:
            embed.add_field(name=field[0], value=field[1])
        return embed

    async def create_welcome(self, member):
        '''Creates a welcome banner for the given member.'''
        welcome = Image.open(os.path.join(self.resources["welcomes"],
                             random.choice(os.listdir(self.resources["welcomes"]))))
        avi = Image.open(BytesIO(await member.avatar_url_as(static_format="png", size=64).read()))
        draw = ImageDraw.Draw(welcome)
        member_name = self.asciify(member.name)
        member_name = f"{member_name[:12]}..." if len(member_name) > 32 else member_name
        top_text = f"Welcome,\n{member_name}"
        bot_text = f"You're our {self.ordinal(member.guild.member_count)} member!"
        top_font_size, bot_font_size = 80, 55
        top_font = ImageFont.truetype(self.resources["tenshi_font"], top_font_size)
        bot_font = ImageFont.truetype(self.resources["tenshi_font"], bot_font_size)
        text_size = draw.multiline_textsize(top_text, font=top_font)[0] // 2
        top_text_x, top_text_y = 670, 170
        bot_text_x, bot_text_y = 375, 350
        top_outline, bot_outline = 2, 2
        white = (255, 255, 255, 255)
        blue = (15, 90, 170, 255)
        for x_offset, y_offset in itertools.product((-2, 2), (-2, 2)):      # Draw the outline around the text
            draw.multiline_text((top_text_x - text_size + x_offset, top_text_y + y_offset), top_text,
                                align="center", font=top_font, fill=white)
            draw.multiline_text((bot_text_x + x_offset, bot_text_y + y_offset), bot_text,
                                align="center", font=bot_font, fill=white)
        draw.multiline_text((top_text_x - text_size, top_text_y), top_text, # Draw the top text and bottom text
                            align="center", font=top_font, fill=blue)
        draw.multiline_text((bot_text_x, bot_text_y), bot_text,
                            align="center", font=bot_font, fill=blue)
        size = 165
        avi = avi.resize((size, size))
        circle = Image.new("L", (size, size), 0)
        ImageDraw.Draw(circle).ellipse((0, 0, size, size), fill=255)
        avi.putalpha(circle)
        welcome.alpha_composite(avi, (20, 150))
        welcome_image = BytesIO()
        welcome.save(welcome_image, format="PNG")
        welcome_image.seek(0)
        return welcome_image

    async def request(self, url, *, method="GET", **kwargs):
        '''This helper coroutine makes a request to a url.
        If the request returns JSON, this coroutine returns a dict. Otherwise, it returns a bytes object.'''
        async with ClientSession(headers={"User-Agent": "Ona Agent"}) as session:
            async with session.request(method, url, **kwargs) as result:
                self.assert_(200 <= result.status < 300,
                             error="An error occurred while connecting to the server. Try again!")
                return await result.json() if result.content_type == "application/json" else await result.read()

    async def google_search(self, query, image=False):
        '''Search Google with a query. Retrieve image results if image=True.'''
        params = {"q": query, "key": self.secrets.google_key, "cx": self.secrets.google_engine_id}
        if image:
            params["searchType"] = "image"
        return (await self.request("https://www.googleapis.com/customsearch/v1", params=params))["items"]

    async def send_webhook(self, channel, content=None, *, username=None, avatar_url=None, file=None, embed=None):
        '''Abstract the use of webhooks for a TextChannel. If Ona doesn't have the manage_webhooks permission,
        the message will be sent normally instead.'''
        if isinstance(channel, discord.TextChannel) and channel.permissions_for(channel.guild.me).manage_webhooks:
            webhooks = await channel.webhooks()
            if not webhooks:
                webhooks.append(await channel.create_webhook(name="Ona Webhook"))
            await webhooks[0].send(self.sanitize(content), username=username or channel.guild.me.display_name,
                                   avatar_url=avatar_url or self.user.avatar_url, file=file, embed=embed)
        else:
            await channel.send(self.sanitize(content), file=file, embed=embed)

    @staticmethod
    def plural(value, word):
        value = int(value) if float(value).is_integer() else value  # Remove .0 if it exists
        return f"1 {word}" if abs(value) == 1 else f"{value:,} {word}s"

    @staticmethod
    def filename_from_url(url):
        return url.split("/")[-1].split("?")[0]

    @staticmethod
    def ordinal(n):
        return f"{n:,}" + ({1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th") if n % 100 < 10 or 20 < n % 100 else "th")

    @staticmethod
    def sanitize(s):
        return s.replace("@everyone", "everyone").replace("@here", "here") if s else None

    @staticmethod
    def asciify(s):
        return "".join(c if ord(c) < 128 else "-" for c in s)


# Various command checks

def not_blacklisted(ctx):
    return ctx.ona.assert_(ctx.channel.id not in ctx.guild_doc.blacklist,
                           error="Commands have been disabled in this channel.")


def not_silenced(ctx):
    if ctx.channel.permissions_for(ctx.author).manage_messages:
        return True
    ctx.ona.assert_(not ctx.guild or ctx.guild.id not in ctx.author_doc.silenced,
                    error="You've been silenced in this server.")
    if ctx.channel.id not in ctx.guild_doc.chat_throttle:
        return True
    return ctx.ona.assert_(not ctx.guild or not ctx.guild_doc.silent,
                           error="Silent mode is currently enabled. Try another channel instead.")


# This check ignores all channels not on the image_throttle list
async def image_throttle(ctx):
    if ctx.message.id not in ctx.guild_doc.image_throttle:
        return True
    # OnaError if there are too many images in the channel
    last_ten = await ctx.history(limit=10).flatten()
    return ctx.ona.assert_(sum(len(message.attachments) for message in last_ten) > 2,
                           error="There are too many images here. Try again later!")


# This check ignores all channels not on the chat_throttle list
async def chat_throttle(ctx):
    if ctx.channel.id not in ctx.guild_doc.chat_throttle:
        return True
    # OnaError if the 10th oldest message is <40 seconds old
    async for message in ctx.history(limit=10):
        oldest = message
    return ctx.ona.assert_(oldest.timestamp + timedelta(0, 40) > datetime.utcnow(),
                           error="The chat is too active. Try again later!")
