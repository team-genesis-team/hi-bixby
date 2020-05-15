import discord
import os
import datetime
from discord.ext import commands, tasks
from itertools import cycle



colour = discord.Colour.blue()
status = cycle(['하이빅스비명령어', '문의는 제네시스#7225'])


client = commands.Bot(command_prefix='하이빅스비')
client.remove_command('help')



for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")


 
@client.event
async def on_ready():
    print("다음으로 로그인합니다")
    print(client.user.name)
    print(client.user.id)
    print('Discord.py 버전 : ' + discord.__version__)
    print("bot starting..")#봇 시작이라고 뜨게하기
    print("==========")
    change_status.start()

@tasks.loop(seconds=10)
async def change_status():
    await client.change_presence(activity=discord.Game(next(status)))








access_token = os.environ["BOT_TOKEN"]
client.run(access_token)
