from discord import Interaction, Embed, Webhook
import logging

from game.data.constants import brand_color, LOGGING_CHANNEL_ID, backup_msg
from scripts.botlib import bot

logger = logging.getLogger(__name__)

async def followup_response(followup: Webhook, title: str, message: str, 
                            ephemeral=False, footer=None, view=None):
    """
    Sends a followup message through the given webhook in the standard format.
    """
    try:
        embed = Embed(
            color=brand_color,
            title=title,
            description=message
        )
        if footer is not None:
            embed.set_footer(footer)

        if view is not None:
            await followup.send(embed=embed, view=view, ephemeral=ephemeral)
        else:
            await followup.send(embed=embed, ephemeral=ephemeral)
    except Exception as e:
        logger.error(f"Failed to send response message: {e}")
        raise

async def interaction_response(interaction: Interaction, title: str, 
                               message: str, ephemeral=False, footer=None, 
                               view=None):
    """
    Sends a message responding to the given interaction in the standard format.
    """
    try:
        embed = Embed(
            color=brand_color,
            title=title,
            description=message
            )
        
        if footer is not None:
            embed.set_footer(footer)
        
        if view is not None:
            await interaction.response.send_message(embed=embed, view=view, 
                                                    ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, 
                                                    ephemeral=ephemeral)

    except Exception as e:
        logger.error(f"Failed to send response message: {e}")
        raise

async def followup_error(followup: Webhook, message = ""):
    """
    Used to report errors in followup responses. A message can be optionally 
    attached if the nature of the error is known. Because followups can only 
    send a new message, the original should be deleted.
    """
    try:
        await followup.send(embed=Embed(
            color=brand_color,
            title="Oops!",
            description=message if message != "" else backup_msg
        ), ephemeral=True)
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")
        raise

async def interacton_error(interaction: Interaction, message = ""):
    """
    Used to report general errors. A message can be optionally attached if the 
    nature of the error is known.
    """
    try:
        await interaction.response.send_message(embed=Embed(
            color=brand_color,
            title="Oops!",
            description=message if message != "" else backup_msg
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