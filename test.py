import asyncio
import logging

import game.actions as actions
from game.tick import tick

from scripts.load import load
from scripts.database import init_db, get_db
from scripts.log import log_setup
from scripts.rendering import snapshot_center

from world.world import tile_list, nation_list, units

log_setup("logs/test.log")
logging.getLogger(__name__)

async def test():
    await init_db("data/test.db")
    await load()
    
try:
    asyncio.run(test())
finally:
    asyncio.run(get_db().rollback())