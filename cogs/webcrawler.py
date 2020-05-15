import discord
import datetime
import warnings
import re
import bs4
import urllib
import requests as rq
from discord.ext import commands
from bs4 import BeautifulSoup
from bs4 import BeautifulSoup as bs
from urllib.parse import quote
from urllib.request import HTTPError
from urllib.request import urlopen, Request

colour = discord.Colour.blue()

opggsummonersearch = 'https://www.op.gg/summoner/userName='

tierScore = {
        'default': 0,
        'iron': 1,
        'bronze': 2,
        'silver': 3,
        'gold': 4,
        'platinum': 5,
        'diamond': 6,
        'master': 7,
        'grandmaster': 8,
        'challenger': 9
    }


def deleteTags(htmls):
    for a in range(len(htmls)):
        htmls[a] = re.sub('<.+?>', '', str(htmls[a]), 0).strip()
    return htmls


def tierCompare(solorank, flexrank):
    if tierScore[solorank] > tierScore[flexrank]:
        return 0
    elif tierScore[solorank] < tierScore[flexrank]:
        return 1
    else:
        return 2

warnings.filterwarnings(action='ignore')


class 크롤링(commands.Cog):
    """웹크롤링을 활용한 기능들을 보여줍니다"""

    def __init__(self, client):
        self.client = client


    @commands.command(name="인벤", pass_context=True)
    async def inven(self, ctx):
        """인벤의 주요뉴스를 보여줍니다"""
        embed = discord.Embed(
            title="인벤 주요뉴스",
            colour=colour
        )
        targetSite = 'http://www.inven.co.kr/webzine/news/?hotnews=1'

        header = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
        melonrqRetry = rq.get(targetSite, headers=header)
        melonht = melonrqRetry.text
        melonsp = bs(melonht, 'html.parser')
        artists = melonsp.findAll('span', {'class': 'title'})
        titles = melonsp.findAll('span', {'class': 'summary'})
        for i in range(len(titles)):
            artist = artists[i].text.strip()
            title = titles[i].text.strip()
            embed.add_field(name="{0:3d}".format(i + 1), value='제목:{0} - 내용:{1}'.format(artist, title), inline=False)
            embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="노래순위", pass_context=True)
    async def music(self, ctx):
        """멜론차트를 모여줍니다."""
        embed = discord.Embed(
            title="노래순위",
            description="노래순위입니다.",
            colour=colour
        )
        targetSite = 'https://www.melon.com/chart/index.htm'

        header = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
        melonrqRetry = rq.get(targetSite, headers=header)
        melonht = melonrqRetry.text
        melonsp = bs(melonht, 'html.parser')
        artists = melonsp.findAll('span', {'class': 'checkEllipsis'})
        titles = melonsp.findAll('div', {'class': 'ellipsis rank01'})
        for i in range(len(titles)):
            artist = artists[i].text.strip()
            title = titles[i].text.strip()
            embed.add_field(name="{0:3d}위".format(i + 1), value='{0} - {1}'.format(artist, title), inline=False)
            embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="실검", pass_context=True)
    async def sc(self, ctx):
        """네이버 실검을보여줍니다 연관성에 따라 다르게 나올수있습니다"""
        embed = discord.Embed(
            title="실시간 검색어",
            description="실시간 검색어입니다.",
            colour=colour
        )
        targetSite = 'https://datalab.naver.com/keyword/realtimeList.naver?groupingLevel=3&where=main'
        header = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
        source = rq.get(targetSite, headers=header).text
        soup = BeautifulSoup(source, "html.parser")
        hotKeys = soup.select("span.item_title")
        index = 0
        for key in hotKeys:
            index += 1
            embed.add_field(name="{}위".format(index), value=key.text, inline=False)
            embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="롤전적", pass_context=True)
    async def lol(self, ctx, *, playerNickname):
        """롤전적을 보여줍니다."""
        checkURLBool = urlopen(opggsummonersearch + quote(playerNickname))
        bs = BeautifulSoup(checkURLBool, 'html.parser')

        # 자유랭크 언랭은 뒤에 '?image=q_auto&v=1'표현이없다
        RankMedal = bs.findAll('img', {
            'src': re.compile('\/\/[a-z]*\-[A-Za-z]*\.[A-Za-z]*\.[A-Za-z]*\/[A-Za-z]*\/[A-Za-z]*\/[a-z0-9_]*\.png')})
        # index 0 : Solo Rank
        # index 1 : Flexible 5v5 rank

        # for mostUsedChampion
        mostUsedChampion = bs.find('div', {'class': 'ChampionName'})
        mostUsedChampionKDA = bs.find('span', {'class': 'KDA'})

        # 솔랭, 자랭 둘다 배치가 안되어있는경우 -> 사용된 챔피언 자체가 없다. 즉 모스트 챔피언 메뉴를 넣을 필요가 없다.

        if len(playerNickname) == 1:
            embed = discord.Embed(title="소환사 이름이 입력되지 않았습니다!", description="", color=colour)
            embed.add_field(name="Summoner name not entered",
                            value="To use command !롤전적 : !롤전적 (Summoner Nickname)", inline=False)
            await ctx.send("Error : Incorrect command usage ", embed=embed)

        elif len(deleteTags(bs.findAll('h2', {'class': 'Title'}))) != 0:
            embed = discord.Embed(title="존재하지 않는 소환사", description="", color=colour)
            embed.add_field(name="해당 닉네임의 소환사가 존재하지 않습니다.", value="소환사 이름을 확인해주세요", inline=False)
            await ctx.send("Error : Non existing Summoner ", embed=embed)
        else:
            try:
                # Scrape Summoner's Rank information
                # [Solorank,Solorank Tier]
                solorank_Types_and_Tier_Info = deleteTags(bs.findAll('div', {'class': {'RankType', 'TierRank'}}))
                # [Solorank LeaguePoint, Solorank W, Solorank L, Solorank Winratio]
                solorank_Point_and_winratio = deleteTags(
                    bs.findAll('span', {'class': {'LeaguePoints', 'wins', 'losses', 'winratio'}}))
                # [Flex 5:5 Rank,Flexrank Tier,Flextier leaguepoint + W/L,Flextier win ratio]
                flexrank_Types_and_Tier_Info = deleteTags(bs.findAll('div', {
                    'class': {'sub-tier__rank-type', 'sub-tier__rank-tier', 'sub-tier__league-point',
                              'sub-tier__gray-text'}}))
                # ['Flextier W/L]
                flexrank_Point_and_winratio = deleteTags(bs.findAll('span', {'class': {'sub-tier__gray-text'}}))

                # embed.set_imag()는 하나만 들어갈수 있다.

                # 솔랭, 자랭 둘다 배치 안되어있는 경우 -> 모스트 챔피언 출력 X
                if len(solorank_Point_and_winratio) == 0 and len(flexrank_Point_and_winratio) == 0:
                    embed = discord.Embed(title="소환사 전적검색", description="", color=colour)
                    embed.add_field(name="Summoner Search From op.gg", value=opggsummonersearch + playerNickname,
                                    inline=False)
                    embed.add_field(name="Ranked Solo : Unranked", value="Unranked", inline=False)
                    embed.add_field(name="Flex 5:5 Rank : Unranked", value="Unranked", inline=False)
                    embed.set_thumbnail(url='https:' + RankMedal[0]['src'])
                    await ctx.send("소환사 " + playerNickname + "님의 전적", embed=embed)

                # 솔로랭크 기록이 없는경우
                elif len(solorank_Point_and_winratio) == 0:

                    # most Used Champion Information : Champion Name, KDA, Win Rate
                    mostUsedChampion = bs.find('div', {'class': 'ChampionName'})
                    mostUsedChampion = mostUsedChampion.a.text.strip()
                    mostUsedChampionKDA = bs.find('span', {'class': 'KDA'})
                    mostUsedChampionKDA = mostUsedChampionKDA.text.split(':')[0]
                    mostUsedChampionWinRate = bs.find('div', {'class': "Played"})
                    mostUsedChampionWinRate = mostUsedChampionWinRate.div.text.strip()

                    FlexRankTier = flexrank_Types_and_Tier_Info[0] + ' : ' + flexrank_Types_and_Tier_Info[1]
                    FlexRankPointAndWinRatio = flexrank_Types_and_Tier_Info[2] + " /" + flexrank_Types_and_Tier_Info[-1]
                    embed = discord.Embed(title="소환사 전적검색", description="", color=colour)
                    embed.add_field(name="Summoner Search From op.gg", value=opggsummonersearch + playerNickname,
                                    inline=False)
                    embed.add_field(name="Ranked Solo : Unranked", value="Unranked", inline=False)
                    embed.add_field(name=FlexRankTier, value=FlexRankPointAndWinRatio, inline=False)
                    embed.add_field(name="Most Used Champion : " + mostUsedChampion,
                                    value="KDA : " + mostUsedChampionKDA + " / " + " WinRate : " + mostUsedChampionWinRate,
                                    inline=False)
                    embed.set_thumbnail(url='https:' + RankMedal[1]['src'])
                    await ctx.send("소환사 " + playerNickname + "님의 전적", embed=embed)

                # 자유랭크 기록이 없는경우
                elif len(flexrank_Point_and_winratio) == 0:

                    # most Used Champion Information : Champion Name, KDA, Win Rate
                    mostUsedChampion = bs.find('div', {'class': 'ChampionName'})
                    mostUsedChampion = mostUsedChampion.a.text.strip()
                    mostUsedChampionKDA = bs.find('span', {'class': 'KDA'})
                    mostUsedChampionKDA = mostUsedChampionKDA.text.split(':')[0]
                    mostUsedChampionWinRate = bs.find('div', {'class': "Played"})
                    mostUsedChampionWinRate = mostUsedChampionWinRate.div.text.strip()

                    SoloRankTier = solorank_Types_and_Tier_Info[0] + ' : ' + solorank_Types_and_Tier_Info[1]
                    SoloRankPointAndWinRatio = solorank_Point_and_winratio[0] + "/ " + solorank_Point_and_winratio[
                        1] + " " + solorank_Point_and_winratio[2] + " /" + solorank_Point_and_winratio[3]
                    embed = discord.Embed(title="소환사 전적검색", description="", color=colour)
                    embed.add_field(name="Summoner Search From op.gg", value=opggsummonersearch + playerNickname,
                                    inline=False)
                    embed.add_field(name=SoloRankTier, value=SoloRankPointAndWinRatio, inline=False)
                    embed.add_field(name="Flex 5:5 Rank : Unranked", value="Unranked", inline=False)
                    embed.add_field(name="Most Used Champion : " + mostUsedChampion,
                                    value="KDA : " + mostUsedChampionKDA + " / " + "WinRate : " + mostUsedChampionWinRate,
                                    inline=False)
                    embed.set_thumbnail(url='https:' + RankMedal[0]['src'])
                    await ctx.send("소환사 " + playerNickname + "님의 전적", embed=embed)
                # 두가지 유형의 랭크 모두 완료된사람
                else:
                    # 더 높은 티어를 thumbnail에 안착
                    solorankmedal = RankMedal[0]['src'].split('/')[-1].split('?')[0].split('.')[0].split('_')
                    flexrankmedal = RankMedal[1]['src'].split('/')[-1].split('?')[0].split('.')[0].split('_')

                    # Make State
                    SoloRankTier = solorank_Types_and_Tier_Info[0] + ' : ' + solorank_Types_and_Tier_Info[1]
                    SoloRankPointAndWinRatio = solorank_Point_and_winratio[0] + "/ " + solorank_Point_and_winratio[
                        1] + " " + solorank_Point_and_winratio[2] + " /" + solorank_Point_and_winratio[3]
                    FlexRankTier = flexrank_Types_and_Tier_Info[0] + ' : ' + flexrank_Types_and_Tier_Info[1]
                    FlexRankPointAndWinRatio = flexrank_Types_and_Tier_Info[2] + " /" + flexrank_Types_and_Tier_Info[-1]

                    # most Used Champion Information : Champion Name, KDA, Win Rate
                    mostUsedChampion = bs.find('div', {'class': 'ChampionName'})
                    mostUsedChampion = mostUsedChampion.a.text.strip()
                    mostUsedChampionKDA = bs.find('span', {'class': 'KDA'})
                    mostUsedChampionKDA = mostUsedChampionKDA.text.split(':')[0]
                    mostUsedChampionWinRate = bs.find('div', {'class': "Played"})
                    mostUsedChampionWinRate = mostUsedChampionWinRate.div.text.strip()

                    cmpTier = tierCompare(solorankmedal[0], flexrankmedal[0])
                    embed = discord.Embed(title="소환사 전적검색", description="", color=colour)
                    embed.add_field(name="Summoner Search From op.gg", value=opggsummonersearch + playerNickname,
                                    inline=False)
                    embed.add_field(name=SoloRankTier, value=SoloRankPointAndWinRatio, inline=False)
                    embed.add_field(name=FlexRankTier, value=FlexRankPointAndWinRatio, inline=False)
                    embed.add_field(name="Most Used Champion : " + mostUsedChampion,
                                    value="KDA : " + mostUsedChampionKDA + " / " + " WinRate : " + mostUsedChampionWinRate,
                                    inline=False)
                    if cmpTier == 0:
                        embed.set_thumbnail(url='https:' + RankMedal[0]['src'])
                    elif cmpTier == 1:
                        embed.set_thumbnail(url='https:' + RankMedal[1]['src'])
                    else:
                        if solorankmedal[1] > flexrankmedal[1]:
                            embed.set_thumbnail(url='https:' + RankMedal[0]['src'])
                        elif solorankmedal[1] < flexrankmedal[1]:
                            embed.set_thumbnail(url='https:' + RankMedal[0]['src'])
                        else:
                            embed.set_thumbnail(url='https:' + RankMedal[0]['src'])
                    await ctx.send("소환사 " + playerNickname + "님의 전적", embed=embed)
            except HTTPError as e:
                embed = discord.Embed(title="소환사 전적검색 실패", description="", color=colour)
                embed.add_field(name="", value="올바르지 않은 소환사 이름입니다. 다시 확인해주세요!", inline=False)
                await ctx.send("Wrong Summoner Nickname")

            except UnicodeEncodeError as e:
                embed = discord.Embed(title="소환사 전적검색 실패", description="", color=colour)
                embed.add_field(name="???", value="올바르지 않은 소환사 이름입니다. 다시 확인해주세요!", inline=False)
                await ctx.send("Wrong Summoner Nickname", embed=embed)

    @commands.command(name="영화순위", pass_context=True)
    async def movie(self, ctx):
        """영화를 1~20순위로 나눈 영화순위를 보여줍니다."""
        # http://ticket2.movie.daum.net/movie/movieranklist.aspx
        i1 = 0  # 랭킹 string값
        embed = discord.Embed(
            title="영화순위",
            description="영화순위입니다.",
            colour=colour
        )
        hdr = {'User-Agent': 'Mozilla/5.0'}
        url = 'http://ticket2.movie.daum.net/movie/movieranklist.aspx'
        req = Request(url, headers=hdr)
        html = urllib.request.urlopen(req)
        bsObj = bs4.BeautifulSoup(html, "html.parser")
        moviechartBase = bsObj.find('div', {'class': 'main_detail'})
        moviechart1 = moviechartBase.find('ul', {'class': 'list_boxthumb'})
        moviechart2 = moviechart1.find_all('li')
        for i in range(0, 20):
            i1 = i1 + 1
            stri1 = str(i1)  # i1은 영화랭킹을 나타내는데 사용됩니다
            moviechartLi1 = moviechart2[i]  # ------------------------- 1등랭킹 영화---------------------------
            moviechartLi1Div = moviechartLi1.find('div', {'class': 'desc_boxthumb'})  # 영화박스 나타내는 Div
            moviechartLi1MovieName1 = moviechartLi1Div.find('strong', {'class': 'tit_join'})
            moviechartLi1MovieName = moviechartLi1MovieName1.text.strip()  # 영화 제목
            moviechartLi1Ratting1 = moviechartLi1Div.find('div', {'class': 'raking_grade'})
            moviechartLi1Ratting2 = moviechartLi1Ratting1.find('em', {'class': 'emph_grade'})
            moviechartLi1Ratting = moviechartLi1Ratting2.text.strip()  # 영화 평점
            moviechartLi1openDay1 = moviechartLi1Div.find('dl', {'class': 'list_state'})
            moviechartLi1openDay2 = moviechartLi1openDay1.find_all('dd')  # 개봉날짜, 예매율 두개포함한 dd임
            moviechartLi1openDay3 = moviechartLi1openDay2[0]
            moviechartLi1Yerating1 = moviechartLi1openDay2[1]
            moviechartLi1openDay = moviechartLi1openDay3.text.strip()  # 개봉날짜
            moviechartLi1Yerating = moviechartLi1Yerating1.text.strip()  # 예매율 ,랭킹변동
            embed.add_field(name='---------------랭킹' + stri1 + '위---------------',
                            value='\n영화제목 : ' + moviechartLi1MovieName + '\n영화평점 : ' + moviechartLi1Ratting + '점' + '\n개봉날짜 : ' + moviechartLi1openDay + '\n예매율,랭킹변동 : ' + moviechartLi1Yerating,
                            inline=False)  # 영화랭킹
            embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="코로나", pass_context=True)
    async def corona19(self, ctx):
        """한국의 코로나 바이러스 현황을 알려줍니다."""
        # 보건복지부 코로나 바이러스 정보사이트"
        covidSite = "http://ncov.mohw.go.kr/index.jsp"
        covidNotice = "http://ncov.mohw.go.kr"
        html = urlopen(covidSite)
        bs = BeautifulSoup(html, 'html.parser')
        latestupdateTime = bs.find('span', {'class': "livedate"}).text.split(',')[0][1:].split('.')
        statisticalNumbers = bs.findAll('span', {'class': 'num'})
        beforedayNumbers = bs.findAll('span', {'class': 'before'})

        # 주요 브리핑 및 뉴스링크
        briefTasks = []
        mainbrief = bs.findAll('a', {'href': re.compile('\/tcmBoardView\.do\?contSeq=[0-9]*')})
        for brf in mainbrief:
            container = []
            container.append(brf.text)
            container.append(covidNotice + brf['href'])
            briefTasks.append(container)

        # 통계수치
        statNum = []
        # 전일대비 수치
        beforeNum = []
        for num in range(7):
            statNum.append(statisticalNumbers[num].text)
        for num in range(4):
            beforeNum.append(beforedayNumbers[num].text.split('(')[-1].split(')')[0])

        totalPeopletoInt = statNum[0].split(')')[-1].split(',')
        tpInt = ''.join(totalPeopletoInt)
        lethatRate = round((int(statNum[3]) / int(tpInt)) * 100, 2)
        embed = discord.Embed(title="Covid-19 Virus Korea Status", description="", color=colour)
        embed.add_field(name="Data source : Ministry of Health and Welfare of Korea",
                        value="http://ncov.mohw.go.kr/index.jsp", inline=False)
        embed.add_field(name="Latest data refred time",
                        value="해당 자료는 " + latestupdateTime[0] + "월 " + latestupdateTime[1] + "일 " + latestupdateTime[
                            2] + " 자료입니다.", inline=False)
        embed.add_field(name="확진환자(누적)", value=statNum[0].split(')')[-1] + "(" + beforeNum[0] + ")", inline=True)
        embed.add_field(name="완치환자(격리해제)", value=statNum[1] + "(" + beforeNum[1] + ")", inline=True)
        embed.add_field(name="치료중(격리 중)", value=statNum[2] + "(" + beforeNum[2] + ")", inline=True)
        embed.add_field(name="사망", value=statNum[3] + "(" + beforeNum[3] + ")", inline=True)
        embed.add_field(name="누적확진률", value=statNum[6], inline=True)
        embed.add_field(name="치사율", value=str(lethatRate) + " %", inline=True)
        embed.add_field(name="- 최신 브리핑 1 : " + briefTasks[0][0], value="Link : " + briefTasks[0][1], inline=False)
        embed.add_field(name="- 최신 브리핑 2 : " + briefTasks[1][0], value="Link : " + briefTasks[1][1], inline=False)
        embed.set_thumbnail(
            url="https://wikis.krsocsci.org/images/7/79/%EB%8C%80%ED%95%9C%EC%99%95%EA%B5%AD_%ED%83%9C%EA%B7%B9%EA%B8%B0.jpg")
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send("Covid-19 Virus Korea Status", embed=embed)

    @commands.command(name="검색")
    async def _search_blog(self, ctx, *, search_query):
        """네이버에서 블로그목록을 검색합니다."""
        temp = 0
        url_base = "https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query="
        url = url_base + urllib.parse.quote(search_query)
        title = ["", "", ""]  # 더 많은 검색 : 빈칸("")을 늘리셔야 합니다.
        link = ["", "", ""]  # 더 많은 검색 : 빈칸("")을 늘리셔야 합니다.
        soup = BeautifulSoup(urllib.request.urlopen(url).read(), 'html.parser')
        result = soup.find_all('a', "sh_blog_title _sp_each_url _sp_each_title")
        embed = discord.Embed(title="검색 결과", description=" ", color=colour)
        for n in result:
            if temp == 3:  # 더 많은 검색 : 숫자(3)를 늘리셔야 합니다.
                break
            title[temp] = n.get("title")
            link[temp] = n.get("href")
            embed.add_field(name=title[temp], value=link[temp], inline=False)
            temp += 1
        embed.set_footer(text="검색 완료!")
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(크롤링(client))