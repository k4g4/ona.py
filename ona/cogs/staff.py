from discord.ext import commands
from ona.ona_utils import is_staff, is_admin, is_owner


class Staff:
    '''Helpful commands for moderation and bot maintenance.'''

    def __init__(self, ona):
        self.ona = ona

    def cog_check(self, ctx):
        return is_staff(ctx)

    @commands.command()
    async def kick(self, ctx, *members: discord.Member):
        '''Kick one or more members from the server.'''
        ctx.ona_assert(members, error="Give one or more members to kick.")
        await ctx.message.delete()
        for member in members:
            await ctx.guild.kick(member)
        if len(members) == 1:
            content = f"{members[0].display_name} was kicked by {ctx.author.display_name}."
        else:
            content = (f"{ctx.author.display_name} kicked multiple users:\n▫ " +
                       "\n▫ ".join(member.display_name for member in members))
        staff_logs = ctx.guild.get_channel(ctx.config.staff_logs)
        await staff_logs.send(embed=self.ona.quick_embed(content, title="Staff Logs"))

    @commands.command()
    async def ban(self, ctx, *members: discord.Member):
        '''Ban one or more members from the server.'''
        ctx.ona_assert(members, error="Give one or more members to kick.")
        await ctx.message.delete()
        for member in members:
            await ctx.guild.ban(member)
        if len(members) == 1:
            content = f"{members[0].display_name} was banned by {ctx.author.display_name}."
        else:
            content = (f"{ctx.author.display_name} banned multiple users:\n▫ " +
                       "\n▫ ".join(member.display_name for member in members))
        staff_logs = ctx.guild.get_channel(ctx.config.staff_logs)
        await staff_logs.send(embed=self.ona.quick_embed(content, title="Staff Logs"))

    @commands.command(aliases=['purge'])
    async def prune(self, ctx, count: int, member_filter: discord.Member = None):
        '''Prune multiple messages from the channel with an optional member filter.
        If the member filter is provided, only that member's messages are removed out of the number of
        messages given.'''
        ctx.ona_assert(count > ctx.config.max_prune,
                       error="You can only prune up to {ctx.config.max_prune} messages at a time.")
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=count, check=lambda m: filter and m.author == filter)
        embed = self.ona.quick_embed(f"{len(deleted)} messages were pruned.", title="Staff Logs")
        await ctx.clean_up(await ctx.send(embed=embed))
        embed.add_field(name="Channel", value=ctx.channel.mention)
        await ctx.guild.get_channel(ctx.config.staff_logs).send(embed=embed)

    @commands.command(aliases=["shutdown"])
    @commands.check(is_owner)
    async def close(self, ctx):
        '''Completely shut down Ona.'''
        if await ctx.yes_or_no("Are you sure you'd like me to shut down?"):
            await ctx.send("Shutting down...")
            await self.ona.wait_until_ready()
            await self.ona.close()
        else:
            await ctx.send("Shutdown aborted.")

    @commands.command(pass_context=True, aliases=['changeavi'])
    @commands.check(is_owner)
    async def changeavatar(self, ctx, url: str = None):
        with self.ona.download(await ctx.handle_file_url(url)) as filename, open(filename, 'b') as avatar:
            await self.ona.user.edit(avatar=avatar)
        await ctx.send("My avatar has been updated.")

    @commands.command()
    @commands.check(is_owner)
    async def eval(self, ctx, *expression: str):
        '''Evaluate any Python expression.'''
        try:
            await ctx.send(str(eval(" ".join(expression))))
        except Exception as e:
            raise self.ona.OnaError(f"Error during eval: {e}")


def setup(ona):
    ona.add_cog(Staff(ona))
