import os
import asyncio
import discord
import logging
import pathlib
from discord.ext import commands
from discord import ui, ButtonStyle, Embed, Colour
from dotenv import load_dotenv
from googletrans import Translator
from helpers import *
from log import *
from db import *

# ---------- const -----------
NEW_COMMER_ROLE_ID  = 1372468202965172234   # Role ID for Member (receive when no other role is assigned)
WELCOME_CH_ID       = 1372276435296981218   # Text channel for welcoming people
EN_ROLE_ID          = 1373689070391394525   # Role ID for listening to english
PL_ROLE_ID          = 1373689170609967237   # Role ID for listening to polish

ROLE_ID_2_CHANNEL_ID = {
    1373689070391394525: 1373665044663107676, # english
    1373689170609967237: 1373665158353780866, # polish
}


LISTEN_CH_ID = [ # Text channel where bot is listening and will be translating automatically
    1372282999655370833, # lobby
    1373665044663107676, # english
    1373665186178928702, # russian
    1373665158353780866, # polish
    1373665214565847303, # korean
    1373678224546074675, # turkey
    1373678201867337739, # german
    1373678238404186262, # arabic
]
TRANSLATE_CH_ID = { # Text channel where bot will translate message into
    1373665044663107676: "en", # english
    1373665186178928702: "ru", # russian
    1373665158353780866: "pl", # polish
    1373665214565847303: "ko", # korean
    1373678224546074675: "tr", # turkey
    1373678201867337739: "de", # german
    1373678238404186262: "ar", # arabic
}

# ---------- config ----------

config_log()
log = logging.getLogger("bot-2264")

init_db()

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
    log.info(f"Called `on_ready`")
    log.info(f"Logged in as {bot.user} (ID {bot.user.id})")


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    log.info("Called `on_member_update`")

    cfg = await get_cfg(after.guild.id) # None if not configured yet
    if not cfg:
        log.warning(f"Guild {after.guild.id} not configured; skipping")
        return

    welcome_channel = after.guild.get_channel(cfg["welcome_channel_id"])
    if welcome_channel == None:
        log.warning(f"Could not find channel \"{cfg["welcome_channel_id"]}\"")
        return

    # Roles are *lists* that preserve hierarchy order.
    added_roles   = [r for r in after.roles if r not in before.roles]
    removed_roles = [r for r in before.roles if r not in after.roles]

    for role in added_roles:
        if role.id == cfg["new_member_role_id"]:
            await welcome_channel.send(
                f"Hello everyone, we have {after.mention} with us now!\r\n" + # 
                f"Please choose alliance role and discord nickname, this will help everyone understand who yuu are :eyes:\r\n" +
                f"`[alliance role]` click on alliance icon under this message.\r\n" +
                f"`[   nickname  ]` send message on discord chat `/nick \"YOUR IN-GAME NICK\"`")
            

    #log.info(f"Changing all language channels (count: {len(ROLE_ID_2_CHANNEL_ID)}) visibility for member \"{after.name}\"")
    ## change permissions on specific selected language
    #current_role_ids = { r.id for r in after.roles }
    #
    ## iterate once over every (role, channel) pair we manage
    #for role_id, ch_id in ROLE_ID_2_CHANNEL_ID.items():
    #    channel = after.guild.get_channel(ch_id)
    #    if channel is None: # bad ID or no access
    #        continue
    #
    #    log.info(f"Changing channel (name: {channel.name})...")
    #    if role_id in current_role_ids:
    #        log.info(f"Changing channel (name: {channel.name}) to VISIBLE")
    #        # Member HAS this language role → make sure they can see the channel
    #        await channel.set_permissions(after, view_channel = True)
    #    else:
    #        log.info(f"Changing channel (name: {channel.name}) to HIDDEN")
    #        # Member does NOT have it → revert to channel default (hidden)
    #        await channel.set_permissions(after, view_channel = False)

@bot.event
async def on_message(msg: discord.Message):
    log.info(f"Called `on_message` on channel \"{msg.channel.name}\"")

    # never re-process the bot's own messages (or any bot's, optional)
    if msg.author.bot:
        return    
    
    cfg = await get_cfg(msg.guild.id) # None if not configured yet
    if not cfg:
        log.warning("Guild %s not configured; skipping", msg.guild.id)
        return

    # only act in the target channel
    if msg.channel.id not in cfg["listen_channels"]:
        log.info(f'Channel {msg.channel.name} is not a listen channel; skipping')
        return

    # spawn a task for every language/channel pair
    tasks = [
        asyncio.create_task(
            translate_and_send(translator, log, msg, lang_cfg["channel_id"], lang_code)
        )
        for lang_code, lang_cfg in cfg["languages"].items()
    ]

    # wait for *all* of them before we exit the handler
    # (collect exceptions inside translate_and_send, so gather won’t raise)
    await asyncio.gather(*tasks)

    # hand off to command processor so prefix/slash cmds keep working
    await bot.process_commands(msg)


# ---------- slash commands ----------
@bot.tree.command(name="ping2264", description="Test command for #2264 state!")
async def ping2264(interaction: discord.Interaction):
    log.info("Called `ping2264`")

    await interaction.response.send_message(
        f"{interaction.user.mention} called `ping2264` :eyes:"
    )

@bot.tree.command(name = "set_new_member_role", description = "Sets role for ne members who will receive welcome message")
async def set_newcomer_role(interaction: discord.Interaction, role: discord.Role,):
    log.info("Caled `set_newcomer_role`")

    cfg = await get_cfg(interaction.guild_id) or {
        "listen_channels": [],
        "languages": {},
    }
    cfg["new_member_role_id"] = role.id
    await upsert_cfg(interaction.guild_id, cfg)
    await interaction.response.send_message(
        f"✅ New-comer role set to {role.mention}", ephemeral=True
    )


# make sure slash commands are pushed on startup
@bot.event
async def setup_hook():
    log.info("called `setup_hook`")
    await bot.tree.sync()  # global sync; use guild-specific in dev for instant sync

# ---------- start bot ----------
bot.run(TOKEN)

