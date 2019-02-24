from discord.ext import commands
from ona.ona_utils import is_staff, is_admin, is_owner


class Staff:
    '''Helpful commands for moderation and bot maintenance.'''

    def __init__(self, ona):
        self.ona = ona

    def cog_check(self, ctx):
        return is_staff(ctx)

    @commands.command(aliases=["shutdown"])
    @commands.check(is_owner)
    async def close(self, ctx):
        '''Completely shut down Ona.'''
        if await ctx.send("Are you sure you'd like me to shut down?", yes_or_no=True):
            await ctx.send("Shutting down...")
            await self.ona.wait_until_ready()
            await self.ona.close()
        else:
            await ctx.send("Shutdown aborted.")

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
