import discord
import datetime
import json
import urllib.request
from discord.ext import commands
from urllib.parse import quote
from urllib.request import urlopen, Request, HTTPError

#Naver Open API application ID
access_ID = os.environ["ID"]
client_id = (access_ID)
#Naver Open API application token
access_SECRET = os.environ["SECRET"]
client_secret = (access_SECRET)
colour = discord.Colour.blue()

class 기타(commands.Cog):
    """기타등등의 기능들을 보여줍니다"""

    def __init__(self, client):
        self.client = client


    @commands.command(name="한영번역", pass_context=True)
    async def translation(self, ctx, *, trsText):
        """한국어를 영어로 번역합니다."""
        baseurl = "https://openapi.naver.com/v1/papago/n2mt"
        try:
            if len(trsText) == 1:
                await ctx.send("단어 혹은 문장이 입력되지 않았어요. 다시한번 확인해주세요.")
            else:
                combineword = ""
                for word in trsText:
                    combineword += "" + word
                # if entered value is sentence, assemble again and strip blank at both side
                savedCombineword = combineword.strip()
                combineword = quote(savedCombineword)
                print(combineword)
                # Make Query String.
                dataParmas = "source=ko&target=en&text=" + combineword
                # Make a Request Instance
                request = Request(baseurl)
                # add header to packet
                request.add_header("X-Naver-Client-Id", client_id)
                request.add_header("X-Naver-Client-Secret", client_secret)
                response = urlopen(request, data=dataParmas.encode("utf-8"))

                responsedCode = response.getcode()
                if (responsedCode == 200):
                    response_body = response.read()
                    # response_body -> byte string : decode to utf-8
                    api_callResult = response_body.decode('utf-8')
                    # JSON data will be printed as string type. So need to make it back to type JSON(like dictionary)
                    api_callResult = json.loads(api_callResult)
                    # Final Result
                    translatedText = api_callResult['message']['result']["translatedText"]
                    embed = discord.Embed(title="한국어 -> 영어", description="", color=colour)
                    embed.add_field(name="한국어", value=savedCombineword, inline=False)
                    embed.add_field(name="영어", value=translatedText, inline=False)
                    embed.set_thumbnail(url="https://papago.naver.com/static/img/papago_og.png")
                    embed.timestamp = datetime.datetime.utcnow()
                    await ctx.send("번역 완료", embed=embed)
                else:
                    await ctx.send("Error Code : " + responsedCode)
        except HTTPError as e:
            await ctx.send("Translate Failed. HTTPError Occured.")

    @commands.command(name="영한번역", pass_context=True)
    async def displayembed(self, ctx, *, trsText):
        """영어를 한국어로 번역합니다."""
        baseurl = "https://openapi.naver.com/v1/papago/n2mt"
        try:
            if len(trsText) == 1:
                await ctx.send("단어 혹은 문장이 입력되지 않았어요. 다시한번 확인해주세요.")
            else:
                combineword = ""
                for word in trsText:
                    combineword += "" + word
                # if entered value is sentence, assemble again and strip blank at both side
                savedCombineword = combineword.strip()
                combineword = quote(savedCombineword)
                # Make Query String.
                dataParmas = "source=en&target=ko&text=" + combineword
                # Make a Request Instance
                request = Request(baseurl)
                # add header to packet
                request.add_header("X-Naver-Client-Id", client_id)
                request.add_header("X-Naver-Client-Secret", client_secret)
                response = urlopen(request, data=dataParmas.encode("utf-8"))

                responsedCode = response.getcode()
                if (responsedCode == 200):
                    response_body = response.read()
                    # response_body -> byte string : decode to utf-8
                    api_callResult = response_body.decode('utf-8')

                    # JSON data will be printed as string type. So need to make it back to type JSON(like dictionary)
                    api_callResult = json.loads(api_callResult)
                    # Final Result
                    translatedText = api_callResult['message']['result']["translatedText"]
                    embed = discord.Embed(title="영어 -> 한국어", description="", color=colour)
                    embed.add_field(name="영어", value=savedCombineword, inline=False)
                    embed.add_field(name="한국어", value=translatedText, inline=False)
                    embed.set_thumbnail(url="https://papago.naver.com/static/img/papago_og.png")
                    embed.timestamp = datetime.datetime.utcnow()
                    await ctx.send("번역 완료", embed=embed)
                else:
                    await ctx.send("Error Code : " + responsedCode)
        except HTTPError as e:
            await ctx.send("Translate Failed. HTTPError Occured.")
            
    @commands.command(name="인증", pass_context=True)
    async def certification(self, ctx):
        """사람임을 인증합니다.재미용"""
        code = "0"
        url = "https://openapi.naver.com/v1/captcha/nkey?code=" + code
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        if (rescode == 200):
            response_body = response.read()
            key = response_body.decode('utf-8')
            key = json.loads(key)
            key = key['key']
            url = "https://openapi.naver.com/v1/captcha/ncaptcha.bin?key=" + key
            request = urllib.request.Request(url)
            request.add_header("X-Naver-Client-Id", client_id)
            request.add_header("X-Naver-Client-Secret", client_secret)
            response = urllib.request.urlopen(request)
            rescode = response.getcode()
            if (rescode == 200):
                print("캡차 이미지 저장")
                response_body = response.read()
                name = str(ctx.author.id) + '.png'
                with open(name, 'wb') as f:
                    f.write(response_body)
                await ctx.send(file=discord.File(str(ctx.author.id) + '.png'))

                def check(msg):
                    return msg.author == ctx.author and msg.channel == ctx.channel

                try:
                    msg = await self.client.wait_for("message", timeout=60, check=check)
                except:
                    await ctx.send("시간초과입니다.")
                    return

                code = "1"
                value = msg.content
                url = "https://openapi.naver.com/v1/captcha/nkey?code=" + code + "&key=" + key + "&value=" + str(quote(value))
                request = urllib.request.Request(url)
                request.add_header("X-Naver-Client-Id", client_id)
                request.add_header("X-Naver-Client-Secret", client_secret)
                response = urllib.request.urlopen(request)
                rescode = response.getcode()
                if (rescode == 200):
                    response_body = response.read()
                    sid = response_body.decode('utf-8')
                    answer = json.loads(sid)
                    answer = answer['result']
                    time = json.loads(sid)
                    time = time['responseTime']
                    if str(answer) == 'True':
                        await ctx.send("정답입니다. 걸린시간:" + str(time) + '초')
                    if str(answer) == 'False':
                        await ctx.send("틀리셨습니다. 걸린시간:" + str(time) + '초')
                else:
                    print("Error Code:" + rescode)
            else:
                print("Error Code:" + rescode)
        else:
            print("Error Code:" + rescode)



def setup(client):
    client.add_cog(기타(client))
