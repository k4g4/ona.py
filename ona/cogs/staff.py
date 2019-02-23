from discord.ext import commands
from ona.ona_utils import is_staff, is_admin


class Staff:
    '''Helpful commands for moderation and bot maintenance.'''

    def __init__(self, ona):
        self.ona = ona

    @commands.command(aliases=["shutdown"])
    @commands.check(is_admin)
    async def close(self, ctx):
        '''Completely shut down Ona.'''
        if await ctx.send("Are you sure you'd like me to shut down?", yes_or_no=True):
            await ctx.send("Shutting down...")
            await ctx.ona.wait_until_ready()
            await ctx.ona.close()
        else:
            await ctx.send("Shutdown aborted.")

    @commands.command()
    @commands.check(is_admin)
    async def eval(self, ctx, *expression: str):
        '''Evaluate any Python expression.'''
        try:
            await ctx.send(str(eval(" ".join(expression))))
        except Exception as e:
            raise self.ona.OnaError(f"Error during eval: {e}")


def setup(ona):
    ona.add_cog(Staff(ona))
