import asyncio
import discord
from functools import partial
from googletrans import Translator

# ---------------------------------------------------------------------------
# 1) helper that does ONE translation + send
# ---------------------------------------------------------------------------
async def translate_and_send(
        translator: Translator,
        message: discord.Message,
        channel_to_send_id: int,
        dest_lang: str,
) -> None:
    try:
        channel_to_send = message.guild.get_channel(channel_to_send_id)
        if channel_to_send is None:
            return

        trg = await translator.translate(message.content, dest=dest_lang)

        # skip useless translation (same message or same language)
        if trg.src == dest_lang or trg.text == message.content:
            return

        embed = discord.Embed(
            description = f"[🔗]({message.jump_url}) {trg.text}",
            color = discord.Colour.blurple(),
            timestamp = message.created_at,
        )
        embed.set_author(
            name = message.author.display_name,
            icon_url = message.author.display_avatar.url
        )
        await channel_to_send.send(embed = embed)

    except Exception as exc:
        print(f"[error] `translate_and_send` failed (dest_lang: {dest_lang}) -> {exc}")