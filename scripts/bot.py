import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

# 0: spring, 1: summer, 2: autumn, 3: winter
current_season = 0

brand_color = discord.Color(16417064)

OPGUILD_ID = 1324918248638124114
LOGGING_CHANNEL_ID = 123456789012345678

intents = discord.Intents.default()
class NationsBot(commands.Bot):
    async def setup_hook(self) -> None:
        try:
            await self.load_extension("commands.admin")
            logger.info("Loaded admin extension")
            await self.load_extension("commands.user")
            logger.info("Loaded user extension")
        except Exception as e:
            logger.critical(f"Failed to load extensions in setup_hook: {e}")
            await self.close()
            return
bot = NationsBot(command_prefix="!", intents=intents)

async def sync(bot: commands.Bot) -> None:
    """
    Sync application commands with Discord.
    """
    try:
        opguild = bot.get_guild(OPGUILD_ID)
        commands = await bot.tree.sync(guild=opguild)
        logger.info(f"Commands synced: {[c.name for c in commands]}")
    except Exception as e:
        logger.criterror(f"Sync failed: {e}")