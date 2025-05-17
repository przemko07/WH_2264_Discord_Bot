import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# ---------- config ----------
load_dotenv()
TOKEN   = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # needed for prefix commands

# ---------- prefix commands ----------
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID {bot.user.id})")

@bot.command()
async def ping(ctx: commands.Context):
    """Replies with Pong!"""
    await ctx.reply("🏓 Pong!", mention_author=False)

# ---------- slash commands ----------
@bot.tree.command(name="hello", description="Say hello back!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"👋 Hey {interaction.user.mention}!"
    )

# make sure slash commands are pushed on startup
@bot.event
async def setup_hook():
    await bot.tree.sync()  # global sync; use guild-specific in dev for instant sync

# ---------- kick it off ----------
bot.run(TOKEN)
