import asyncio
import discord
from discord.ext import commands

char_limit = 2000


class OnaContext(commands.Context):
    '''Custom Context class with some quality of life attributes.'''

    @property
    def ona(self):
        return self.bot

    @property
    def config(self):
        # TODO: make the config vary based on which server the ctx is in
        return self.bot.config

    def get_role_named(self, name):
        '''Return a role in the context's guild if it exists, otherwise None.'''
        if self.guild:
            return self.ona.get(self.guild.roles, name=name)

    def has_role(self, role_id):
        return any(role.id == role_id for role in ctx.author.roles)

    def has_any_role(self, role_ids):
        return any(role.id in role_ids for role in ctx.author.roles)

    async def send(self, content="", *, multi=False, file_url=None, **kwargs):
        '''This custom send method adds the ability to send messages larger than the
        Discord character limit.'''
        if multi:
            while len(content) > char_limit:
                await super().send(content[:char_limit])
                content = content[char_limit:]
        if file_url:
            kwargs["file"] = discord.File(file_url)
        return await super().send(content, **kwargs)

    async def yes_or_no(self, *args, **kwargs):
        '''Ask the user a True or False question and return the resulting bool.'''
        message = await self.send(*args, **kwargs)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(r, u):
            return r.message.id == message.id and u == self.author and r.emoji in "✅❌"
        try:
            timeout = self.config.response_timeout
            reaction, _ = await self.ona.wait_for("reaction_add", timeout=timeout, check=check)
        except asyncio.TimeoutError:
            raise self.ona.OnaError("You took too long to react with ✅ or ❌.")
        finally:
            await message.delete()
        return reaction.emoji == "✅"

    async def ask(self, content="", options=[], *, use_embed=False, embed=None, **kwargs):
        '''Ask the user for a response from a list of options and return the position of the chosen option.
        If no option list is provided, return any response from the user as a string.'''
        if embed:
            embed.description = embed.description if embed.description else ""
        for i, option in enumerate(options, 1):
            row = f"\n:white_small_square: {i}) {option}"
            if use_embed:
                embed.description += row
            else:
                content += row
        message = await self.send(content, embed=embed, **kwargs)

        def check(m):
            if m.author != self.author:
                return False
            return not options or m.content.isdigit() and int(m.content) <= len(options)
        try:
            timeout = self.config.response_timeout
            response = await self.ona.wait_for("message", timeout=timeout, check=check)
        except asyncio.TimeoutError:
            raise self.ona.OnaError("You took too long to respond.")
        finally:
            if isinstance(self.channel, discord.TextChannel):
                if self.channel.permissions_for(self.me).manage_messages:
                    await self.channel.delete_messages([message, response])
        if options:
            return int(response.content) - 1    # The returned value is an index of the options list
        return response.content     # No options were provided

    async def embed_browser(self, embeds, pos=0):
        '''Send a list of embeds to display each one along with reaction based controls to navigate through
        them. The start parameter decides which embed should be shown first.'''
        self.ona_assert(isinstance(self.channel, discord.TextChannel),
                        self.channel.permissions_for(self.me).manage_messages,
                        error="I need the `Manage Messages` permission to do that.")
        # Add page numbers to each embed
        for i, embed in enumerate(embeds, 1):
            embed.set_footer(text=f"Page {i} of {len(embeds)}")
        message = await self.send(embed=embeds[pos])
        await message.add_reaction("⬅")
        await message.add_reaction("➡")

        def check(r, u):
            return r.message.id == message.id and not u.bot and r.emoji in "⬅➡"
        while True:
            try:
                timeout = self.config.response_timeout
                reaction, user = await self.ona.wait_for("reaction_add", timeout=timeout, check=check)
            except asyncio.TimeoutError:
                break
            await message.remove_reaction(reaction.emoji, user)
            if user == self.author:
                # increment or decrement the position according to the reaction, unless at either end of the list
                pos += 1 if reaction.emoji == "➡" and pos < len(embeds) - 1 else 0
                pos -= 1 if reaction.emoji == "⬅" and pos > 0 else 0
                await message.edit(embed=embeds[pos])
        await message.clear_reactions()
        return message

    async def clean_up(self, *messages):
        '''When done with a command, call clean_up with an argument-list of messages to delete them all
        as well as the initial command message if Ona has permission.'''
        if not isinstance(self.channel, discord.TextChannel):
            return
        if self.channel.permissions_for(self.me).manage_messages:
            messages += (self.message,)
        await asyncio.sleep(self.config.delete_timer)
        await self.channel.delete_messages(messages)

    async def whisper(self, *args, **kwargs):
        """DM a user instead of sending a message to the chat."""
        message = await self.author.send(*args, **kwargs)
        if isinstance(self.channel, discord.TextChannel):
            await self.clean_up(await self.send(f"{self.author.mention} Check your DM!"))
        return message

    def ona_assert(self, *assertions, error):
        '''Assert that all provided assertions are True. If one is False, raise an OnaError.'''
        if not all(assertions):
            raise self.ona.OnaError(error)
        return True

    async def handle_file_url(self, url):
        '''For commands that require a file url, Ona first checks if the user attached a file.
        If no file was attached and no file url was given, Ona searches chat history for
        the most recent file attachment.'''
        if self.message.attachments:
            return self.message.attachments[0].url
        if url:
            return url
        message = await self.history().find(lambda m: len(m.attachments))
        self.ona_assert(message is not None, error="No image was provided.")
        return message.attachments[0].url
