import discord
import datetime
from discord.ext import commands

colour = discord.Colour.blue()

class 정보(commands.Cog):
    """정보확인을 할수있는 기능입니다"""

    def __init__(self, client):
        self.client = client

    @commands.command(name="핑", pass_context=True)
    async def ping(self, ctx):
        """핑(딜레이)을 보여줍니다."""
        latency = round(self.client.latency * 1000)
        embed = discord.Embed(title="핑(ms)", colour=colour)
        embed.add_field(name="퐁", value="{0}ms".format(latency), inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="정보", pass_context=True)
    async def information(self, ctx):
        """자신의 정보를 보여줍니다."""
        date = datetime.datetime.utcfromtimestamp(((int(ctx.author.id) >> 22) + 1420070400000) / 1000)
        embed = discord.Embed(color=colour)
        embed.add_field(name="이름", value=ctx.author.name, inline=False)
        embed.add_field(name="서버닉네임", value=ctx.author.display_name, inline=False)
        embed.add_field(name="가입일", value=str(date.year) + "년" + str(date.month) + "월" + str(date.day) + "일",
                        inline=False)
        embed.add_field(name="아이디", value=ctx.author.id, inline=False)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="시간", pass_context=True)
    async def time(self, ctx):
        """호스팅 지역의 년, 월, 일, 시간, 분, 초를 알려줍니다."""
        embed = discord.Embed(color=colour)
        a = datetime.datetime.today().year
        b = datetime.datetime.today().month
        c = datetime.datetime.today().day
        d = datetime.datetime.today().hour
        e = datetime.datetime.today().minute
        f = datetime.datetime.today().second
        embed.add_field(name="년", value=str(a) + "년", inline=True)
        embed.add_field(name="월", value=str(b) + "월", inline=True)
        embed.add_field(name="일", value=str(c) + "일", inline=True)
        embed.add_field(name="시간", value=str(d) + "시간", inline=True)
        embed.add_field(name="분", value=str(e) + "분", inline=True)
        embed.add_field(name="초", value=str(f) + "초", inline=True)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="서버정보", pass_context=True)
    async def serverinformation(self, ctx):
        """서버정보를 보여줍니다."""
        embed = discord.Embed(colour=colour)
        embed.add_field(name="서버 이름", value=ctx.guild.name, inline=False)
        embed.add_field(name="서버 아이디", value=ctx.guild.id, inline=False)
        embed.add_field(name="서버 지역", value=str(ctx.guild.region).title(), inline=False)
        embed.add_field(name="서버 주인", value=ctx.guild.owner.display_name, inline=False)
        embed.add_field(name="서버 만들어진 날짜", value=ctx.guild.created_at.strftime("%y/%m/%d %H:%M:%S"), inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(정보(client))