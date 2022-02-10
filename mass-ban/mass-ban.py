import datetime
import typing

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

class MassBan(commands.Cog): 
    """Author: @dpsKita"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["mban"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def massban(self, ctx, members: commands.Greedy[discord.Member], days: typing.Optional[int] = 0, *, reason: str = None):
        """Mass-bans members
        \n[massban/mban] <members (seperated by space)> <deleted message for number of days (optional)> <reason>
        """

        if members is None:
            ctx.send_help(ctx.command)

        for member in members:
            try:
                await member.ban(delete_message_days=days, reason=f"{reason if reason else None}")
            except discord.Forbidden:
                await ctx.send("I don't have the proper permissions to ban people.")
            except Exception as e:
                await ctx.send("An unexpected error occurred, please check the logs for more details.")
                return
                        
def setup(bot):
    bot.add_cog(MassBan(bot))