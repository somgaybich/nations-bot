from discord import Color

# 0: spring, 1: summer, 2: autumn, 3: winter
current_season = 0

def update_season():
    global current_season
    current_season = (current_season + 1) % 4

brand_color = Color(16417064)

admin_mode = True

class CombatSettings:
    def __init__(self):
        # normalized probabilities
        self.ally_contribution = 0.5
        self.base_stalemate_chance = 0.6
        self.crush_a = 0.4
        self.crush_b = 0.2
        # crush_a controls the slope (impact of effectiveness gap on chance)
        # crush_b controls the height/twist (how "crushy" unfavored wins are)

        # multiplied by a roll out of 1
        self.crush_loser_strength_loss = 2,
        self.crush_loser_morale_loss = 1.8,
        self.loser_strength_loss = 1.5,
        self.loser_morale_loss = 1.3,

        self.crush_winner_strength_loss = 0.3,
        self.crush_winner_morale_loss = 0,
        self.winner_strength_loss = 1.0,
        self.winner_morale_loss = 0.7,

        self.stalemate_strength_loss = 1.2,
        self.stalemate_morale_loss = 1.0,

        self.crush_coop_modifier = 0.2,
        self.decisive_coop_modifier = 0.1,
        self.stalemate_coop_modifier = 0.05

        # normalized probabilities
        self.home_terrain_buff = 0.15,
        self.home_city_buff = 0.1,
        self.terrain_difficulty_debuff = 0.1, # for each point of terrain diff
        self.fort_buff = 0.15,
        self.fort_area_buff = 0.05

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
coastal_arability_factor = 0.006

food_surplus_use_rate = 0.2 # % of surplus to grow into
food_shortage_contract_rate = 0.3 # slows contractions due to food shortage
textile_food_debuff = 0.4 # % of food produced with a textile industry

city_types = ["outpost", "village", "town", "city", "metropolis"]

backup_msg = """There was a problem processing that request! Ping @madaman and 
                she will take care of it as soon as possible."""

OPGUILD_ID = 1458983179099832472
LOGGING_CHANNEL_ID = 123456789012345678