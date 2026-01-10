from discord import Color

# 0: spring, 1: summer, 2: autumn, 3: winter
current_season = 0

def update_season():
    global current_season
    current_season = (current_season + 1) % 4

# if set to True will load from the json terrain data instead of the database
# this will erase all tile data in said database, so back up before changing
json_terrain = True

brand_color = Color(16417064)

LOGGING_CHANNEL_ID = 123456789012345678