import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

from scripts.constants import OPGUILD_ID
from scripts.nations import load_terrain, load

class NationsBot(discord.Bot):
    def __init__(self, **kwargs):
        kwargs.setdefault("intents", discord.Intents.default())
        super().__init__(**kwargs)

    async def on_ready(self):
        logger.info("Starting setup proccess...")
        self.load_extension("commands.admin")
        self.load_extension("commands.user")
        logger.info("Loading tile data")
        load_terrain()
        load()
        logger.info(f"Logged in as {self.user}, syncing commands")
        await sync(self)
bot = NationsBot()

async def sync(bot: commands.Bot) -> None:
    """
    Sync application commands with Discord.
    """
    await bot.sync_commands(guild_ids=[OPGUILD_ID])