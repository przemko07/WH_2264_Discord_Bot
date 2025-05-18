import os
import asyncio
import discord
from discord.ext import commands
from discord import ui, ButtonStyle, Embed, Colour
from dotenv import load_dotenv
from googletrans import Translator
import helpers

# ---------- const -----------

NEW_COMMER_ROLE_ID = 1373321252160409610    # Role ID for new commers (receiving this role triggers functions)
BOT_LOG_CH_ID = 1373323014535381034         # Text channel for writing bot logs
WELCOME_CH_ID = 1373323014535381034         # Text channel for welcoming people
LISTEN_CH_ID = [ # Text channel where bot is listening and will be translating automatically
    1373622004636454943, # polish
    1373622033128362004,  # english
    1043495045057228845  # ogólny
]
TRANSLATE_CH_ID = { # Text channel where bot will translate message into
    1373622004636454943: "pl",
    1373622033128362004: "en"
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
    print("[info] called `on_ready`")
    print(f"✅ Logged in as {bot.user} (ID {bot.user.id})")


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    print("[info] called `on_member_update`")

    log_channel = after.guild.get_channel(BOT_LOG_CH_ID)
    if log_channel == None:
        raise RuntimeError("channel == None")  # TODO: XXX: change exceptions to errors (if it crashes my bot)
    await log_channel.send("[info] called `on_member_update`")

    welcome_channel = after.guild.get_channel(WELCOME_CH_ID)
    if welcome_channel == None:
        raise RuntimeError("channel == None")  # TODO: XXX: change exceptions to errors (if it crashes my bot)
    

    # Roles are *lists* that preserve hierarchy order.
    added_roles   = [r for r in after.roles if r not in before.roles]
    removed_roles = [r for r in before.roles if r not in after.roles]

    for role in added_roles:
        if role.id == NEW_COMMER_ROLE_ID:
            await log_channel.send(f"✅ {after.mention} just received **{role.name}**")
            await welcome_channel.send(
                f"hello everyone, we have {after.mention} on #2264 state discord!\r\n" + # 
                f"I will help you choose discord alliance role and discord nickname. This will help everyone understand who yuu are.\r\n" +
                f"[alliance role]: click on alliance icon under this message.\r\n" +
                f"[nickname]: send message on discord chat `/nick \"YOUR IN GAME NICK\"`")
            def receive_reply(msg: discord.Message) -> bool:
                return (
                    msg.author.id == after.id
                    and msg.channel.id == WELCOME_CH_ID
                    and msg.content.lower().strip() == "hello"
                )
            
            try:
                await bot.wait_for("message", check=receive_reply, timeout=5)
            except asyncio.exceptions.TimeoutError:
                # user never replied — optional: handle or ignore
                None
            await welcome_channel.send(":)")
            
@bot.event
async def on_message(msg: discord.Message):
    print("[info] called `on_message`")

    # 0) never re-process the bot's own messages (or any bot's, optional)
    if msg.author.bot:
        return
    
    log_channel = msg.guild.get_channel(BOT_LOG_CH_ID)
    if log_channel == None:
        raise RuntimeError("channel == None")  # TODO: XXX: change exceptions to errors (if it crashes my bot)
    await log_channel.send("[info] called `on_message`")


    print(f"[info] msg.channel.id: {msg.channel.id}")

    # 1) only act in the target channel
    if not msg.channel.id in LISTEN_CH_ID:
        return

    for translate_channel_id in TRANSLATE_CH_ID:
        translate_lang = TRANSLATE_CH_ID[translate_channel_id]
        try:
            # 2) run translation (googletrans auto-detects src language)
            trg = await translator.translate(msg.content, dest=translate_lang)

            # 3) avoid echoing if we are trying to translate to the same language
            if trg.src == translate_lang:
                continue
            # avoid echoing if the message translate to the same thing (for example: HAHAHAHA)
            if trg.text == msg.content:
                continue

            channel = msg.guild.get_channel(translate_channel_id)

            # 4) send back the translated text
            #await channel.send(
            #    f"*[{trg.src.upper()} → {translate_lang}]* {msg.author.display_name} -> {trg.text}"
            #)

            embed = discord.Embed(
                #title = "jump to original",
                #description = f"*[{trg.src.upper()} → {translate_lang}]* {trg.text}",
                description = f"*[{trg.src.upper()} → {translate_lang.upper()}]* [🔗]({msg.jump_url}) {trg.text}",
                color = discord.Colour.blurple(),
                #url = msg.jump_url
            )
            # I dont like thumbnail, it makes whole message taller and not looking good
            #embed.set_thumbnail(url=msg.author.avatar.url)
            embed.set_author(
                name = msg.author.display_name,
                icon_url = msg.author.avatar.url
            )

            # ▸ Button: style=link, label optional, emoji optional
            view = ui.View()
            view.add_item(
                ui.Button(
                    style = ButtonStyle.link,
                    label = "Jump to message",
                    url = msg.jump_url,
                    emoji = "🔗"               # any Unicode emoji or a custom one by ID
                )
            )

            #await channel.send(embed = embed, view = view)
            await channel.send(embed = embed)
            

        except Exception as exc:
            # transient googletrans failures are common—log & bail
            await msg.channel.send(f"⚠️ Translation error: {exc}")
            return

    # 5) hand off to command processor so prefix/slash cmds keep working
    await bot.process_commands(msg) # XXX: consider this, probably not a good idea to use commands on translation channels

@bot.command()
async def ping(ctx: commands.Context):
    print("[info] called `ping`")
    """Replies with Pong!"""
    await ctx.reply("🏓 Pong!", mention_author=False)

# ---------- slash commands ----------
@bot.tree.command(name="hello", description="Say hello back!")
async def hello(interaction: discord.Interaction):
    print("[info] called `hello`")
    channel = interaction.guild.get_channel(BOT_LOG_CH_ID)
    if channel == None: raise RuntimeError("channel == None")
    await channel.send("raised `hello`")

    hello_world_trans = translator.translate("Hello", dest="pl").text

    await interaction.response.send_message(
        f"👋 {hello_world_trans} {interaction.user.mention}!"
    )


# make sure slash commands are pushed on startup
@bot.event
async def setup_hook():
    print("[info] called `setup_hook`")
    await bot.tree.sync()  # global sync; use guild-specific in dev for instant sync

# ---------- start bot ----------
bot.run(TOKEN)
