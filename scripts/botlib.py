import logging
import discord
import time

logger = logging.getLogger(__name__)

from scripts.constants import OPGUILD_ID

class NationsBot(discord.Bot):
    def __init__(self, **kwargs):
        kwargs.setdefault("intents", discord.Intents.default())
        super().__init__(**kwargs)

    async def on_ready(self):
        timer = time.perf_counter()
        self.load_extension("commands.admin")
        self.load_extension("commands.user")
        await sync(self)
        logger.debug(f"Took {(timer / 1000000):.2f}ms to set up commands")
        logger.info("Setup complete!")

bot = NationsBot()

async def sync(bot: NationsBot) -> None:
    """
    Sync application commands with Discord.
    """
    logger.info("Syncing commands")
    await bot.sync_commands(guild_ids=[OPGUILD_ID])