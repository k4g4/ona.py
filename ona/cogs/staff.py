import discord
from json import loads, JSONDecodeError
from discord.ext import commands
from ona.utils import is_owner


class Staff(commands.Cog):
    '''Helpful commands for moderation and bot maintenance.'''

    def __init__(self, ona):
        self.ona = ona

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, *members: discord.Member):
        '''Kick one or more members from the server.'''
        ctx.check_perm("kick_members")
        ctx.ona_assert(members, error="Give one or more members to kick.")
        await ctx.message.delete()
        for member in members:
            await ctx.guild.kick(member)
        if len(members) == 1:
            content = f"{members[0].display_name} was kicked by {ctx.author.display_name}."
        else:
            content = (f"{ctx.author.display_name} kicked multiple users:\n▫ " +
                       "\n▫ ".join(member.display_name for member in members))
        await self.ona.staff_log(ctx.guild, content)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, *members: discord.Member):
        '''Ban one or more members from the server.'''
        ctx.check_perm("ban_members")
        ctx.ona_assert(members, error="Give one or more members to kick.")
        await ctx.message.delete()
        for member in members:
            await ctx.guild.ban(member)
        if len(members) == 1:
            content = f"{members[0].display_name} was banned by {ctx.author.display_name}."
        else:
            content = (f"{ctx.author.display_name} banned multiple users:\n▫ " +
                       "\n▫ ".join(member.display_name for member in members))
        await self.ona.staff_log(ctx.guild, content)

    @commands.command(aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def prune(self, ctx, count: int, filter: discord.Member = None):
        '''Prune multiple messages from the channel with an optional member filter.
        If the member filter is provided, only that member's messages are removed out of the number of
        messages given.'''
        ctx.check_perm("manage_messages")
        ctx.ona_assert(count < ctx.guild_doc.max_prune,
                       error=f"You can only prune up to {ctx.guild_doc.max_prune} messages at a time.")
        ctx.message.delete()
        pruned = await ctx.channel.purge(limit=count, check=lambda m: not filter or m.author == filter)
        await self.ona.staff_log(f"Pruned {self.ona.plural(len(pruned), 'message')}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        '''View all available server settings.'''
        await ctx.whisper(embed=self.ona.quick_embed("\n".join(self.ona.guild_db.template.keys()), title="Settings"))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def editsetting(self, ctx, setting: str = None, value: str = None):
        '''Change any settings on a server. For a full list of settings, use the `settings` command.'''
        setting = setting if setting else await ctx.ask("Which setting would you like to edit?")
        ctx.ona_assert(setting in self.ona.guild_db.template,
                       error="That isn't a valid setting. Use `{ctx.guild_doc.prefix}settings` to see all settings.")
        with ctx.guild_doc_ctx() as guild_doc:
            content = f"Give the new value for `{setting}`:"
            if setting in guild_doc:
                content = f"`{setting}` is currently set to `{guild_doc[setting]}`. {content}"
            new_setting = value if value else await ctx.ask(content)
            try:
                guild_doc[setting] = loads(new_setting)
            except JSONDecodeError:
                guild_doc[setting] = new_setting
        await ctx.staff_log(f"`{setting}` is now set to `{ctx.guild_doc[setting]}`.")

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

    @commands.command(pass_context=True, aliases=['editavi'])
    @commands.check(is_owner)
    async def editavatar(self, ctx, url: str = None):
        '''Attach an image to change Ona's avatar.'''
        with self.ona.download(await ctx.handle_file_url(url)) as filename, open(filename, 'b') as avatar:
            await self.ona.user.edit(avatar=avatar)
        await ctx.send("My avatar has been updated.")

    @commands.command()
    @commands.check(is_owner)
    async def eval(self, ctx, *, expression: str):
        '''Evaluate any Python expression.'''
        try:
            await ctx.send(eval(expression))
        except Exception as e:
            raise self.ona.OnaError(f"Error during eval: {e}")

    @commands.command()
    @commands.check(is_owner)
    async def hack(self, ctx, member: discord.Member, money: int):
        '''Give or remove money from a user.'''
        with ctx.member_doc_ctx(member) as member_doc:
            member_doc.money += money
        await ctx.staff_log((f"{member.display_name} {'gained' if money >= 0 else 'lost'} "
                             f"{money} {ctx.guild_doc.currency}."))


def setup(ona):
    ona.add_cog(Staff(ona))
