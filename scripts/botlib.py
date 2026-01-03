import logging
import discord
import time
from datetime import datetime, timezone
from discord.ext import tasks

from scripts.nations import tick
from scripts.database import get_db

logger = logging.getLogger(__name__)

from scripts.constants import OPGUILD_ID

class NationsBot(discord.Bot):
    def __init__(self, **kwargs):
        kwargs.setdefault("intents", discord.Intents.default())
        self.db_commit.start()
        self.tick.start()
        super().__init__(**kwargs)

    async def on_ready(self):
        timer = time.perf_counter()
        self.load_extension("commands.admin")
        self.load_extension("commands.user")
        await sync(self)
        logger.debug(f"Took {(timer / 1000000):.2f}ms to set up commands")
        logger.info("Setup complete!")

    @tasks.loop(minutes=5)
    async def db_commit(self):
        logger.info("Committing database...")
        try:
            await get_db().commit()
            logger.info("Committed all database changes")
        except Exception as e:
            logger.error(f"Unable to commit database: {e}")
            raise
    
    @tasks.loop(hours=1)
    async def tick(self):
        if datetime.now(timezone.utc).hour == 0:
            try:
                await tick()
            except Exception as e:
                logger.error(f"Failed to execute game tick: {e}")
                raise

bot = NationsBot()

async def sync(bot: NationsBot) -> None:
    """
    Sync application commands with Discord.
    """
    logger.info("Syncing commands")
    await bot.sync_commands(guild_ids=[OPGUILD_ID])