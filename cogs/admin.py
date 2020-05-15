import discord
import datetime
from discord.utils import get
from discord.ext import commands

colour = discord.Colour.blue()

class 관리자(commands.Cog):
    """관리자 기능들을 보여줍니다"""

    def __init__(self, client):
        self.client = client

    @commands.command(name="청소")
    @commands.has_permissions(administrator=True)
    async def _clear(self, ctx, number):
        """메시지를 청소합니다(관리자)"""
        number = int(number)  # Converting the amount of messages to delete to an integer
        if number >= 100 or number <= 0:
            embed = discord.Embed(title="1개부터 99개가지만 해주세요.", colour=colour)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)
        else:
            await ctx.channel.purge(limit=number + 1)
            embed = discord.Embed(title="{}개를 삭제하였습니다.".format(number), colour=colour)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)

    @_clear.error
    async def _clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title="{}님, 당신은 이 명령을 실행하실 권한이 없습니다.".format(ctx.message.author), colour=colour)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)

    @commands.command(name="킥")
    @commands.has_permissions(kick_members=True)
    async def _kick(self, ctx, member: discord.Member, *, reason=None):
        """맨션한 사람을 추방시킵니다. (관리자)"""
        await member.kick(reason=reason)
        embed = discord.Embed(title=str(member) + "을(를) 킥하였습니다.", colour=colour)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @_kick.error
    async def _kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title="{}님, 당신은 이 명령을 실행하실 권한이 없습니다.".format(ctx.message.author), colour=colour)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)

    @commands.command(name="밴")
    @commands.has_permissions(ban_members=True)
    async def _ban(self, ctx, member: discord.Member):
        """맨션한 사람을 밴시킵니다. (관리자)"""
        await member.ban()
        embed = discord.Embed(title=str(member) + "을(를) 밴시켰습니다.", colour=colour)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @_ban.error
    async def _ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title="{}님, 당신은 이 명령을 실행하실 권한이 없습니다.".format(ctx.message.author), colour=colour)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)

    @commands.command(name="언밴", pass_context=True)
    @commands.has_permissions(ban_members=True)
    async def _unban(self, ctx, *, user_name):
        """이름#아이디를 하시면 언밴 시킵니다. (관리자)"""
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = user_name.split('#')
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                embed = discord.Embed(title=f"{user.mention}을(를) 언밴시켰습니다.", colour=colour)
                embed.timestamp = datetime.datetime.utcnow()
                await ctx.send(embed=embed)
                return

    @_unban.error
    async def _unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title="{}님, 당신은 이 명령을 실행하실 권한이 없습니다.".format(ctx.message.author), colour=colour)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)

    @commands.command(name="뮤트", pass_context=True)
    @commands.has_permissions(administrator=True)
    async def _mute(self, ctx, member: discord.Member = None):
        """유저를 뮤트시킵니다. Muted라는 역할이 있서야 작동합니다. \n Muted역할은 뮤트의 기능을 추가해주세요 (관리자)"""
        member = member or ctx.message.author
        await member.add_roles(get(ctx.guild.roles, name="뮤트"))
        await ctx.send(member.mention + "를 뮤트 했습니다")

    @_mute.error
    async def _mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title="{}님, 당신은 이 명령을 실행하실 권한이 없습니다.".format(ctx.message.author), colour=colour)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)

    @commands.command(name="언뮤트", pass_context=True)
    @commands.has_permissions(administrator=True)
    async def _unmute(self, ctx, member: discord.Member = None):
        """유저를 언뮤트 시킵니다. (관리자)"""
        member = member or ctx.message.author
        await member.remove_roles(get(ctx.guild.roles, name='뮤트'))
        await ctx.send(member.mention + "를 언뮤트 했습니다.")

    @_unmute.error
    async def _unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title="{}님, 당신은 이 명령을 실행하실 권한이 없습니다.".format(ctx.message.author), colour=colour)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)


def setup(client):
    client.add_cog(관리자(client))
