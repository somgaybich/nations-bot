import random

class Espionage:
    def __init__(self, investment, espionage_type, target):
        self.investment = investment
        self.success_chance = 0.1 + (0.05 * (investment - 1))
        self.reveal_chance = 0.9 - (0.04 * (investment - 1))
        self.espionage_type = espionage_type
        self.target = target
    
    def roll(self):
        if random.random() > self.success_chance:
            if self.espionage_type == "spy":
                pass
                # do spy stuff?
            elif self.espionage_type == "assassin":
                pass
                # do assassin stuff?
        if random.random() > self.reveal_chance:
            pass
            # do reveal stuff?