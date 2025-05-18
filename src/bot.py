import os
import asyncio
import discord
from discord.ext import commands
from discord import ui, ButtonStyle, Embed, Colour
from dotenv import load_dotenv
from googletrans import Translator
import helpers

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
]
TRANSLATE_CH_ID = { # Text channel where bot will translate message into
    1373665044663107676: "en", # english
    1373665186178928702: "ru", # russian
    1373665158353780866: "pl", # polish
    1373665214565847303: "ko", # korean
}

# ---------- config ----------
load_dotenv()
TOKEN   = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True          # needed for prefix commands
intents.members = True                  # lets us receive member-update events

translator = Translator()               # google translator for multi languages

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

    # loop over all channels I need to translate into, and translate into them
    for translate_channel_id in TRANSLATE_CH_ID:
        translate_lang = TRANSLATE_CH_ID[translate_channel_id]
        try:
            print(f"[info] translating user message into {translate_lang}")

            # run translation (googletrans auto-detects src language)
            trg = await translator.translate(msg.content, dest=translate_lang)
            print(f"[info] translated succesfully from language {trg.src}")

            # avoid echoing if we are trying to translate to the same language
            if trg.src == translate_lang:
                continue
            # avoid echoing if the message translate to the same thing (for example: HAHAHAHA)
            if trg.text == msg.content:
                continue

            channel = msg.guild.get_channel(translate_channel_id)


            # 4) send back the translated text
            #await channel.send(
            #    f"*[{trg.src.upper()} → {translate_lang.upper()}]* [🔗]({msg.jump_url}) {trg.text}"
            #)

            embed = discord.Embed(
                #title = "jump to original",
                #description = f"*[{trg.src.upper()} → {translate_lang}]* {trg.text}",
                #description = f"[🔗]({msg.jump_url}) *[{trg.src.upper()} → {translate_lang.upper()}]*  {trg.text}",
                description = f"[🔗]({msg.jump_url}) {trg.text}",
                color = discord.Colour.blurple(),
                #url = msg.jump_url
            )
            # XXX: I dont like thumbnail, it makes whole message taller and not looking good
            #embed.set_thumbnail(url=msg.author.avatar.url)
            embed.set_author(
                name = msg.author.display_name,
                icon_url = msg.author.avatar.url
            )

            await channel.send(embed = embed)
        except Exception as exc:
            # transient googletrans failures are common—log & bail
            print(f"[error] Translation error: {exc}")
            continue

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
