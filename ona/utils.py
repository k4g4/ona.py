import os
import requests
import discord
from contextlib import contextmanager
from datetime import timedelta, datetime
from json import loads
from discord.ext import commands


class OnaUtilsMixin:
    '''Various bot utilities are kept in this class.'''

    # All errors that are displayed to the user instead of being logged
    class OnaError(commands.CommandError):
        pass

    def get(self, iterable, **attrs):
        return discord.utils.get(iterable, **attrs)

    def quick_embed(self, content="", *, title=None, url=None, author=None, fields=[]):
        '''An embed factory method.'''
        embed = discord.Embed(description=content, title=title, url=url, color=self.config.ona_color)
        if author:
            embed.set_author(name=author.display_name, icon_url=author.avatar_url)
        for field in fields:
            embed.add_field(name=field[0], value=field[1])
        return embed

    def search(self, query, image=False):
        '''Search Google with a query. Retrieve image results if image=True.'''
        params = {"q": query, "key": self.secrets.google_key, "cx": self.secrets.google_engine_id}
        if image:
            params["searchType"] = "image"
        return loads(requests.get("https://www.googleapis.com/customsearch/v1", params=params).text)["items"]

    @staticmethod
    def plural(value, word):
        value = int(value) if float(value).is_integer() else value  # Remove .0 if it exists
        return f"one {word}" if value == 1 else f"{value:,} {word}s"

    @staticmethod
    @contextmanager
    def download(url):
        '''This helper coroutine downloads a file from a url and yields it to a context manager,
        then deletes the file once the context manager exits.'''
        filename = os.path.split(url)[1].partition("size")[0]
        req = requests.get(url, headers={"User-Agent": "Ona Agent"})
        with open(filename, 'wb') as fd:
            for chunk in req.iter_content(chunk_size=128):
                fd.write(chunk)
        try:
            yield filename
        finally:
            os.remove(filename)

    async def log(self, content):
        print(content)
        logs = self.get_guild(self.config.server).get_channel(self.config.logs)
        await logs.send(embed=self.quick_embed(content, title="OnaLogger"))


# Various command checks

def is_owner(ctx):
    return ctx.ona.is_owner(ctx.author)


def in_server(ctx):
    return ctx.ona_assert(ctx.guild, error="You need to be in a server to use this command.")


def not_blacklisted(ctx):
    return ctx.ona_assert(ctx.channel.id not in ctx.config.blacklist,
                          error="Commands have been disabled in this channel.")


def not_silenced(ctx):
    if ctx.channel.id not in ctx.config.chat_throttle:
        return True
    ctx.ona_assert(not ctx.guild or not ctx.has_role(ctx.config.silenced),
                   error="You've been silenced. Use a bot channel instead.")
    return ctx.ona_assert(not ctx.guild or all(role.id != ctx.config.silenced for role in ctx.guild.me.roles),
                          error="I'm on silent mode. Try again later!")


# This check ignores all channels not on the image_throttle list
async def image_throttle(ctx):
    if ctx.message.id not in ctx.config.image_throttle:
        return True
    # OnaError if there are too many images in the channel
    last_ten = await ctx.history(limit=10).flatten()
    return ctx.ona_assert(sum(len(message.attachments) for message in last_ten) > 2,
                          error="There are too many images here. Try again later!")


# This check ignores all channels not on the chat_throttle list
async def chat_throttle(ctx):
    if ctx.channel.id not in ctx.config.chat_throttle:
        return True
    # OnaError if the 10th oldest message is <40 seconds old
    async for message in ctx.history(limit=10):
        oldest = message
    return ctx.ona_assert(oldest.timestamp + timedelta(0, 40) > datetime.utcnow(),
                          error="The chat is too active. Try again later!")
