import traceback
import logging
import asyncio
import json

import discord
from discord import Embed, ApplicationContext

from scripts.nations import tick, nation_list
from scripts.ui import ConfirmView
from scripts.constants import brand_color
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

    @discord.slash_command(description="Force a game tick.")
    async def tick(self, ctx: ApplicationContext):
        confirm_future = asyncio.Future()
        await ctx.interaction.response.send_message(embed=Embed(
            color=brand_color,
            title="Are you sure?",
            description="Forcing a tick at the wrong time may invalidate nation data."
        ), view=ConfirmView(confirm_future))
        message = await ctx.interaction.original_response()
        
        result = await confirm_future
        if result == "No" or result is None:
            await message.edit(embed=Embed(
                color=brand_color,
                title="Cancelled",
                description="Game tick was cancelled or timed out."
            ), view=None)
            return
        
        try:
            await tick()
            await message.edit(embed=Embed(
                color=brand_color,
                title="Success!",
                description="Game tick processed."
            ), view=None)
            return
        except Exception as e:
            await message.edit(embed=Embed(
                color=brand_color,
                title="Oops!",
                description="There was an issue executing the game tick."
            ), view=None)
            logger.error(f"Couldn't execute game tick: {e}")
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