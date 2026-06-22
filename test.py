import asyncio
import logging
import shutil

import game.logic.actions as actions

from world.load import load
from world.database import init_db, get_db
from scripts.log import log_setup

from world.world import get_state

log_setup("logs/test.log")
logging.getLogger(__name__)

async def test():
    shutil.copy("data/map.db", "data/test.db")
    await init_db("data/test.db")
    await load(get_state())
    
    # Do game actions
    await actions.new_nation(
        name="Testia", 
        userid=247164420273209345, 
        state=get_state()
    )
    await actions.new_region(
        name="Testville", 
        location=(-28, 35), 
        owner=247164420273209345,
        capital=True,
        state=get_state()
    )
    
    # Make sure the new game state is save-load stable
    await get_db().commit()
    await load(get_state())
    shutil.copy("data/map.db", "data/test.db")
    print("Test complete.")
    
asyncio.run(test())