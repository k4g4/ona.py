from discord.ext import commands
from ona.ona_utils import is_staff, is_admin


class Staff():
    def __init__(self, ona):
        self.ona = ona

    @commands.command()
    @commands.check(is_admin)
    async def close(self, ctx):
        loading = ctx.ona.get_emoji_named("nowLoading")
        await ctx.send(f"{loading} Shutting down... {loading}")
        await ctx.ona.wait_until_ready()
        await ctx.ona.close()


def setup(ona):
    ona.add_cog(Staff(ona))
