import asyncio
import logging

import game.logic.actions as actions
from game.logic.tick import tick

from world.load import load
from world.database import init_db, get_db
from scripts.log import log_setup
from scripts.rendering import snapshot_center

log_setup("logs/test.log")
logging.getLogger(__name__)

async def test():
    await init_db("data/test.db")
    await load()
    
try:
    asyncio.run(test())
finally:
    asyncio.run(get_db().rollback())