import asyncio
import logging
import shutil

import game.logic.actions as actions
import game.logic.combat as combat

from world.load import load
from world.database import init_db, get_db
from scripts.log import log_setup

from world.world import get_state

log_setup("logs/test.log")
logging.getLogger(__name__)

test_user = 247164420273209345

async def test():
    shutil.copy("data/map.db", "data/test.db")
    await init_db("data/test.db")
    await load(get_state())
    
    # Do game actions
    await actions.new_nation(
        name="Testia", 
        userid=test_user, 
        state=get_state()
    )
    await actions.new_region(
        name="Testville", 
        location=(-28, 35), 
        owner=test_user,
        capital=True,
        state=get_state()
    )

    await actions.new_army(
        name="1st army",
        owner=test_user,
        region_name="Testville",
        state=get_state()
    )
    first_army_id = get_state().unit_ids["1st army"]
    first_army = get_state().units[first_army_id]
    await combat.move_unit(
        unit=first_army,
        direction='n',
        state=get_state()
    )
    
    # Make sure the new game state is save-load stable
    await get_db().commit()
    await load(get_state())
    shutil.copy("data/map.db", "data/test.db")
    print("Test passed with no errors.")
    
asyncio.run(test())