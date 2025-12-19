import discord
from discord import Interaction
import traceback
import logging

from scripts.bot import sync

logger = logging.getLogger(__name__)

class AdminCog(discord.Cog):
    def __init__(self, bot: discord.bot):
        self.bot = bot

    async def cog_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == 247164420273209345
    
    @discord.slash_command(description="Reload a bot extension.")
    async def reload_extension(self, interaction: discord.Interaction, extension: str):
        try:
            await self.bot.reload_extension(extension)
            logger.info(f"Reloaded extension {extension}")
            await interaction.response.send_message(f"Reloaded {extension}", ephemeral=True)
            await sync(self.bot)
        except Exception as e:
            await interaction.response.send_message(f"Error reloading {extension}:\n```\n{traceback.format_exc()}\n```", ephemeral=True)
            logger.error(f"Failed to reload extension {extension}: {e}")

async def setup(bot: discord.Bot):
    try:
        logger.debug("Registering admin cog")
        await bot.add_cog(AdminCog(bot))
        logger.debug("Registered admin cog")
    except Exception as e:
        logger.critical(f"Failed to load admin cog: {e}")
        await bot.close()
        return