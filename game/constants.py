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
combat_settings = {
    # normalized probabilities
    "ally_contribution": 0.5,
    "base_stalemate_chance": 0.2,
    "base_crushing_chance": 0.25,
    "crushing_chance_modifier": 0.75,

    # multiplied by a roll out of 1
    "crush_loser_strength_loss": 2,
    "crush_loser_morale_loss": 1.8,
    "loser_strength_loss": 1.5,
    "loser_morale_loss": 1.3,
    "crush_winner_strength_loss": 0.3,
    "crush_winner_morale_loss": 0,
    "winner_strength_loss": 1.0,
    "winner_morale_loss": 0.7,
    "stalemate_strength_loss": 1.2,
    "stalemate_morale_loss": 1.0,

    # multiplied by a roll out of 100
    "crush_stability_modifier": 20,
    "decisive_stability_modifier": 10,
    "stalemate_stability_modifier": 5,

    # normalized probabilities
    "home_terrain_buff": 0.15,
    "home_city_buff": 0.1,
    "desert_debuff": 0.1,
    "forest_debuff": 0.1,
    "mountains_debuff": 0.15,
    "high_mountains_debuff": 0.20,
    "fort_buff": 0.15,
    "fort_area_buff": 0.05
}

OPGUILD_ID = 1458983179099832472
LOGGING_CHANNEL_ID = 123456789012345678