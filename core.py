import asyncio
import dotenv
import os
import tracemalloc
import logging

# Clears preexisting log data
with open("logs/last.log", 'w') as f:
    pass
logging.basicConfig(filename='logs/last.log', encoding='utf-8', level=logging.DEBUG, 
                    format="[%(asctime)s][%(levelname)s] [%(message)s]", datefmt='%H:%M:%S')
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
    try:
        logger.info("Starting...")
        await bot.start(token)
    except KeyboardInterrupt:
        logger.critical("Shutting down.")
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())