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

city_types = ["outpost", "village", "town", "city", "metropolis"]

arable_biomes = ["monsoon", "savanna", "humid_subtropical", "mediterranean", 
                 "humid_continental", "subarctic_continental"]
dry_biomes = ["hot_steppe", "hot_desert", "cold_steppe", "cold_desert"]

backup_msg = """There was a problem processing that request! Ping @madaman and 
                she will take care of it as soon as possible."""

OPGUILD_ID = 1458983179099832472
LOGGING_CHANNEL_ID = 123456789012345678