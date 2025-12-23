import discord
from discord import ApplicationContext
import traceback
import logging

from scripts.botlib import sync

logger = logging.getLogger(__name__)

class AdminCog(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    async def cog_check(self, ctx: ApplicationContext) -> bool:
        return ctx.interaction.user.id == 247164420273209345
    
    @discord.slash_command(description="Reload a bot extension.")
    async def reload_extension(self, ctx: ApplicationContext, extension: str):
        try:
            self.bot.reload_extension(extension)
            logger.info(f"Reloaded extension {extension}")
            await ctx.interaction.response.send_message(f"Reloaded {extension}", ephemeral=True)
            await sync(self.bot)
        except Exception as e:
            await ctx.interaction.response.send_message(f"Error reloading {extension}:\n```\n{traceback.format_exc()}\n```", ephemeral=True)
            logger.error(f"Failed to reload extension {extension}: {e}")
            raise

def setup(bot: discord.Bot):
    try:
        logger.info("Registering admin cog")
        bot.add_cog(AdminCog(bot))
        logger.info("Registered admin cog")
    except Exception as e:
        logger.critical(f"Failed to load admin cog: {e}")
        bot.close()
        raise