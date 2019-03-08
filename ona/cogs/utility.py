import time
import asyncio
import discord
from json import loads
from os import path
from io import BytesIO
from datetime import datetime, timedelta
from html.parser import HTMLParser
from discord.ext import commands
from ona.utils import in_guild


class Utility(commands.Cog):
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
            try:
                command = next(cmd for cmd in self.ona.commands if command_name.lower() in [cmd.name] + cmd.aliases)
            except StopIteration:
                raise self.ona.OnaError("That is not a valid command name.")
            await ctx.send(embed=await self.ona.formatter.format_help_for(ctx, command))
        else:
            await ctx.whisper(embed=await self.ona.formatter.format_help_for(ctx, self.ona))

    @commands.command()
    @commands.check(in_guild)
    async def members(self, ctx):
        '''See how many members are in the server.'''
        await ctx.send(f"We're at **{ctx.guild.member_count:,}** members! {self.ona.config.heart_eyes}")

    @commands.command(aliases=["avi", "pfp"])
    async def avatar(self, ctx, member: discord.Member = None):
        '''Display a user's avatar.'''
        member = member if member else ctx.author
        avatar = BytesIO(await self.ona.download(member.avatar_url_as(static_format="png", size=256)))
        await ctx.send(f"{member.display_name}'s avatar:", file=discord.File(avatar, f"{member.id}.png"))

    @commands.command(aliases=["emoji", "e"])
    async def emote(self, ctx, emoji: discord.PartialEmoji):
        '''Get a fullsize image for an emote. Only works for emotes in servers Ona shares.'''
        await ctx.send(file=discord.File(BytesIO(await self.ona.download(emoji.url)), path.split(emoji.url)[1]))

    @commands.command(aliases=["info", "userinfo"])
    async def user(self, ctx, member: discord.Member = None):
        '''See information about a user.'''
        member = member if member else ctx.author
        if hasattr(member, "roles"):
            roles = f"**Roles:** {', '.join(role.name for role in member.roles[1:][::-1])}"
        else:
            roles = ""
        color = member.color if member.color.value else self.ona.config.ona_color
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

    @commands.command(aliases=["search", "g"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def google(self, ctx, *, query: str):
        '''Search for anything on Google.'''
        query = query if query else await ctx.ask("Give a word or phrase to search:")
        fields = [(result["title"], result["link"]) for result in await self.ona.google_search(query)]
        embeds = []
        per_page = 5
        for i in range(0, len(fields), per_page):
            embed = self.ona.quick_embed(title="Search Results", author=ctx.author, fields=fields[i:i+per_page])
            embeds.append(embed.set_thumbnail(url="https://i.imgur.com/oRN5hP2.png"))
        await ctx.embed_browser(embeds)

    @commands.command(aliases=["img", "image"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def imagesearch(self, ctx, *, query: str):
        '''Search for any image using Google.'''
        query = query if query else await ctx.ask("Give a word or phrase to search:")
        results = await self.ona.google_search(query, image=True)

        embeds = []
        for result in results:
            embed = self.ona.quick_embed(result["title"], title="Search Results", author=ctx.author)
            embeds.append(embed.set_image(url=result["link"]))
        await ctx.embed_browser(embeds)

    @commands.command(aliases=["yt"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def youtube(self, ctx, *, query: str):
        '''Search for a video on YouTube.'''
        query = query if query else await ctx.ask("Give a word or phrase to search:")
        results = await self.ona.google_search(f"youtube {query}")
        await ctx.send(next(item["link"] for item in results if "youtube.com/watch" in item["link"]))

    @commands.command()
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def define(self, ctx, *, query: str):
        '''Find the definition for a word or phrase.'''
        query = query if query else await ctx.ask("Give a word or phrase to define:")
        search_url = "https://od-api.oxforddictionaries.com/api/v1/search/en"
        headers = {"app_id": self.ona.secrets.oxford_id, "app_key": self.ona.secrets.oxford_key}
        params = {"q": query, "limit": 1}
        results = self.ona.download(search_url, params=params, headers=headers)["results"]
        self.ona.assert_(len(results), error=f"'{query}' is not an English word.")
        entry_url = "https://od-api.oxforddictionaries.com/api/v1/entries/en/" + results[0]["id"].lower()
        lex_entries = self.ona.download(entry_url, headers=headers)["results"][0]["lexicalEntries"]

        def combine_defs(lex_entry):    # flatten each lexical entry into a list of definitions
            senses = (sense for entry in lex_entry["entries"] for sense in entry["senses"] if "definitions" in sense)
            return [(sense.get("domains", ["Misc"])[0], sense["definitions"][0].capitalize()) for sense in senses]

        pages = [(lex_entry["lexicalCategory"], combine_defs(lex_entry)) for lex_entry in lex_entries]
        embeds = []
        for page in pages:
            embed = self.ona.quick_embed(title=f"{query.title()} - {page[0]}", author=ctx.author, fields=page[1])
            embeds.append(embed.set_thumbnail(url="https://i.imgur.com/hd60hLe.png"))
        await ctx.embed_browser(embeds)

    @commands.command()
    async def osu(self, ctx, *, username: str):
        '''Search for an osu! profile. Provide either an osu! username or user id.'''
        username = username if username else await ctx.ask("Give a username to search for:")
        mode = await ctx.ask("Choose a gamemode:", ["Standard", "Taiko", "Catch the Beat", "Mania"])
        params = {"k": self.ona.secrets.osu_key, "u": username, "m": mode}
        result = self.ona.download("https://osu.ppy.sh/api/get_user", params=params)
        self.ona.assert_(result.text != [], error="The username/id provided is invalid.")

        # All stats are provided as strings by default. Convert to python objects.
        osu_user = {k: loads(v) if str(v).replace(".", "").isdigit() else v for k, v in result[0].items()}
        url = f"https://osu.ppy.sh/osu_users/{osu_user['user_id']}"
        stats = [
            ("Rank", f"{osu_user['pp_rank']:,} ({osu_user['pp_country_rank']:,} {osu_user['country']})"),
            ("Level", int(osu_user["level"])),
            ("Performance Points", f"{int(osu_user['pp_raw']):,}"),
            ("Accuracy", round(osu_user["accuracy"], 2)),
            ("Playcount", f"{osu_user['playcount']:,}"),
            ("Ranked Score", f"{osu_user['ranked_score']:,}")
        ]
        embed = self.ona.quick_embed(title=f"{osu_user['username']}'s Stats", url=url, fields=stats)
        embed.set_thumbnail(url=f"https://a.ppy.sh/{osu_user['user_id']}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["sauce"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def source(self, ctx, url: str = None):
        '''Perform a reverse image search using iqdb.org.'''
        url = await ctx.url_handler(url)
        body = (await self.ona.download("http://iqdb.org", method="POST", data={"url": url})).decode()
        self.ona.assert_("No relevant matches" not in body, "HTTP request failed" not in body,
                         error="No results found.")
        parser = HTMLParser()
        urls = []

        def handler(tag, attrs):    # This handler parses the iqdb.org response html for all href links
            any(urls.append(attr[1]) for attr in attrs if attr[0] == "href")
        parser.handle_starttag = handler
        parser.feed(body)
        url = urls[2]   # The second href is the "best match"
        if url.startswith("//"):    # Fix links
            url = f"https:{url}"
        await ctx.send(f"Here's the closest match:\n{url}")


def setup(ona):
    ona.add_cog(Utility(ona))
