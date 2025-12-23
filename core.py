import asyncio
import dotenv
import os
import tracemalloc
import logging
import time

from scripts.database import init_db
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

async def main():
    logger.info("Starting...")
    try:
        timer = time.perf_counter()
        await init_db()
        load_terrain()
        await load()
        logger.debug(f"Took {(time.perf_counter() / 1000000):.2f}ms to initialize data")
        await bot.start(token)
    finally:
        logger.critical("Shutting down.")
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass