import time
import asyncio
import discord
from datetime import datetime, timedelta
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
        uptime = self.ona.plural('day', delta.days) if delta.days else self.ona.plural('second', delta.seconds)
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
        with self.ona.download(member.avatar_url_as(static_format="png", size=256)) as avatar:
            await ctx.send(f"{member.display_name}'s avatar:", file=discord.File(avatar))


def setup(ona):
    ona.add_cog(Utility(ona))
