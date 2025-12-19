import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

from scripts.constants import OPGUILD_ID
from scripts.nations import load_terrain, load

class NationsBot(discord.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}, syncing commands")
        await sync(self)

    async def setup_hook(self) -> None:
        try:
            await self.load_extension("commands.admin")
            await self.load_extension("commands.user")
            logger.info("Loading tile data")
            await load_terrain()
            await load()
        except Exception as e:
            logger.critical(f"Failed to load extensions in setup_hook: {e}")
            await self.close()
bot = NationsBot()

async def sync(bot: commands.Bot) -> None:
    """
    Sync application commands with Discord.
    """
    try:
        await bot.sync_commands(guild_ids=[OPGUILD_ID])
    except Exception as e:
        logger.critical(f"Sync failed: {e}")