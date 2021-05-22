import asyncio
import os
import discord
from discord.ext import commands
from discord.ext.commands import bot
from discord.utils import get
from dotenv import load_dotenv
import youtube_dl

#Loads Vavyt's Discord token into main.py to be called
load_dotenv('TOKEN.env')


#sets the prefix of commands
client = commands.Bot(command_prefix='~')


#Removes "help" command to be reassigned
client.remove_command('help')


#Bot initialization
@client.event
async def on_ready():
    print('{0.user} is online.'.format(client))
    channel = client.get_channel(844326203875000350)
    await channel.send('Online')
    game = discord.Game("Use ~help")
    await client.change_presence(status=discord.Status.idle, activity=game)


@client.command(aliases=['Help'])
async def help(ctx):
    channel = ctx.channel
    await channel.send('```Here are the commands for Vavyt:  \n -------------------------------- \n ~ping  -  pings \n ~WhereIsMyGuineaPig  -  Finds the guinea pig \n ~clear  -  Clears all messages in a channel \n ~join  -  Vavyt joins the voice channel \n ~leave  -  Vavyt leaves the voice channel it is in \n ~play  -  Usage: ~play (Youtube link here). Plays audio from a Youtube link \n ~pause  -  Pauses audio playing in a voice channel  \n ~resume  -  Resumes audio in a voice channel \n ~stop  -  Stops playing audio from Youtube link in a voice channel```')


@client.command(aliases=['Ping'])
async def ping(ctx):
    channel = ctx.channel
    await channel.send('Pong!')


@client.command(aliases=['WhereGP'])
async def WhereIsMyGuineaPig(ctx):
    channel = ctx.channel
    await channel.send('<@!78953526977368064> Here he is!')


@client.command(aliases=['purge'])
async def clear(ctx):  # ctx -> cont
    await ctx.message.delete()  # deletes the message that called the command

    channel = ctx.channel
    await channel.send('Deleting messages. . .')
    async for message in channel.history(limit=200):
        await message.delete()


#Sets up the youtube downloader to prepare to play songs
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename


#Command to join author's voice channel
@client.command(aliases=['Join'])
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

#Command to leave author's voice channel
@client.command(aliases=['Leave'])
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

#plays audio from a youtube link through bot in voice channel
@client.command(aliases=['Play'])
async def play(ctx, url):
    song_there = os.path.isfile("song.mp3")
    try:
        if song_there:
            os.remove("song.mp3")
    except PermissionError:
        await ctx.send("Wait for the current playing music end or use the 'stop' command")
        return
    await ctx.send("Getting everything ready, one moment please . . . ")
    print("Someone wants to play music let me get that ready for them...")
    voice = get(client.voice_clients, guild=ctx.guild)
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, 'song.mp3')
    voice.play(discord.FFmpegPCMAudio("song.mp3"))
    voice.volume = 100
    voice.is_playing()


#Pauses audio being played in voice channel
@client.command(aliases=['Pause'])
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients)
    if voice.is_playing():
        voice.pause()
        ctx.message.send('Paused')


#Resumes paused audio in voice channel
@client.command(aliases=['Resume'])
async def resume(ctx):
  voice = discord.utils.get(client.voice_clients)
  if voice.is_paused():
    voice.resume()
    ctx.message.send('Resuming')


#Stops playing audio in voice channel
@client.command(aliases=['Stop'])
async def stop(ctx):
   voice = discord.utils.get(client.voice_clients)
   voice.stop()
   ctx.message.send('Stopping . . . ')


client.run(os.getenv('DISCORD_TOKEN'))
# https://discordpy.readthedocs.io/en/latest/api.html
#await client.process_commands(message)  # process commands after checking on_message