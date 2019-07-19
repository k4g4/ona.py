import asyncio
import discord
from json import loads, JSONDecodeError
from typing import Optional
from discord.ext import commands


class Staff(commands.Cog):
    '''Helpful commands for moderation and bot maintenance.'''

    def __init__(self, ona):
        self.ona = ona
        self.r9k_message_cache = []

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        '''Kick one or more members from the server.'''
        self.ona.assert_(members, error="Give one or more members to kick.")
        await ctx.message.delete()
        for member in members:
            await ctx.guild.kick(member, reason=f"{ctx.author.name}: {reason or 'No reason provided'}")
        content = (f"{members[0].display_name} was kicked." if len(members) == 1 else
                   (f"Multiple users were kicked:\n▫ " +
                    "\n▫ ".join(member.display_name for member in members)))
        await ctx.staff_log(content, fields=[("Reason", reason)] if reason else [])

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        '''Ban one or more members from the server.'''
        self.ona.assert_(members, error="Give one or more members to kick.")
        await ctx.message.delete()
        for member in members:
            await ctx.guild.ban(member, reason=f"{ctx.author.name}: {reason or 'No reason provided'}")
        content = (f"{members[0].display_name} was banned." if len(members) == 1 else
                   (f"Multiple users were banned:\n▫ " +
                    "\n▫ ".join(member.display_name for member in members)))
        await ctx.staff_log(content, fields=[("Reason", reason)] if reason else [])

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx, members: commands.Greedy[discord.Member], minutes: Optional[int], *, reason=None):
        '''Give any number of members a Muted role.
        After the list of members, a number may be given to mute for a certain number of minutes.'''
        self.ona.assert_(members, error="Give one or more members to mute.")
        self.ona.assert_(minutes is None or 0 < minutes < self.ona.config.max_minutes,
                         error=f"The number of minutes must positive and fewer than {self.ona.config.max_minutes}")
        muted = ctx.guild.get_role(ctx.guild_doc.muted)
        self.ona.assert_(muted, error="No `Muted` role has been set in this server.")
        await ctx.message.delete()
        successes, failures = [], []
        for member in members:
            try:
                await member.add_roles(muted, reason=f"{ctx.author.name}: {reason or 'No reason provided'}")
                successes.append(member)
            except discord.HTTPException:
                failures.append(member)
        for_n_minutes = f" for {self.ona.plural(minutes, 'minute')}" if minutes else ""
        content = ""
        if successes:
            content += (f"{successes[0].display_name} was muted{for_n_minutes}." if len(members) == 1 else
                        (f"Multiple users were muted{for_n_minutes}:\n▫ " +
                         "\n▫ ".join(member.display_name for member in successes)))
        if failures:
            content += f"\n{self.ona.plural(len(failures), 'member')} could not be muted. Check the role hierarchy."
        await ctx.staff_log(content, fields=[("Reason", reason)] if reason else [])
        if not minutes or not successes:
            return
        await asyncio.sleep(minutes * 60)
        for member in successes:
            try:
                await member.remove_roles(muted)
            except discord.HTTPException:
                pass
        await ctx.staff_log("The member(s) from {self.ona.plural(minutes, 'minute')} ago have been unmuted.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        '''Remove the Muted role from any number of members.'''
        self.ona.assert_(members, error="Give one or more members to mute.")
        muted = ctx.guild.get_role(ctx.guild_doc.muted)
        self.ona.assert_(muted, error="No `Muted` role has been set in this server.")
        await ctx.message.delete()
        failures, successes = [], []
        for member in members:
            try:
                await member.remove_roles(muted, reason=reason)
                successes.append(member)
            except discord.HTTPException:
                failures.append(member)
        content = ""
        if successes:
            content += (f"{successes[0].display_name} was unmuted." if len(members) == 1 else
                        (f"Multiple users were unmuted:\n▫ " +
                         "\n▫ ".join(member.display_name for member in successes)))
        if failures:
            content += f"\n{self.ona.plural(len(failures), 'member')} could not be unmuted. Check the role hierarchy."
        await ctx.staff_log(content, fields=[("Reason", reason)] if reason else [])

    @commands.command(aliases=["silent"])
    @commands.has_permissions(manage_messages=True)
    async def silence(self, ctx, members: commands.Greedy[discord.Member], minutes: int = None):
        '''Turn on silent mode, or silence any number of members.
        Silent mode will ignore commands in channels listed on the chat_throttle list.
        A number may be given to keep silent mode off for a certain number of minutes.'''
        for_n_minutes = f" for {self.ona.plural(minutes, 'minute')}" if minutes else ""
        if members:
            for member in members:
                with ctx.member_doc_ctx(member) as member_doc:
                    member_doc.silenced.append(ctx.guild.id)
            content = (f"{members[0].display_name if len(members) == 1 else f'{len(members)} members'} "
                       f"may no longer use commands{for_n_minutes}.")
        else:
            with ctx.guild_doc_ctx() as guild_doc:
                guild_doc.silent = True
            content = f"Silent mode is now enabled. Nobody may use commands{for_n_minutes}."
        await ctx.send(content)
        await ctx.staff_log(content)
        if not minutes:
            return
        await asyncio.sleep(minutes * 60)
        if members:
            for member in members:
                with ctx.member_doc_ctx(member) as member_doc:
                    if ctx.guild.id not in member_doc.silenced:
                        continue
                    member_doc.silenced.remove(ctx.guild.id)
            content = f"The member(s) from {self.ona.plural(minutes, 'minute')} ago have been unsilenced."
        else:
            with ctx.guild_doc_ctx() as guild_doc:
                if not guild_doc.silent:    # If silent mode was disabled before now
                    return
                guild_doc.silent = False
            content = "Silent mode has been disabled. Everyone may use commands."
        await ctx.send(content)
        await ctx.staff_log(content)

    @commands.command(aliases=["unsilent"])
    @commands.has_permissions(manage_messages=True)
    async def unsilence(self, ctx, *members: discord.Member):
        '''Disable silent mode, or unsilence any number of members.'''
        if members:
            for member in members:
                with ctx.member_doc_ctx(member) as member_doc:
                    if ctx.guild.id not in member_doc.silenced:
                        continue
                    member_doc.silenced.remove(ctx.guild.id)
            content = (f"{members[0].display_name if len(members) == 1 else f'{len(members)} members'} "
                       f"may use commands again.")
        else:
            with ctx.guild_doc_ctx() as guild_doc:
                self.ona.assert_(guild_doc.silent, error="Silent mode is already disabled.")
                guild_doc.silent = False
            content = "Silent mode has been disabled. Everyone may use commands."
        await ctx.send(content)
        await ctx.staff_log(content)

    @commands.command(aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def prune(self, ctx, filter: Optional[discord.Member], count: int):
        '''Prune multiple messages from a channel.
        If a member is provided, only that member's messages are removed out of the number of messages given.'''
        self.ona.assert_(0 < count < self.ona.config.max_prune,
                         error=f"The number of messages must be positive and fewer than {self.ona.config.max_prune}.")
        await ctx.message.delete()
        pruned = await ctx.channel.purge(limit=count, check=lambda m: not filter or m.author == filter)
        content = f"Pruned {self.ona.plural(len(pruned), 'message')}."
        await ctx.send(content)
        fields = [("Channel", ctx.channel.mention)]
        if filter:
            fields.append(("Filter", filter.mention))
        await ctx.staff_log(content, fields=fields)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def r9k(self, ctx, minutes: Optional[int]):
        '''Enable or disable R9K mode in the channel.
        When enabled, R9K mode will delete long duplicate messages.'''
        with ctx.guild_doc_ctx() as guild_doc:
            if ctx.channel.id not in guild_doc.r9k:
                guild_doc.r9k.append(ctx.channel.id)
                await ctx.send(f"R9K mode has been enabled in {ctx.channel.mention}.")
            else:
                guild_doc.r9k.remove(ctx.channel.id)
                await ctx.send(f"R9K mode has been disabled in {ctx.channel.mention}.")
        await asyncio.sleep(minutes * 60)
        with ctx.guild_doc_ctx() as guild_doc:
            if ctx.channel.id in guild_doc.r9k:
                guild_doc.r9k.remove(ctx.channel.id)
                await ctx.send(f"R9K mode has been disabled in {ctx.channel.mention}.")

    @commands.Cog.listener(name="on_message")
    async def r9k_listener(self, message):
        if message.channel.id not in self.ona.guild_db.get_doc(message.guild).r9k:
            return
        if message.channel.permissions_for(message.author).administrator:
            return
        if len(message.content) < self.ona.config.min_r9k_char:
            return
        if await message.channel.history(before=message).get(content=message.content):
            await message.delete()

    @commands.command(aliases=["add_emote"])
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    async def addemote(self, ctx, name=None):
        '''Create an emote in the server with the specified name.'''
        name = name or (await ctx.ask("Give a name for the emote:")).replace(" ", "_")
        image = await self.ona.request(await ctx.get_last_url())
        try:
            emote = await ctx.guild.create_custom_emoji(name=name, image=image)
        except discord.HTTPException as e:
            raise self.ona.OnaError(f"Either the emote limit has been reached or the name '{name}' is invalid.")
        await ctx.staff_log(f"An emote was added: {emote}", fields=[("Name", emote.name)])
        await ctx.send(f"The emote has been added successfully. {emote}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        '''View all available server settings.'''
        await ctx.whisper(embed=self.ona.embed("\n".join(self.ona.guild_db.template.keys()), title="Settings"))

    @commands.command(aliases=["edit_setting"])
    @commands.has_permissions(administrator=True)
    async def editsetting(self, ctx, setting=None, value=None):
        '''Change any settings on a server.
        For a full list of settings, use the `settings` command.'''
        setting = setting or await ctx.ask("Which setting would you like to edit?")
        self.ona.assert_(setting in self.ona.guild_db.template,
                         error=f"That isn't a valid setting. Use `{ctx.guild_doc.prefix}settings` to see all settings.")
        with ctx.guild_doc_ctx() as guild_doc:
            content = f"Give the new value for `{setting}`:"
            if setting in guild_doc:
                content = f"`{setting}` is currently set to `{guild_doc[setting]}`. {content}"
            new_setting = value if value else await ctx.ask(content)
            try:
                guild_doc[setting] = loads(new_setting)
            except JSONDecodeError:
                guild_doc[setting] = new_setting
        content = f"`{setting}` is now set to `{ctx.guild_doc[setting]}`."
        await ctx.staff_log(content)
        await ctx.send(content)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unquote(self, ctx, member: discord.Member, number: int):
        '''Remove a quote from a member.'''
        with ctx.member_doc_ctx(member) as member_doc:
            member_doc.quotes.pop(number - 1)
        content = f"{member.display_name}'s {self.ona.ordinal(number)} quote has been removed."
        await ctx.send(content)
        await ctx.staff_log(content)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_guild=True)
    async def invites(self, ctx):
        '''Check invites in the server.'''
        invites = await ctx.guild.invites()
        await ctx.send(", ".join(f"{invite.inviter.name}: {invite.uses:,} uses"
                                 for invite in sorted(invites, key=lambda i: i.uses, reverse=True)[:20]
                                 if invite.uses > 0))

    @commands.command(aliases=["shutdown"])
    @commands.is_owner()
    async def close(self, ctx):
        '''Completely shut down Ona.'''
        if await ctx.prompt("Are you sure you'd like me to shut down?"):
            await ctx.send("Shutting down...")
            await self.ona.wait_until_ready()
            await self.ona.close()
        else:
            await ctx.send("Shutdown aborted.")

    @commands.command(aliases=["editavi", "edit_avatar", "edit_avi"])
    @commands.is_owner()
    async def editavatar(self, ctx):
        '''Change Ona's avatar.'''
        await self.ona.user.edit(avatar=await self.ona.request(await ctx.get_last_url()))
        content = "My avatar has been updated."
        await ctx.staff_log(content)
        await ctx.send(content)

    @commands.command(name="eval")
    @commands.is_owner()
    async def _eval(self, ctx, *, expression):
        '''Evaluate any Python expression.'''
        try:
            await ctx.send(eval(expression))
        except Exception as e:
            raise self.ona.OnaError(f"{type(e).__name__}: {e}")

    @commands.command(aliases=["edit_money"])
    @commands.is_owner()
    async def editmoney(self, ctx, member: discord.Member, money: int):
        '''Give or remove money from a user.'''
        with ctx.member_doc_ctx(member) as member_doc:
            member_doc.money += money
        content = f"{member.display_name} {'gained' if money >= 0 else 'lost'} {abs(money)} {ctx.guild_doc.currency}."
        await ctx.staff_log(content)
        await ctx.send(content)


def setup(ona):
    ona.add_cog(Staff(ona))
