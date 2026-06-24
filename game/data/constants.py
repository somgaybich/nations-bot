from discord import Color
from dataclasses import dataclass

# 0: spring, 1: summer, 2: autumn, 3: winter
current_season = 0

def update_season():
    global current_season
    current_season = (current_season + 1) % 4

brand_color = Color(16417064)

admin_mode = True

@dataclass
class CombatSettings:
    # normalized probabilities
    ally_contribution = 0.5
    base_stalemate_chance = 0.6
    crush_a = 0.4
    crush_b = 0.2
    # crush_a controls the slope (impact of effectiveness gap on chance)
    # crush_b controls the height/twist (how "crushy" unfavored wins are)

    # multiplied by a roll out of 1
    crush_loser_strength_mult = 2.0
    crush_loser_morale_mult = 1.8
    loser_strength_mult = 1.5
    loser_morale_mult = 1.3

    crush_winner_strength_mult = 0.3
    crush_winner_morale_mult = 0.0
    winner_strength_mult = 1.0
    winner_morale_mult = 0.7

    stalemate_strength_mult = 1.2
    stalemate_morale_mult = 1.0

    crush_coop_modifier = 0.2
    decisive_coop_modifier = 0.1
    stalemate_coop_modifier = 0.05

    # normalized probabilities
    home_terrain_buff = 0.15
    home_city_buff = 0.1
    terrain_difficulty_debuff = 0.1 # for each point of terrain diff
    fort_buff = 0.15
    fort_area_buff = 0.05

combat_settings = CombatSettings()

# This has been deprecated functionally but is still useful for reference
# FIXME: Remove in production
# empty_inventory = {
#     "food": 0.0, 
#     "iron": 0.0, 
#     "copper": 0.0, 
#     "gold": 0.0, 
#     "coal": 0.0, 
#     "steel": 0.0, 
#     "machinery": 0.0, 
#     "oil": 0.0, 
#     "textiles": 0.0, 
#     "jewelry": 0.0, 
#     "spice": 0.0, 
#     "consumer goods": 0.0, 
#     "horses": 0.0, 
#     "gems": 0.0, 
#     "glass": 0.0
# }

# arability = biome + (coastal_arability_factor / biome ** 2)
# [coastal term only added if coastal, obviously]

@dataclass
class BiomeArability:
    mediterranean = 1.0
    humid_subtropical = 0.9
    humid_continental = 0.8
    monsoon = 0.7
    subarctic_continental = 0.5
    oceanic = 0.5
    savanna = 0.3
    hot_steppe = 0.2
    cold_steppe = 0.2
    mountains = 0.2
    high_mountains = 0.1
    cold_desert = 0.1
    hot_desert = 0.1
    tundra = 0.1
    ice_caps = 0.0
coastal_arability_factor = 0.006

biome_arability = BiomeArability()

@dataclass
class BattleResult:
    CRUSHING_LOSS = 0
    LOSS = 1
    STALEMATE = 2
    VICTORY = 3
    CRUSHING_VICTORY = 4
    RETREATS = [0, 1, 2]
    LOSES_MOVEMENT = [0, 1, 2, 3]

battle_result = BattleResult()

surplus_use_rate = 0.2 # % of surplus to grow into
contract_rate = 0.3 # slows contractions
variety_shrink = 1 # pop/s lost when missing luxuries
luxury_mult = 4 # increases luxury production
steel_mult = 2
machine_mult = 2
textile_food_debuff = 0.4 # % of food produced with a textile industry

### Relative to the weights of each luxury. With no bonuses, all
### luxuries add up to a weight of 5.
no_luxury_weight = 20
# Bonus applies for each tile matching the environment
luxury_env_bonus = 0.2
luxury_industries = ["jewelry", "spice", "consumer_goods", 
                     "horses", "gems", "glass"]

city_types = ["outpost", "village", "town", "city", "metropolis"]

backup_msg = """There was a problem processing that request! Ping @madaman and 
                she will take care of it as soon as possible."""

OPGUILD_ID = 1458983179099832472
LOGGING_CHANNEL_ID = 123456789012345678