import time
import asyncio
import discord
from json import loads
from datetime import datetime, timedelta
from html.parser import HTMLParser
from discord.ext import commands


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

    @commands.command()
    async def uptime(self, ctx):
        '''Check how long Ona has been running for.'''
        delta = datetime.utcnow() - self.ona.uptime
        uptime = self.ona.plural(delta.days, 'day') if delta.days else self.ona.plural(delta.seconds, 'second')
        await ctx.send(f"I've been running for {uptime}.")

    @commands.command()
    @commands.guild_only()
    async def members(self, ctx):
        '''See how many members are in the server.'''
        await ctx.send(f"We're at **{ctx.guild.member_count:,}** members! {self.ona.config.heart_eyes}")

    @commands.command(aliases=["server", "server_info"])
    @commands.guild_only()
    async def serverinfo(self, ctx):
        '''See detailed information about a server.'''
        fields = [("Owner", ctx.guild.owner.mention), ("ID", ctx.guild.id),
                  ("Members", f"{ctx.guild.member_count:,}"), ("Boosts", ctx.guild.premium_subscription_count),
                  ("Roles", len(ctx.guild.roles)), ("Created", ctx.guild.created_at.strftime("%b %d, %Y")),
                  ("Channels", f"{len(ctx.guild.text_channels)} text, {len(ctx.guild.voice_channels)} voice"),
                  ("Static Emotes", (f"{len([str(emoji) for emoji in ctx.guild.emojis if not emoji.animated])}"
                                     f" / {ctx.guild.emoji_limit}")),
                  ("Animated Emotes", (f"{len([str(emoji) for emoji in ctx.guild.emojis if emoji.animated])}"
                                       f" / {ctx.guild.emoji_limit}"))]
        thumbnail = ctx.guild.icon_url_as(format="png")
        embed = self.ona.embed(title=ctx.guild.name, thumbnail=thumbnail, fields=fields)
        embed.set_image(url=ctx.guild.banner_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["avi", "profile_picture", "pfp"])
    async def avatar(self, ctx, member: discord.Member = None):
        '''Display a user's avatar.'''
        member = member or ctx.author
        await ctx.send(asset=member.avatar_url_as(static_format="png", size=256))

    @commands.command(aliases=["emoji", "e"])
    async def emote(self, ctx, emoji: discord.PartialEmoji):
        '''Get a fullsize image for an emote.
        Only works for emotes in servers Ona shares.'''
        await ctx.send(asset=emoji.url)

    @commands.command(aliases=["info", "member", "member_info", "userinfo", "user_info"])
    async def memberinfo(self, ctx, member: discord.Member = None):
        '''See detailed information about a member.'''
        member = member or ctx.author
        fields = [("Global Name", member.name), ("ID", member.id),
                  ("Created", member.created_at.strftime("%b %d, %Y"))]
        if hasattr(member, "roles"):
            fields.insert(0, ("Roles", f"{', '.join(role.name for role in member.roles[1:][::-1])}"))
        if hasattr(member, "joined_at"):
            fields.append(("Joined", member.joined_at.strftime("%b %d, %Y")))
        if member.activity:
            if member.activity.name == "Spotify":
                fields.append(("Listening to", member.activity.title))
            else:
                fields.append((member.activity.type.name.title(), member.activity.name))
        avatar = member.avatar_url_as(static_format="png")
        embed = self.ona.embed(title=member.display_name, thumbnail=avatar, fields=fields)
        if member.color.value:
            embed.color = member.color
        await ctx.send(embed=embed)

    @commands.command(aliases=["np", "now_playing"])
    async def nowplaying(self, ctx, member: discord.Member = None):
        '''See what a member is listening to on Spotify.'''
        member = member or ctx.author
        self.ona.assert_(member.activity.name == "Spotify",
                         error="This member isn't listening to anything on Spotify right now.")
        spotify = member.activity
        fields = [("Album", spotify.album), ("Artists", ", ".join(spotify.artists))]
        duration, current = spotify.duration, datetime.utcnow() - spotify.start
        position = f"{current.seconds//60}:{current.seconds%60:02} / {duration.seconds//60}:{duration.seconds%60:02}"
        fields.append(("Song Position", position))
        thumbnail = spotify.album_cover_url
        embed = self.ona.embed(title=spotify.title, thumbnail=thumbnail, author=member, fields=fields)
        await ctx.send(embed=embed)

    @commands.command(aliases=["search", "g"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def google(self, ctx, *, query=""):
        '''Search for anything on Google.'''
        query = query or await ctx.ask("Give a word or phrase to search:")
        fields = [(result["title"], result["link"]) for result in await self.ona.google_search(query)]
        embeds = []
        per_page = 5
        for i in range(0, len(fields), per_page):
            embed = self.ona.embed(title="Search Results", author=ctx.author, fields=fields[i:i+per_page])
            embeds.append(embed.set_thumbnail(url="https://i.imgur.com/oRN5hP2.png"))
        await ctx.embed_browser(embeds)

    @commands.command(aliases=["img", "image", "image_search"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def imagesearch(self, ctx, *, query=""):
        '''Search for any image using Google.'''
        query = query or await ctx.ask("Give a word or phrase to search:")
        results = await self.ona.google_search(query, image=True)
        embeds = []
        for result in results:
            embed = self.ona.embed(result["title"], title="Search Results", author=ctx.author)
            embeds.append(embed.set_image(url=result["link"]))
        await ctx.embed_browser(embeds)

    @commands.command(aliases=["yt"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def youtube(self, ctx, *, query=""):
        '''Search for a video on YouTube.'''
        query = query if query else await ctx.ask("Give a word or phrase to search:")
        results = await self.ona.google_search(f"youtube {query}")
        await ctx.send(next(item["link"] for item in results if "youtube.com/watch" in item["link"]))

    @commands.command()
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def define(self, ctx, *, query=""):
        '''Find the definition for a word or phrase.'''
        query = query or await ctx.ask("Give a word or phrase to define:")
        search_url = "https://od-api.oxforddictionaries.com/api/v1/search/en"
        headers = {"app_id": self.ona.secrets.oxford_id, "app_key": self.ona.secrets.oxford_key}
        params = {"q": query, "limit": 1}
        results = (await self.ona.request(search_url, params=params, headers=headers))["results"]
        self.ona.assert_(len(results), error=f"'{query}' is not an English word.")
        entry_url = "https://od-api.oxforddictionaries.com/api/v1/entries/en/" + results[0]["id"].lower()
        lex_entries = (await self.ona.request(entry_url, headers=headers))["results"][0]["lexicalEntries"]

        def combine_defs(lex_entry):    # flatten each lexical entry into a list of definitions
            senses = (sense for entry in lex_entry["entries"] for sense in entry["senses"] if "definitions" in sense)
            return [(sense.get("domains", ["Misc"])[0], sense["definitions"][0].capitalize())
                    for sense in senses]

        pages = [(lex_entry["lexicalCategory"], combine_defs(lex_entry)) for lex_entry in lex_entries]
        embeds = []
        for page in pages:
            embed = self.ona.embed(title=f"{query.title()} - {page[0]}", author=ctx.author, fields=page[1])
            embeds.append(embed.set_thumbnail(url="https://i.imgur.com/hd60hLe.png"))
        await ctx.embed_browser(embeds)

    @commands.command(aliases=["ud"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def urban(self, ctx, *, query=""):
        '''Find the urban dictionary entry for a word or phrase.'''
        query = query or await ctx.ask("Give a word or phrase to search for:")
        results = (await self.ona.request(f"https://api.urbandictionary.com/v0/define?term={query}"))["list"]
        embeds = []

        def strip(s):
            return s.replace("[", "").replace("]", "")
        for result in results:
            fields = [("Definition", strip(result["definition"])), ("Example", strip(result["example"]))]
            embed = self.ona.embed(title=query.title(), author=ctx.author, fields=fields)
            embed.url = result["permalink"]
            embeds.append(embed.set_thumbnail(url="https://i.imgur.com/RoKVYoy.jpg"))
        await ctx.embed_browser(embeds)

    @commands.command()
    async def osu(self, ctx, *, username=""):
        '''Search for an osu! profile.
        Provide either an osu! username or user id.'''
        username = username or await ctx.ask("Give a username to search for:")
        mode = await ctx.ask("Choose a gamemode:", ["Standard", "Taiko", "Catch the Beat", "Mania"])
        params = {"k": self.ona.secrets.osu_key, "u": username, "m": mode}
        result = self.ona.request("https://osu.ppy.sh/api/get_user", params=params)
        self.ona.assert_(result.text != [], error="The username/id provided is invalid.")

        # All stats are provided as strings by default. Convert to python objects.
        osu_user = {k: loads(v) if str(v).replace(".", "").isdigit() else v
                    for k, v in result[0].items()}
        url = f"https://osu.ppy.sh/osu_users/{osu_user['user_id']}"
        stats = [
            ("Rank", f"{osu_user['pp_rank']:,} ({osu_user['pp_country_rank']:,} {osu_user['country']})"),
            ("Level", int(osu_user["level"])),
            ("Performance Points", f"{int(osu_user['pp_raw']):,}"),
            ("Accuracy", round(osu_user["accuracy"], 2)),
            ("Playcount", f"{osu_user['playcount']:,}"),
            ("Ranked Score", f"{osu_user['ranked_score']:,}")
        ]
        embed = self.ona.embed(title=f"{osu_user['username']}'s Stats", url=url, fields=stats)
        embed.set_thumbnail(url=f"https://a.ppy.sh/{osu_user['user_id']}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["sauce"])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def source(self, ctx):
        '''Perform a reverse image search using iqdb.org.'''
        url = await ctx.get_last_url()
        body = (await self.ona.request("http://iqdb.org", method="POST", data={"url": url})).decode()
        self.ona.assert_("No relevant matches" not in body, "HTTP request failed" not in body,
                         error="No results found.")
        parser = HTMLParser()
        hrefs = []

        def handler(tag, attrs):    # This handler parses the iqdb.org response html for all href links
            any(hrefs.append(attr[1]) for attr in attrs if attr[0] == "href")
        parser.handle_starttag = handler
        parser.feed(body)
        href = hrefs[2]   # The second href is the "best match"
        if href.startswith("//"):    # Fix links
            href = f"https:{href}"
        await ctx.send(f"Here's the closest match:\n{href}")


def setup(ona):
    ona.add_cog(Utility(ona))
