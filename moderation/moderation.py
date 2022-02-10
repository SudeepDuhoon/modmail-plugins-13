import datetime
import typing

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

MEMBER_ID_REGEX = re.compile(r'<@!?([0-9]+)>$')

class MemberOrID(commands.IDConverter):
    async def convert(self, ctx: commands.Context, argument: str) -> Union[discord.Member, discord.User]:
        result: Union[discord.Member, discord.User]
        try:
            result = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            match = self._get_id_match(argument) or MEMBER_ID_REGEX.match(argument)
            if match:
                try:
                    result = await ctx.bot.fetch_user(int(match.group(1)))
                except discord.NotFound as e:
                    raise commands.BadArgument(f'Member {argument} not found') from e
            else:
                raise commands.BadArgument(f'Member {argument} not found')

        return result

class Moderation(commands.Cog): 
    """Author: @dpsKita"""
    
    def __init__(self, bot):
        self.bot = bot
        self.defaultColor = 0x2f3136
        self.db = bot.api.get_plugin_partition(self)

    @commands.command(aliases=["lchannel"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def logschannel(self, ctx, channel: discord.TextChannel):
        """Set the logs channel"""
        await self.db.find_one_and_update({"_id": "config"}, {"$set": {"logs_channel": channel.id}}, upsert=True)
        
        embed = discord.Embed(color=self.defaultColor, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Set Channel", value=f"Successfully set the logs channel to {channel.mention}", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(aliases=["mban"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def massban(self, ctx, members: commands.Greedy[discord.Member], days: typing.Optional[int] = 0, *, reason: str = None):
        """*Mass-bans members*\n
        Note(s)
        ├─ `Members` - seperate by space.
        ├─ `Days` - deleted messages for number of days (optional; default is 0).
        └─ `Reason` - self explanatory; optional."""
        config = await self.db.find_one({"_id": "config"})
        logs_channel = config["logs_channel"]
        setchannel = discord.utils.get(ctx.guild.channels, id=int(logs_channel))

        if members is not None:
            for member in members:
                if not isinstance(member, (discord.User, discord.Member)):
                    member = await MemberOrID.convert(self, ctx, member)
                try:
                    await member.ban(delete_message_days=days, reason=f"{reason if reason else None}")
                    embed = discord.Embed(color=self.defaultColor, timestamp=datetime.datetime.utcnow())
                    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                    
                    embed.add_field(name="Banned user:", value=f"{member.mention} | ID: {member.id}", inline=False)
                    embed.add_field(name="Banned by:", value=f"{ctx.author.mention} | ID: {ctx.author.id}", inline=False)
                    embed.add_field(name="Reason", value=reason, inline=False)

                    await setchannel.send(embed=embed)
                except discord.Forbidden:
                    await ctx.send("I don't have the proper permissions to ban people.")
                except Exception as e:
                    await ctx.send("An unexpected error occurred, please check the logs for more details.")
                    return
                try:
                    await ctx.message.delete()
                except discord.errors.Forbidden:
                    await ctx.send("Not enough permissions to delete messages.", delete_after=2)
        elif members is None:
            return await ctx.send_help(ctx.command)

def setup(bot):
    bot.add_cog(Moderation(bot))