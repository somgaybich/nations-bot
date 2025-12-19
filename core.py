import asyncio
import dotenv
import os
import tracemalloc
import logging

from scripts.bot import sync, bot
from scripts.nations import load_terrain

# Clears preexisting log data
with open("logs/last.log", 'w') as f:
    pass
logging.basicConfig(filename='logs/last.log', encoding='utf-8', level=logging.DEBUG, 
                    format="[%(asctime)s][%(levelname)s] [%(message)s]", datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

tracemalloc.start()

dotenv.load_dotenv(".venv/.env")
token = os.getenv("token")

@bot.event
async def on_ready():
    logger.info("Syncing commands...")
    await sync(bot)
    logger.info("Loading tile data...")
    load_terrain()
    logger.info(f"Logged in as {bot.user}")

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
    try:
        logger.info("Starting...")
        async with bot:
            await bot.start(token)
    except KeyboardInterrupt:
        logger.critical("Shutting down.")
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())