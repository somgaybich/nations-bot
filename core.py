import asyncio
import dotenv
import os
import tracemalloc
import logging
import time

from scripts.constants import json_terrain
from scripts.database import init_db, get_db
from scripts.nations import load_terrain, load
from scripts.log import log_setup
log_setup()

logger = logging.getLogger(__name__)

from scripts.botlib import bot

tracemalloc.start()

dotenv.load_dotenv(".venv/.env")
token = os.getenv("token")

@bot.event
async def on_disconnect():
    logger.error("Lost connection to Discord.")

@bot.event
async def on_resumed():
    logger.info("Reconnected to Discord.")

@bot.event
async def on_connect():
    logger.info("Connected to Discord.")

if __name__ == "__main__":
    try:
        bot.run(token)
    except KeyboardInterrupt:
        pass
    finally:
        logger.critical("Shutting down.")
        asyncio.run(get_db().commit())