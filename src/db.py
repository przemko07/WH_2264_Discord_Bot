import json
import logging
import pathlib
import aiosqlite, json, pathlib, logging
from typing import Dict

log = logging.getLogger("storage")

DB_PATH = pathlib.Path("config.db")

INIT_SQL = """
CREATE TABLE IF NOT EXISTS guild_cfg (
    guild_id            INTEGER PRIMARY KEY,
    new_member_role_id  INTEGER,
    welcome_channel_id  INTEGER,
    listen_ch           TEXT,          -- JSON list[int]
    languages           TEXT           -- JSON {lang: {channel_id, role_id}}
);
"""

_db = None
async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row            # access rows by name
    return _db

async def init_db():
    db = await get_db()
    await db.executescript(INIT_SQL)
    await db.commit()

async def get_cfg(guild_id: int) -> dict | None:
    db = await get_db()
    row = await db.execute_fetchone(
        """
        SELECT new_member_role_id,
               welcome_channel_id,
               listen_ch,
               languages
        FROM   guild_cfg
        WHERE  guild_id = ?
        """,
        (guild_id,)
    )
    if row is None:
        return None
    return {
        "new_member_role_id": row["new_member_role_id"],         # int
        "welcome_channel_id": row["welcome_channel_id"],         # int
        "listen_channels"  : json.loads(row["listen_ch"]),       # list[int]
        "languages"        : json.loads(row["languages"]),       # dict[str,dict]
    }

async def upsert_cfg(guild_id: int, cfg: Dict[str, Any]) -> None:
    """
    Expects `cfg` to have keys:
      new_member_role_id : int
      welcome_channel_id : int
      listen_channels    : list[int]
      languages          : dict[str, dict]
    """
    db = await get_db()
    await db.execute(
        """
        INSERT INTO guild_cfg (
            guild_id, new_member_role_id, welcome_channel_id,
            listen_ch, languages
        )
        VALUES (?,?,?,?,?)
        ON CONFLICT(guild_id) DO UPDATE SET
            new_member_role_id = excluded.new_member_role_id,
            welcome_channel_id = excluded.welcome_channel_id,
            listen_ch          = excluded.listen_ch,
            languages          = excluded.languages
        """,
        (
            guild_id,
            cfg["new_member_role_id"],
            cfg["welcome_channel_id"],
            json.dumps(cfg["listen_channels"], separators=(",", ":")),
            json.dumps(cfg["languages"],      separators=(",", ":")),
        ),
    )
    await db.commit()