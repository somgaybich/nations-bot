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

city_types = ["outpost", "village", "town", "city", "metropolis"]

arable_biomes = ["monsoon", "savanna", "humid_subtropical", "mediterranean", 
                 "humid_continental", "subarctic_continental"]
dry_biomes = ["hot_steppe", "hot_desert", "cold_steppe", "cold_desert"]

backup_msg = """There was a problem processing that request! Ping @madaman and 
                she will take care of it as soon as possible."""

OPGUILD_ID = 1458983179099832472
LOGGING_CHANNEL_ID = 123456789012345678