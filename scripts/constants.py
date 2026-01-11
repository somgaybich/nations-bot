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

# COMBAT SETTINGS
# normalized probabilities
ALLY_CONTRIBUTION = 0.5
BASE_STALEMATE_CHANCE = 0.2
BASE_CRUSHING_CHANCE = 0.25
CRUSHING_CHANCE_MODIFIER = 0.75

# multiplied by a roll out of 1
CRUSH_LOSER_STRENGTH_LOSS = 2
CRUSH_LOSER_MORALE_LOSS = 1.8
LOSER_STRENGTH_LOSS = 1.5
LOSER_MORALE_LOSS = 1.3
CRUSH_WINNER_STRENGTH_LOSS = 0.3
CRUSH_WINNER_MORALE_LOSS = 0
WINNER_STRENGTH_LOSS = 1.0
WINNER_MORALE_LOSS = 0.7
STALEMATE_STRENGTH_LOSS = 1.2
STALEMATE_MORALE_LOSS = 1.0

# multiplied by a roll out of 100
CRUSH_STABILITY_MODIFIER = 20
DECISIVE_STABILITY_MODIFIER = 10
STALEMATE_STABILITY_MODIFIER = 5

# normalized probabilities
HOME_TERRAIN_BUFF = 0.15
HOME_CITY_BUFF = 0.1
DESERT_DEBUFF = 0.1
FOREST_DEBUFF = 0.1
MOUNTAINS_DEBUFF = 0.15
HIGH_MOUNTAINS_DEBUFF = 0.20
FORT_BUFF = 0.15
FORT_AREA_BUFF = 0.05

# MOVEMENT SETTINGS
difficulties = {
    "desert": 2,
    "forest": 2,
    "mountains": 2,
    "high_mountains": 3
}

OPGUILD_ID = 1458983179099832472
LOGGING_CHANNEL_ID = 123456789012345678