import asyncio
import dotenv
import os
import tracemalloc
import logging

# Clears preexisting log data
with open("logs/last.log", 'w') as f:
    pass

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("[%(asctime)s][%(levelname)s] [%(message)s]", datefmt='%H:%M:%S')

file_handler = logging.FileHandler('logs/last.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG) # For now set to DEBUG, if it becomes clogged change to INFO
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

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