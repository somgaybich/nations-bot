from discord import Color

# 0: spring, 1: summer, 2: autumn, 3: winter
current_season = 0

def update_season():
    global current_season
    current_season = (current_season + 1) % 4

brand_color = Color(16417064)

admin_mode = True

# COMBAT SETTINGS
combat_settings: dict[str, float] = {
    # normalized probabilities
    "ally_contribution": 0.5,
    "base_stalemate_chance": 0.6,
    "crush_a": 0.4,
    "crush_b": 0.2,
    # crush_a controls the slope (impact of gap on chance)
    # crush_b controls the height/twist (how likely an unfavored crush can be)

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

    "crush_coop_modifier": 0.2,
    "decisive_coop_modifier": 0.1,
    "stalemate_coop_modifier": 0.05,

    # normalized probabilities
    "home_terrain_buff": 0.15,
    "home_city_buff": 0.1,
    "terrain_difficulty_debuff": 0.1, # for each point of terrain diff over 1
    "fort_buff": 0.15,
    "fort_area_buff": 0.05
}

empty_inventory = {
    "food": 0.0, 
    "iron": 0.0, 
    "copper": 0.0, 
    "gold": 0.0, 
    "coal": 0.0, 
    "steel": 0.0, 
    "machinery": 0.0, 
    "oil": 0.0, 
    "textiles": 0.0, 
    "jewelry": 0.0, 
    "spice": 0.0, 
    "consumer goods": 0.0, 
    "horses": 0.0, 
    "gems": 0.0, 
    "glass": 0.0
}

# arability = biome + (coastal_factor / biome ** 2)
# [coastal term only added if coastal, obviously]
biome_arability = {
    "mediterranean": 1.0,
    "humid_subtropical": 0.9,
    "humid_continental": 0.8,
    "monsoon": 0.7,
    "subarctic_continental": 0.5,
    "oceanic": 0.5,
    "savanna": 0.3,
    "hot_steppe": 0.2,
    "cold_steppe": 0.2,
    "mountains": 0.2,
    "high_mountains": 0.1,
    "cold_desert": 0.1,
    "hot_desert": 0.1,
    "tundra": 0.1,
    "ice_caps": 0.0
}
coastal_arability_factor = 0.006 # a = ba + (caf / ba**2)

food_surplus_use_rate = 0.2 # % of surplus to grow into
food_shortage_contract_rate = 0.3 # slows contractions due to food shortage

city_types = ["outpost", "village", "town", "city", "metropolis"]

backup_msg = """There was a problem processing that request! Ping @madaman and 
                she will take care of it as soon as possible."""

OPGUILD_ID = 1458983179099832472
LOGGING_CHANNEL_ID = 123456789012345678