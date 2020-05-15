import asyncio
import functools
import logging
import os
import pathlib
import discord
import discord.ext.commands as commands
import youtube_dl


def setup(client):
    """Extension's entry point."""
    client.add_cog(음악(client))


def duration_to_str(duration):
    """Converts a timestamp to a string representation."""
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    duration = []
    if days > 0: duration.append(f'{days} 일')
    if hours > 0: duration.append(f'{hours} 시간')
    if minutes > 0: duration.append(f'{minutes} 분')
    if seconds > 0 or len(duration) == 0: duration.append(f'{seconds} 초')

    return ', '.join(duration)


class MusicError(commands.UserInputError):
    """Base exception for errors involving the Music cog."""
    pass


class Song(discord.PCMVolumeTransformer):
    """Represents a song to play."""

    def __init__(self, song_info, volume=1.0):
        self.info = song_info.info
        self.requester = song_info.requester
        self.channel = song_info.channel
        self.filename = song_info.filename
        super().__init__(discord.FFmpegPCMAudio(self.filename, options='-vn'), volume=volume)


class SongInfo:
    """Represents a Song's info."""
    ytdl_opts = {
        'default_search': 'auto',
        'format': 'bestaudio/best',
        'ignoreerrors': True,
        'source_address': '0.0.0.0',
        'nocheckcertificate': True,
        'restrictfilenames': True,
        'logger': logging.getLogger(__name__),
        'logtostderr': False,
        'no_warnings': True,
        'quiet': True,
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'noplaylist': True
    }
    ytdl = youtube_dl.YoutubeDL(ytdl_opts)

    def __init__(self, info, requester, channel):
        self.info = info
        self.requester = requester
        self.channel = channel
        self.filename = info.get('_filename', self.ytdl.prepare_filename(self.info))
        self.downloaded = asyncio.Event()
        self.local_file = '_filename' in info

    @classmethod
    async def create(cls, query, requester, channel, loop=None):
        """Class method to create a SongInfo."""
        try:
            # Path.is_file() can throw a OSError on syntactically incorrect paths, like urls.
            if pathlib.Path(query).is_file():
                return cls.from_file(query, requester, channel)
        except OSError:
            pass

        return await cls.from_ytdl(query, requester, channel, loop=loop)

    @classmethod
    def from_file(cls, file, requester, channel):
        """Class method to create a SongInfo from a file on disk."""
        path = pathlib.Path(file)
        if not path.exists():
            raise MusicError(f'File {file} not found.')

        info = {
            '_filename': file,
            'title': path.stem,
            'creator': 'local file',
        }
        return cls(info, requester, channel)

    @classmethod
    async def from_ytdl(cls, request, requester, channel, loop=None):
        """Class method to create a SongInfo using ytdl."""
        loop = loop or asyncio.get_event_loop()

        # Get sparse info about our query
        partial = functools.partial(cls.ytdl.extract_info, request, download=False, process=False)
        sparse_info = await loop.run_in_executor(None, partial)

        if sparse_info is None:
            raise MusicError(f'정보를 검색 할 수 없습니다 : {request}')

        # If we get a playlist, select its first valid entry
        if "entries" not in sparse_info:
            info_to_process = sparse_info
        else:
            info_to_process = None
            for entry in sparse_info['entries']:
                if entry is not None:
                    info_to_process = entry
                    break
            if info_to_process is None:
                raise MusicError(f'정보를 검색 할 수 없습니다 : {request}')

        # Process full video info
        url = info_to_process.get('url', info_to_process.get('webpage_url', info_to_process.get('id')))
        partial = functools.partial(cls.ytdl.extract_info, url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise MusicError(f'정보를 검색 할 수 없습니다 : {request}')

        # Select the first search result if any
        if "entries" not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise MusicError(f'URL에서 정보를 검색 할 수 없습니다 : {info_to_process["url"]}')

        return cls(info, requester, channel)

    async def download(self, loop):
        """Downloads the song file with ytdl."""
        if not pathlib.Path(self.filename).exists():
            partial = functools.partial(self.ytdl.extract_info, self.info['webpage_url'], download=True)
            self.info = await loop.run_in_executor(None, partial)
        self.downloaded.set()

    async def wait_until_downloaded(self):
        """Helper function to wait until the song file has been downloaded."""
        await self.downloaded.wait()

    def __str__(self):
        title = f"**{self.info['title']}**"
        creator = f"**{self.info.get('creator') or self.info['uploader']}**"
        duration = f" (시간: {duration_to_str(self.info['duration'])})" if 'duration' in self.info else ''
        return f'{title} 아티스트: {creator}{duration}'


class Playlist(asyncio.Queue):
    """Represents a playlist."""

    def __iter__(self):
        return self._queue.__iter__()

    def clear(self):
        """Clears the playlist from its items."""
        for song in self._queue:
            os.remove(song.filename)
        self._queue.clear()

    def get_song(self):
        """Gets the first item of the playlist."""
        return self.get_nowait()

    def add_song(self, song):
        """Adds an item to the playlist."""
        self.put_nowait(song)

    def __str__(self):
        info = 'Current playlist:\n'
        info_len = len(info)

        for song in self:
            song_repr = f'{song}\n'
            song_repr_len = len(song_repr)

            if info_len + song_repr_len > 1995:
                info += '[...]'
                break

            info += song_repr
            info_len += song_repr_len

        return info


class GuildMusicState:
    """The music state of a guild."""

    def __init__(self, loop):
        self.playlist = Playlist(maxsize=50)
        self.voice_client = None
        self.loop = loop
        self.player_volume = 0.5
        self.skips = set()
        self.min_skips = 5

    @property
    def current_song(self):
        """Returns the song that is currently played."""
        return self.voice_client.source

    @property
    def volume(self):
        """Returns the volume of the audio player."""
        return self.player_volume

    @volume.setter
    def volume(self, value):
        """Sets the volume of the audio player."""
        self.player_volume = value
        if self.voice_client:
            self.voice_client.source.volume = value

    async def stop(self):
        """Clears the playlist and stops the player."""
        self.playlist.clear()
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None

    def is_playing(self):
        """Indicates if we're currently playing audio."""
        return self.voice_client and self.voice_client.is_playing()

    async def play_next_song(self, song=None, error=None):
        """Callback called after the voice_client has finished playing a source."""
        if error:
            await self.current_song.channel.send(f'오류발생 {self.current_song}: {error}')

        if song and not song.local_file and song.filename not in [s.filename for s in self.playlist]:
            os.remove(song.filename)

        if self.playlist.empty():
            await self.stop()
        else:
            next_song_info = self.playlist.get_song()
            await next_song_info.wait_until_downloaded()
            source = Song(next_song_info, self.player_volume)
            self.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next_song(next_song_info, e), self.loop).result())
            await next_song_info.channel.send(f'음악 시작합니다 정보:{next_song_info}')


class 음악(commands.Cog):
    """음악기능을 보여줍니다."""

    def __init__(self, client):
        self.client = client
        self.music_states = {}

    def cog_unload(self):
        """Handles special unloading."""
        for state in self.music_states.values():
            self.client.loop.create_task(state.stop())

    def cog_check(self, ctx):
        """Extra checks for the cog's commands."""
        if not ctx.guild:
            raise commands.NoPrivateMessage('개인 메시지에는이 명령을 사용할 수 없습니다.')
        return True

    async def cog_before_invoke(self, ctx):
        """Pre invoke hook for the cog's commands."""
        ctx.music_state = self.music_states.setdefault(ctx.guild.id, GuildMusicState(self.client.loop))

    async def cog_command_error(self, ctx, error):
        """Error handler for the cog's commands."""
        if not isinstance(error, (commands.UserInputError, commands.CheckFailure)):
            return

        try:
            await ctx.send(error)
        except discord.Forbidden:
            pass  # /shrug

    @commands.command(name="음악정보")
    async def status(self, ctx):
        """음악 정보를 보여줍니다."""
        if ctx.music_state.is_playing():
            song = ctx.music_state.current_song
            await ctx.send(f'재생중인 음악:{song}. 볼륨:{song.volume * 100}% 들어가있는 채널{ctx.voice_client.channel.mention}')
        else:
            await ctx.send('재생하지 않습니다.')

    @commands.command(name="리스트")
    async def playlist(self, ctx):
        """음악 리스트를 보여줍니다."""
        await ctx.send(f'{ctx.music_state.playlist}')

    @commands.command(name="입장")
    @commands.has_permissions(manage_guild=True)
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """봇이 음악 채널에 들어갑니다."""
        if channel is None and not ctx.author.voice:
            raise MusicError('음성 채널이 아니거나 참여할 음성 채널을 지정하지 않았습니다.')

        destination = channel or ctx.author.voice.channel

        if ctx.voice_client:
            await ctx.voice_client.move_to(destination)
        else:
            ctx.music_state.voice_client = await destination.connect()

    @commands.command(name="플레이")
    async def play(self, ctx, *, request: str):
        """음악을 재생합니다."""
        await ctx.message.add_reaction('\N{HOURGLASS}')

        # Create the SongInfo
        song = await SongInfo.create(request, ctx.author, ctx.channel, loop=ctx.bot.loop)

        # Connect to the voice channel if needed
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            await ctx.invoke(self.join)

        # Add the info to the playlist
        try:
            ctx.music_state.playlist.add_song(song)
        except asyncio.QueueFull:
            raise MusicError('재생 목록이 가득 찼습니다. 나중에 다시 시도하십시오.')

        if not ctx.music_state.is_playing():
            # Download the song and play it
            await song.download(ctx.bot.loop)
            await ctx.music_state.play_next_song()
        else:
            # Schedule the song's download
            ctx.bot.loop.create_task(song.download(ctx.bot.loop))
            await ctx.send(f'{song} 재생목록{ctx.music_state.playlist.qsize()}번')

        await ctx.message.remove_reaction('\N{HOURGLASS}', ctx.me)
        await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')

    @play.error
    async def play_error(self, ctx, error):
        """Error handler for the `play ` command."""
        await ctx.message.remove_reaction('\N{HOURGLASS}', ctx.me)
        await ctx.message.add_reaction('\N{CROSS MARK}')

    @commands.command(name="멈추기")
    @commands.has_permissions(manage_guild=True)
    async def pause(self, ctx):
        """음악을 멈춥니다"""
        if ctx.voice_client:
            ctx.voice_client.pause()
        await ctx.send('음악을 잠시 멈춥니다')

    @commands.command(name="재생")
    @commands.has_permissions(manage_guild=True)
    async def resume(self, ctx):
        """멈춘음악을 다시 재생합니다."""
        if ctx.voice_client:
            ctx.voice_client.resume()
        await ctx.send('음악을 다시 재생합니다')

    @commands.command(name="종료")
    @commands.has_permissions(manage_guild=True)
    async def stop(self, ctx):
        """플레이어를 중지하고 재생 목록을 지우고 음성 채널을 떠납니다."""
        await ctx.music_state.stop()
        await ctx.send('음악을 종료하고 채널을 나갑니다')

    @commands.command(name="볼륨")
    async def volume(self, ctx, volume: int = None):
        """볼륨을 설정합니다. 0부터 100까지"""
        if volume < 0 or volume > 100:
            raise MusicError('볼륨 레벨은 0에서 100 사이 여야합니다.')
        ctx.music_state.volume = volume / 100
        await ctx.send(f'볼륨을 {volume}으로 설정했습니다.')

    @commands.command(name="기록삭제")
    async def clear(self, ctx):
        """재생목록을 지웁니다."""
        ctx.music_state.playlist.clear()
        await ctx.send('재생 목록을 삭제합니다.')

    @commands.command(name="스킵")
    async def skip(self, ctx):
        """음악을 스킵합니다."""
        if not ctx.music_state.is_playing():
            raise MusicError('건너 뛸 항목이 없습니다.')

        if ctx.author.id in ctx.music_state.skips:
            raise MusicError(f'{ctx.author.mention} 이미 그 노래를 건너 뛰기로 투표했습니다')

        # Count the vote
        ctx.music_state.skips.add(ctx.author.id)
        await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')

        # Check if the song has to be skipped
        if len(
                ctx.music_state.skips) > ctx.music_state.min_skips or ctx.author == ctx.music_state.current_song.requester:
            ctx.music_state.skips.clear()
            ctx.voice_client.stop()

    @commands.command(hidden=True)
    @commands.has_permissions(manage_guild=True)
    async def minskips(self, ctx, number: int):
        """Sets the minimum number of votes to skip a song.
        Requires the `Manage Guild` permission.
        """
        ctx.music_state.min_skips = number