from aiohttp import ClientSession
import discord
from contextlib import contextmanager
from datetime import timedelta, datetime
from discord.ext import commands


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
        embed = discord.Embed(description=str(content), title=title, color=self.config.ona_color)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if timestamp:
            embed.timestamp = datetime.utcnow()
        if author:
            embed.set_author(name=author.display_name, icon_url=author.avatar_url)
        for field in fields:
            embed.add_field(name=field[0], value=field[1])
        return embed

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

    @staticmethod
    def plural(value, word):
        value = int(value) if float(value).is_integer() else value  # Remove .0 if it exists
        return f"one {word}" if value == 1 else f"{value:,} {word}s"

    @staticmethod
    def filename_from_url(url):
        return url.split("/")[-1].split("?")[0]

    @staticmethod
    def ordinal(n):
        return str(n) + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th") if n % 100 < 10 or 20 < n % 100 else "th"


# Various command checks

def not_blacklisted(ctx):
    return ctx.ona.assert_(ctx.channel.id not in ctx.guild_doc.blacklist,
                           error="Commands have been disabled in this channel.")


def not_silenced(ctx):
    if ctx.channel.id not in ctx.guild_doc.chat_throttle:
        return True
    ctx.ona.assert_(not ctx.guild or ctx.author.id not in ctx.guild_doc.silenced,
                    error="You've been silenced. Try another channel instead.")
    return ctx.ona.assert_(not ctx.guild or not ctx.guild_doc.silent,
                           error="Silent mode is currently enabled. Try again later!")


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
