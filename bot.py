import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import sys
import ollama
import asyncio

members = [] #hold member list    

systemMessage = open("sysPrompt.txt",encoding='utf8').read()
memories = open("memories.txt",encoding='utf8')

line = memories.read()
if (len(line)>0):
    systemMessage+=f"this is summary of your last chat session \n{line}"  # Handle open memories file in read or overwrite mode
memories.close()
memories = open("memories.txt","a")         # Change back mode to overwrite


# print(systemMessage)   #DEBUG---------------------------
model = "gemma4:e2b "  # model used

messages= [ 
    {"role":"system", "content": (systemMessage)}         # to contain the messages
]
memory = [
    
]                                             # to contain chat history without system prompt
tools=[{
    'type': 'function',
    'function': {
    'name': 'warn',
    'description': 'to warn member when they say the word "shit"',
    'parameters': {
        'type': 'object',
        'required': ['message'],
    },
    },
},
]


load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename="discordbot.log",encoding='utf-8',mode='w')
intents = discord.Intents.default()
intents.message_content = True     # Set intents to true in code
intents.members = True
intents.presences = True

# ---------------------------------------------------
bot = commands.Bot(command_prefix="!", intents=intents) # set prefix so every bot command will start with "!" (in discord server)
# ---------------------------------------------------

# ON BOT READY --------------------------
@bot.event
async def on_ready(): 
    #// LIST MEMBERS IN GUILD
    for guild in bot.guilds:
        for member in guild.members:
            members.append(member.id)

    print(f"HI, I'am {bot.user.name}")


# BOT COMMAND FUNCTION -----------------------
@bot.command()  
async def list_servers(ctx):
    for guild in bot.guilds:
        await ctx.send(f"{ctx.author.mention} bot joined in {guild}")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command()
async def mention(ctx):
    for i in range (len(members)):
        await ctx.send(f"{i} - {ctx.guild.get_member(members[i]).display_name}")
    
    def check(m):
        return (m.author == ctx.author and m.channel == ctx.channel)
    
    try:
        await ctx.send("choose which member you wanna mention: ")
        message = await bot.wait_for("message",timeout=15.0,check=check)
    except asyncio.TimeoutError:
        await ctx.send("time ran out")
    else:
        mentioned = str(members[int(message.content)])
        member = ctx.guild.get_member(members[int(message.content)])
        await ctx.send(f"HELLO {member.mention}")

            
# ON EVENT FUNCTION ----------------------------       
@bot.event
async def on_member_join(member):
    await member.send(f"welcome to the server {member.name}")

@bot.event
async def on_message(message):
    if message.content.lower() == "/exit":
        if len(memory)>0:
            memory.append({'role': 'system','content': "you are being shutted down, now summarize this chat for you so you can easily remember this chat session in the next session!. remember important points (names, event, story, name, specific topics), also give your opinion for each member you interacted with so you will remember how to get the conversation going with them, make sure in the next session you remember you have been shutted down before."})
            summary = ollama.chat(model=model, messages=memory)
            print(summary["message"]["content"])
            memories.write("\n"+summary["message"]["content"]+ f"\nabove is memories created at {message.created_at} -- END OF MEMORY --")
            memories.close()
            await bot.close()
            return
        else:
            memories.close()
            await bot.close()


    if not message.content.startswith(bot.command_prefix):
        if message.author == bot.user:return                              # Do not response the bot message
        
        messages.append({'role': message.author.display_name,'content':message.content})     # append user input to the message sent
        memory.append({'role': message.author.display_name,'content':message.content})
        # message.author.username+" say: "+
        response = ollama.chat(model=model, messages=messages)#,options={"temperature": 1.5}

        messages.append({'role': 'assistant','content':response["message"]["content"]}) # append bot response
        memory.append({'role': 'assistant','content':response["message"]["content"]})
        
        for i in messages:          #debug to print convo
            print(i)
        await message.channel.send(response["message"]["content"])

        # Crucial line: allows the bot to process other commands
    await bot.process_commands(message)


# ----- ON CALL FUNCTION -----
async def warn(message):
    await message.channel.send(f"dont say that {message.author.mention}")


bot.run(token=token,log_handler=handler,log_level=logging.DEBUG) # RUN BOT