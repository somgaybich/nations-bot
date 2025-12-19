import discord
from discord.ext import commands
import traceback
import logging

from scripts.bot import sync, NationsBot, OPGUILD_ID
from scripts.response import response
from scripts.map import render_snapshot

logger = logging.getLogger(__name__)

class AdminCog(commands.Cog):
    def __init__(self, bot: NationsBot):
        self.bot = bot

    async def cog_check(self, ctx: discord.ApplicationContext) -> bool:
        return ctx.interaction.user.id == 247164420273209345
    
    @discord.slash_command(description="Reload a bot extension.", guild_ids=[OPGUILD_ID])
    async def reload_extension(self, interaction: discord.Interaction, extension: str):
        try:
            await self.bot.reload_extension(extension)
            logger.info(f"Reloaded extension {extension}")
            await interaction.response.send_message(f"Reloaded {extension}", ephemeral=True)
            await sync(self.bot)
        except Exception as e:
            await interaction.response.send_message(f"Error reloading {extension}:\n```\n{traceback.format_exc()}\n```", ephemeral=True)
            logger.error(f"Failed to reload extension {extension}: {e}")

async def setup(bot: commands.Bot):
    try:
        cog = AdminCog(bot)
        await bot.add_cog(cog)
    except Exception as e:
        logger.critical(f"Failed to load admin cog: {e}")
        await bot.close()
        return