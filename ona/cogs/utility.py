import time
import asyncio
import requests
import discord
from datetime import datetime, timedelta
from html.parser import HTMLParser
from discord.ext import commands
from ona.ona_utils import in_server


class Utility:
    '''These commands perform a variety of useful tasks.'''

    def __init__(self, ona):
        self.ona = ona

    @commands.command()
    async def ping(self, ctx):
        '''Check Ona's response time.'''
        start = time.time()
        message = await ctx.send("My ping is...")
        await asyncio.sleep(2)
        end = time.time()
        await message.edit(content=f"My ping is... **{round((end-start-2) * 1000, 2)}** milliseconds.")
        await ctx.clean_up(message)

    @commands.command()
    async def uptime(self, ctx):
        '''Check how long Ona has been running for.'''
        delta = datetime.utcnow() - self.ona.uptime
        uptime = self.ona.plural(delta.days, 'day') if delta.days else self.ona.plural(delta.seconds, 'second')
        await ctx.clean_up(await ctx.send(f"I've been running for {uptime}."))

    @commands.command(aliases=["commands"])
    async def help(self, ctx, command_name: str = None):
        '''Display help for any or all of Ona's commands.'''
        if command_name:
            command = next(cmd for cmd in self.ona.commands if command_name.lower() in [cmd.name] + cmd.aliases)
            ctx.ona_assert(command is not None, error="That is not a valid command name.")
            await ctx.send(embed=await self.ona.formatter.format_help_for(ctx, command))
        else:
            await ctx.whisper(embed=await self.ona.formatter.format_help_for(ctx, self.ona))

    @commands.command()
    @commands.check(in_server)
    async def members(self, ctx):
        '''See how many members are in the server.'''
        await ctx.send(f"We're at **{ctx.guild.member_count:,}** members! {ctx.ona.get_emoji_named('heartEyes')}")

    @commands.command(aliases=["avi", "pfp"])
    async def avatar(self, ctx, *, member: discord.Member = None):
        '''Display a user's avatar.'''
        member = member if member else ctx.author
        with self.ona.download(member.avatar_url_as(static_format="png", size=256)) as avatar_file:
            await ctx.send(f"{member.display_name}'s avatar:", file=discord.File(avatar_file))

    @commands.command(aliases=["emoji", "e"])
    async def emote(self, ctx, *, emoji: discord.Emoji):
        '''Get a fullsize image for an emote. Only works for emotes in servers Ona shares.'''
        with self.ona.download(emoji.url) as emoji_file:
            await ctx.send(file=discord.File(emoji_file))

    @commands.command(aliases=["info", "userinfo"])
    async def user(self, ctx, member: discord.Member = None):
        '''Get info about a user.'''
        member = member if member else ctx.author
        if hasattr(member, "roles"):
            roles = f"**Roles:** {', '.join(role.name for role in member.roles[1:][::-1])}"
        else:
            roles = ""
        color = member.color if member.color.value else ctx.config.ona_color
        embed = discord.Embed(title=member.display_name, description=roles, color=color)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="Global Name", value=member.name).add_field(name="ID", value=member.id)
        embed.add_field(name="Created", value=member.created_at.strftime("%b %d, %Y"))
        if hasattr(member, "joined_at"):
            embed.add_field(name="Joined", value=member.joined_at.strftime("%b %d, %Y"))
        if member.activity:
            if member.activity.type == discord.ActivityType.listening:
                embed.add_field(name="Listening to", value=member.activity.title)
            else:
                embed.add_field(name=member.activity.type.name.title(), value=member.activity.name)
        await ctx.send(embed=embed)

    @commands.command(aliases=["sauce"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def source(self, ctx, url: str = None):
        '''Reverse image search any image. Either attach an image, post its url, or use the
        most recently posted image in the channel.'''
        if ctx.message.attachments:
            url = ctx.message.attachments[0].url
        if url is None:
            message = await ctx.history().find(lambda message: len(message.attachments))
            ctx.ona_assert(message is not None, error="No image was provided.")
            url = message.attachments[0].url
        loop = asyncio.get_event_loop()
        req = await loop.run_in_executor(None, requests.post, "http://iqdb.org", {"url": url})
        ctx.ona_assert("No relevant matches" not in req.text, "HTTP request failed" not in req.text,
                       error="No results found.")
        parser = HTMLParser()
        urls = []

        # This handler parses the iqdb.org response html for all href links
        def handler(tag, attrs):
            any(urls.append(attr[1]) for attr in attrs if attr[0] == "href")
        parser.handle_starttag = handler
        parser.feed(req.text)
        url = urls[2]   # The second href is the "best match"
        if url.startswith("//"):
            url = f"https:{url}"
        await ctx.send(f"Here's the closest match:\n{url}")


def setup(ona):
    ona.add_cog(Utility(ona))
