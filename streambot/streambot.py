import discord
import copy
import video
from youtube import getTitlesForSearchString
from youtube import getAllVideosFromSearch
from discord.ext import commands
from discord.voice_client import VoiceClient
import asyncio
from heapq import heappop, heappush, heapify
from queue import PriorityQueue
from downloader import Downloader

# client = discord.Client()
client = commands.Bot(command_prefix="!")

votingTag = 0

heap = []
heapify(heap)
userVoteMap = {}


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.command()
async def hello(ctx):
    print("HELLO!")
    await ctx.send('Hello')

@client.command()
async def ytsearch(ctx, phrase):
    await ctx.send(getTitlesForSearchString(phrase))

async def process_song_queue(ctx):
    def after_download(d):
        if tup != None : heappush(heap, tup)
        ctx.bot.loop.create_task(process_song_queue(ctx))

    downloader = Downloader("./vidpath", after_download)
    tup = None
    if len(heap) != 0:
        ## Pop off queue
        tup = heappop(heap)
        video = tup[1]
        ## Check if the song is already downloaded. If so, get the filename
        ## by title
        if (video.id not in downloader.get_downloaded_urls()):
            downloader.download_video(video.url)
        else:
            filename = "{}-{}".format(video.video_name, video.id)
            await play_local(ctx, filename)


async def play_local(ctx, filename):
    async def after_song(error):
        ctx.bot.loop.create_task(process_song_queue(ctx))

    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filename))
    ctx.voice_client.play(source, after=after_song)

    await ctx.send("Now playing file {}".format(filename))

@client.command()
async def pause(ctx):
    if (ctx.voice.is_playing()): ctx.voice_client.pause()

@client.command()
async def resume(ctx):
    if (ctx.voice.is_paused()): ctx.voice_client.resume()

@client.command()
async def joinvc(ctx, *, channel_name: discord.VoiceChannel):
    try:
        if ctx.voice_client is not None:
            ctx.bot.loop.create_task(process_song_queue(ctx))
            return await ctx.voice_client.move_to(channel_name)

        await channel_name.connect()
        ctx.bot.loop.create_task(process_song_queue(ctx))
    except:
        print("Channel not found!!!")

@client.command()
async def leavevc(ctx):
    await ctx.voice_client.disconnect()

@client.command()
async def add(ctx, numberResult, searchPhrase):
    global heap
    global votingTag
    # Should be in format of !add2q $numberResult $searchPhrase
    # E.g. !add2q 1 who are you 
    await ctx.send("Adding " + searchPhrase + " to the queue with voting tag #" + str(votingTag) + ".")
    vid = getAllVideosFromSearch(searchPhrase, votingTag)[0]
    heappush(heap, (vid.num_votes(), vid))
    votingTag += 1

@client.command()
async def show(ctx):
    finalStr = ""
    temp = copy.deepcopy(heap)
    tmpArr = []
    while len(temp) != 0:
        tmpArr.append(heappop(temp))

    tmpArr.reverse()
    for item in tmpArr:
        finalStr += str(item[0]) + " votes: " + item[1].video_name + " " + " with voting tag #" + str(item[1].id) + '\n'
    await ctx.send(finalStr)

@client.command()
async def upvote(ctx, votedTag):
    await abstract_vote("U", str(ctx.author), votedTag, ctx)

@client.command()
async def downvote(ctx, votedTag):
    await abstract_vote("D", str(ctx.author), votedTag, ctx)

@client.command()
async def remvote(ctx, votedTag):
    await abstract_vote("R", str(ctx.author), votedTag, ctx)

#Pass in U for upvote, R for remove, and D for downvote
async def abstract_vote(typeOfVote, username, votedTag, context):
    global heap
    temp = copy.deepcopy(heap)
    matchedItem = ""
    tempHeap = []

    for item in temp:
        currentVotingTag = item[1].id
        currentVideo = item[1]
        if int(currentVotingTag) == int(votedTag):
            if typeOfVote == "U":
                currentVideo.upvote(username)
                await context.send(username + " upvoted: " + currentVideo.video_name + ", which is now at " + str(currentVideo.num_votes()) + " votes.")
            elif typeOfVote == "D":
                currentVideo.downvote(username)
                await context.send(username + " downvoted: " + currentVideo.video_name + ", which is now at " + str(currentVideo.num_votes()) + " votes.")
            else:
                currentVideo.remove_vote(username)
                await context.send(username + " removed their vote from: " + currentVideo.video_name + ", which is now at " + str(currentVideo.num_votes()) + " votes.")

            heappush(tempHeap, (currentVideo.num_votes(), currentVideo))
        else:
            heappush(tempHeap, item)
    heap = tempHeap

tokenFile = open("token.txt","r+")
token = tokenFile.read()
client.run(token)
tokenFile.close()