import os
import asyncio
import discord
from discord.ext import commands
from discord import ui, ButtonStyle, Embed, Colour
from dotenv import load_dotenv
from googletrans import Translator
from helpers import *

# ---------- const -----------

# My test server

NEW_COMMER_ROLE_ID = 1373321252160409610    # Role ID for new commers (receiving this role triggers functions)
WELCOME_CH_ID = 1373323014535381034         # Text channel for welcoming people
LISTEN_CH_ID = [ # Text channel where bot is listening and will be translating automatically
    1373622004636454943, # polish
    1373622033128362004, # english
    1043495045057228845  # ogólny
]
TRANSLATE_CH_ID = { # Text channel where bot will translate message into
    1373622004636454943: "pl",
    1373622033128362004: "en"
}

# 2264 server

NEW_COMMER_ROLE_ID = 1372468202965172234    # Role ID for Member (receive when no other role is assigned)
WELCOME_CH_ID = 1372276435296981218         # Text channel for welcoming people
LISTEN_CH_ID = [ # Text channel where bot is listening and will be translating automatically
    1372282999655370833, # lobby
    1373665044663107676, # english
    1373665186178928702, # russian
    1373665158353780866, # polish
    1373665214565847303, # korean
    1373678224546074675, # turkey
    1373678201867337739, # german
    1373678238404186262, # arabic
    1377198864741699654, # chinese
    1377199517631516722, # spanish
]
TRANSLATE_CH_ID = { # Text channel where bot will translate message into
    1373665044663107676: "en", # english
    1373665186178928702: "ru", # russian
    1373665158353780866: "pl", # polish
    1373665214565847303: "ko", # korean
    1373678224546074675: "tr", # turkey
    1373678201867337739: "de", # german
    1373678238404186262: "ar", # arabic
    1377198864741699654: "zh-TW", # chinese traditional
    1377199517631516722: "es", # spanish
}

# ---------- config ----------
load_dotenv()
TOKEN   = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True          # needed for prefix commands
intents.members = True                  # lets us receive member-update events

translator = Translator()               # google translator for multi languages
print_available_languages()

# ---------- prefix commands ----------
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"[info] Called `on_ready`")
    print(f"[info] Logged in as {bot.user} (ID {bot.user.id})")


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    print("[info] Called `on_member_update`")

    welcome_channel = after.guild.get_channel(WELCOME_CH_ID)
    if welcome_channel == None:
        raise RuntimeError("channel == None")  # TODO: XXX: change exceptions to errors (if it crashes my bot)    

    # Roles are *lists* that preserve hierarchy order.
    added_roles   = [r for r in after.roles if r not in before.roles]
    removed_roles = [r for r in before.roles if r not in after.roles]

    for role in added_roles:
        if role.id == NEW_COMMER_ROLE_ID:
            await welcome_channel.send(
                f"hello everyone, we have {after.mention} on #2264 state discord!\r\n" + # 
                f"I will help you choose discord alliance role and discord nickname. This will help everyone understand who yuu are.\r\n" +
                f"[alliance role]: click on alliance icon under this message.\r\n" +
                f"[nickname]: send message on discord chat `/nick \"YOUR IN GAME NICK\"`")
            
@bot.event
async def on_message(msg: discord.Message):
    print("[info] Called `on_message`")

    # never re-process the bot's own messages (or any bot's, optional)
    if msg.author.bot:
        return

    print(f"[info] msg.channel.id: {msg.channel.id}")
    

    # only act in the target channel
    if not msg.channel.id in LISTEN_CH_ID:
        print(f"NOT translating on channel ID {msg.channel.id}")
        return

    # spawn a task for every language/channel pair
    tasks = [
        asyncio.create_task(
            translate_and_send(translator, msg, ch_id, lang)
        )
        for ch_id, lang in TRANSLATE_CH_ID.items()
    ]

    # wait for *all* of them before we exit the handler
    # (collect exceptions inside translate_and_send, so gather won’t raise)
    await asyncio.gather(*tasks)

    # hand off to command processor so prefix/slash cmds keep working
    await bot.process_commands(msg)


# ---------- slash commands ----------
@bot.tree.command(name="on2264", description="Test command for #2264 state!")
async def on2264(interaction: discord.Interaction):
    print("[info] Called `hello`")

    await interaction.response.send_message(
        f"👋 {interaction.user.mention} called `on2264`"
    )


# make sure slash commands are pushed on startup
@bot.event
async def setup_hook():
    print("[info] called `setup_hook`")
    await bot.tree.sync()  # global sync; use guild-specific in dev for instant sync

# ---------- start bot ----------
bot.run(TOKEN)
