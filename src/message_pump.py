import asyncio
import discord
from discord.ext import commands
from datetime import datetime
from functools import partial
from googletrans import Translator

#  alliance_key (str) -> list[tuple[datetime, coroutine]]
#  we store the *send coroutine* so the writer can just await it later.
_MESSAGE_BUFFER: dict[str, list[tuple[datetime, asyncio.Future]]] = defaultdict(list)
_BUFFER_LOCK = asyncio.Lock()

def run_writer_loop(bot: commands.Bot):
    bot.loop.create_task(_writer_loop())     # ← starts background flusher

async def queue_message (alliance: str, coro: asyncio.Future) -> None:
    """
    Queue message onto message list
    alliance  - key (e.g. language code, channel name, your 'alliance')
    coro      - coroutine that, when awaited, sends the Discord message
    """

    global FLUSH_INTERVAL
    global _BUFFER_LOCK
    global _MESSAGE_BUFFER

    async with _BUFFER_LOCK:
        _MESSAGE_BUFFER[alliance].append((datetime.now(), coro))

async def translate_and_send(
        message: discord.Message,
        channel_to_send_id: int,
        dest_lang: str) -> None:
    """
    Translates a Discord message and sends it to the specified channel.

    Parameters
    ----------
    message : discord.Message
        The Discord message to be translated.
    channel_to_send_id : int
        The ID of the channel where the translated message will be sent.
    dest_lang : str
        The target language code (e.g., 'en', 'es', 'fr').

    Returns
    -------
    None
        This function does not return a value.
    """

    global translator
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
            color = discord.Colour.blurple()
        )
        embed.set_author(
            name = message.author.display_name,
            icon_url = message.author.avatar.url
        )
        await channel_to_send.send(embed = embed)

    except Exception as exc:
        print(f"[error] `translate_and_send` failed (dest_lang: {dest_lang}) -> {exc}")





async def _writer_loop():
    """
    Periodically flush the buffered messages in timestamp order,
    per alliance bucket.
    """
    while True:
        await asyncio.sleep(FLUSH_INTERVAL)

        async with _BUFFER_LOCK:
            # copy → clear under lock, then send outside to keep contention low
            buckets = {
                k: sorted(v, key=lambda t: t[0])  # sort by timestamp
                for k, v in _MESSAGE_BUFFER.items()
            }
            _MESSAGE_BUFFER.clear()

        # send outside the lock
        for alliance, items in buckets.items():
            for _ts, send_coro in items:
                try:
                    await send_coro
                except Exception as exc:
                    print(f"[error] send failed for {alliance}: {exc}")