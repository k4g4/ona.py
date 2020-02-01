import asyncio
import discord
from discord.ext import commands

event = commands.Cog.listener


class Events(commands.Cog):
    '''Event coroutines are kept in this class to reduce clutter.'''

    def __init__(self, ona):
        self.ona = ona

    @event()
    async def on_ready(self):
        content = "Ona has logged in."
        print(content)
        embed = self.ona.embed(content, timestamp=True, author=self.ona.user)
        main_guild = self.ona.get_guild(self.ona.config.main_guild)
        await main_guild.get_channel(self.ona.guild_db.get_doc(main_guild).logs).send(embed=embed)

    @event()
    async def on_message(self, message):
        if message.author.bot:
            return
        ctx = await self.ona.process_commands(message)

    @event()
    async def on_message_edit(self, initial, message):
        if message.author.bot:
            return
        await self.ona.process_commands(message)
        if not message.guild:     # Assume we're in a guild after this point
            return
        logs = self.ona.guild_db.get_doc(message.guild).logs
        if not logs:     # Do nothing when a guild has no logs setting specified
            return
        fields = [("Before", initial.content), ("After", message.content), ("Channel", message.channel.mention)]
        embed = self.ona.embed(title="Message was edited", timestamp=True, author=message.author, fields=fields)
        await message.guild.get_channel(logs).send(embed=embed)

    @event()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        if not message.guild:   # Assume we're in a guild after this point
            return
        logs = self.ona.guild_db.get_doc(message.guild).logs
        if not logs:     # Do nothing when a guild has no logs setting specified, or in a PrivateChannel
            return
        embed = self.ona.embed(message.content, title="Message was deleted", timestamp=True, author=message.author)
        if message.attachments:
            embed.set_image(url=message.attachments[0].proxy_url)
            embed.add_field(name="Filename", value=message.attachments[0].filename)
        await message.guild.get_channel(logs).send(embed=embed)

    @event()
    async def on_member_join(self, member):
        guild_doc = self.ona.guild_db.get_doc(member.guild)
        general = member.guild.get_channel(guild_doc.general)
        try:
            welcome_image = await self.ona.create_welcome(member)
            await general.send(f"Welcome to Tenshi Paradise, {member.mention} <a:stockingBlush:649595125307015200>\n",
                               file=discord.File(welcome_image, f"{member.id}_{member.guild.member_count}.png"))
        except Exception as e:
            print(e)
            await general.send(f"Welcome to Tenshi Paradise, {member.mention} <a:stockingBlush:649595125307015200>\n")
        finally:
            await member.add_roles(discord.Object(393973228818661378))

    @event()
    async def on_member_update(self, initial, member):
        if initial.roles == member.roles:
            return
        with self.ona.user_db.doc_context(member) as member_doc:
            member_doc.roles[str(member.guild.id)] = [role.id for role in member.roles[1:]]  # First role is @everyone

    @event()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance(error, commands.CommandOnCooldown):
            cooldown = round(error.retry_after) + 1
            error_text = f"This command is on cooldown for {self.ona.plural(cooldown, 'second')}."
        elif isinstance(error, commands.MissingPermissions):
            if ctx.guild:
                error_text = f"You need the `{error.missing_perms[0].title()}` permission."
            else:
                error_text = "You need to be in a server to use this command."
        elif isinstance(error, commands.BotMissingPermissions):
            if ctx.guild:
                error_text = f"I need the `{error.missing_perms[0].title()}` permission to do that."
            else:
                error_text = "You need to be in a server to use this command."
        elif isinstance(error, commands.NoPrivateMessage):
            error_text = "You need to be in a server to use this command."
        elif isinstance(error, commands.CheckFailure):
            error_text = "You don't have permission to do that!"
        elif isinstance(error, self.ona.OnaError):
            error_text = str(error)
        else:
            error_text = f"{type(error).__name__}: {error} "
            if hasattr(error.__traceback__, "tb_next"):
                error_text += f"(line #{error.__traceback__.tb_next.tb_lineno})"
            print(error_text)
            embed = self.ona.embed(error_text, timestamp=True, author=self.ona.user)
            main_guild = self.ona.get_guild(self.ona.config.main_guild)
            await (await self.ona.fetch_channel(self.ona.guild_db.get_doc(main_guild).logs)).send(embed=embed)
            return
        await ctx.clean_up(await ctx.send(f"{error_text} {self.ona.config.error}"))

    @event()
    async def on_error(self, error):
        error_text = f"{type(error).__name__}: {error} (line #{error.__traceback__.tb_next.tb_lineno})"
        print(error_text)
        embed = self.ona.embed(error_text, timestamp=True, author=self.ona.user)
        main_guild = self.ona.get_guild(self.ona.config.main_guild)
        await main_guild.get_channel(self.ona.guild_db.get_doc(main_guild).logs).send(embed=embed)


def setup(ona):
    ona.add_cog(Events(ona))
