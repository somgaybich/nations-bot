from discord import Interaction, Embed
import logging

from scripts.constants import brand_color, LOGGING_CHANNEL_ID
from scripts.botlib import bot

logger = logging.getLogger(__name__)

async def response(interaction: Interaction, title: str, message: str, ephemeral=False, footer=None, view=None):
    """
    Sends a message to the user in the standard format.
    """
    try:
        if footer is not None:
            await interaction.response.send_message(embed=Embed(
            color=brand_color,
            title=title,
            description=message
            ).set_footer(
                text=footer
            ), ephemeral=ephemeral, view=view)
        else:
            await interaction.response.send_message(embed=Embed(
            color=brand_color,
            title=title,
            description=message
            ), ephemeral=ephemeral, view=view)
    except Exception as e:
        logger.error(f"Failed to send response message: {e}")
        raise

async def error(interaction: Interaction, message = ""):
    """
    Used to report general errors. A message can be optionally attached if the nature of the error is known.
    """
    try:
        if message != "":
            await interaction.response.send_message(embed=Embed(
                color=brand_color,
                title="Oops!",
                description=f"There was a problem processing your request! {message}"
            ), ephemeral=True)
        else:
            await interaction.response.send_message(embed=Embed(
                color=brand_color,
                title="Oops!",
                description="There was a problem processing your request! Ping @madaman and she will take care of it as soon as possible."
            ), ephemeral=True)
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")
        raise
    
async def log_info(message = ""):
    try:
        logging_channel = bot.get_channel(LOGGING_CHANNEL_ID)
        logging_channel.send(message, ephemeral=True)
    except Exception as e:
        logger.error(f"Error logging to {logging_channel.name}: {e}")
        raise