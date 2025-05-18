import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import helpers

# ---------- const -----------

NEW_COMMER_ROLE_ID = 1373321252160409610    # Role ID for new commers (receiving this role triggers functions)
BOT_LOG_CH_ID = 1373323014535381034         # Text channel for writing bot logs
WELCOME_CH_ID = 1373323014535381034         # Text channel for welcoming people



# ---------- config ----------
load_dotenv()
TOKEN   = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True          # needed for prefix commands
intents.members = True                  # lets us receive member-update events

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
            await welcome_channel.send(f"{after.mention} hello new-commer on #2264 state discord!")
            def receive_reply(msg: discord.Message) -> bool:
                return (
                    msg.author.id == after.id
                    and msg.channel.id == WELCOME_CH_ID
                    and msg.content.lower().strip() == "hello"
                )
            
            try:
                await bot.wait_for("message", check=receive_reply, timeout=5)
            except TimeoutError:
                # user never replied — optional: handle or ignore
                None
            await welcome_channel.send(":)")
            

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

    await interaction.response.send_message(
        f"👋 Hey {interaction.user.mention}!"
    )


# make sure slash commands are pushed on startup
@bot.event
async def setup_hook():
    print("[info] called `setup_hook`")
    await bot.tree.sync()  # global sync; use guild-specific in dev for instant sync

# ---------- start bot ----------
bot.run(TOKEN)
