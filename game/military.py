import random
import math

import scripts.database as db
import scripts.errors as errors

from game.constants import combat_settings, current_season

from world.map import Tile, move_in_direction
from world.cities import City
from world.world import nation_list, tile_list

class Unit:
    """
    A generalized class for a military unit.
    Strength & morale are on [0, 100], exp is positive
    Type is in ["army", "fleet"]
    """
    def __init__(self, name: str, type: str, home: str, owner: int, movement_free: int, 
                 location: tuple[int, int] = (0, 0), strength: int = 1, morale: int = 1, 
                 exp: int = 0, unit_id: int | None = None):
        self.id = unit_id # IDs aren't guaranteed if the initial save fails!
        self.name = name
        self.type = type
        self.home = home
        self.owner = owner
        self.location = location
        self.strength = strength
        self.morale = morale
        self.exp = exp
        self.movement_free = movement_free
    
    async def save(self):
        await db.save_unit(self)
    
    def effectiveness(self, attacking: bool, location: tuple[int, int]) -> int:
        base_eff = self.morale * self.strength
        eff = base_eff

        home_city = nation_list[self.owner].cities[self.home]
        location = tile_list[location]
        battle_terrain = location.terrain
        home_terrain = home_city.terrain
        
        if battle_terrain == home_terrain:
            eff += combat_settings["home_terrain_buff"]
        if location in home_city.area() or (location in home_city.metroarea() and home_city.tier == 4):
            eff += combat_settings["home_city_buff"]
            if location == home_city:
                eff += combat_settings["home_city_buff"]
        elif attacking:
            match battle_terrain:
                case "desert":
                    eff -= combat_settings["desert_debuff"]
                case "forest":
                    eff -= combat_settings["forest_debuff"]
                case "mountains":
                    eff -= combat_settings["mountains_debuff"]
                case "high_mountains":
                    eff -= combat_settings["high_mountains_debuff"]
                #TODO: Update when more terrain types are added
        if "fort" in location.structures:
            eff += combat_settings["fort_buff"]
        else:
            for tile in location.area():
                if "fort" in tile.structures:
                    eff += combat_settings["fort_area_buff"]
                    break
        
        # TODO: Incorporate effectiveness loss due to command hierarchy
        return eff
        
    async def move(self, direction: str):
        from world.world import units
        new_tile, last_tile = move_in_direction(tile_list[self.location], direction)
        if new_tile.difficulty > self.movement_free:
            raise errors.OutOfMovement()
        if new_tile.terrain.land_biome == "high_mountains" and current_season == 3:
            raise errors.TileImpassable("armies cannot enter high mountains during winter")
        if not new_tile.terrain.is_land and self.type == "army":
            raise errors.TileImpassable("armies cannot enter water tiles")
        if not new_tile.terrain.is_water and self.type == "fleet":
            raise errors.TileImpassable("fleets can only move in water")
        
        self.location = new_tile.location
        self.movement_free -= new_tile.difficulty

        for unit in units:
            if unit.location == new_tile.location and unit.owner != self.owner and not unit.owner in nation_list[self.owner].allies:
                await self.attack(unit, last_tile)
        
        await self.save()

    async def retreat(self):
        from world.world import units
        retreat_candidates: list[Tile] = []
        for tile in tile_list[self.location].area():
            if tile.difficulty <= self.movement_free:
                for unit in units:
                    if unit.location == tile.location:
                        # This tile has an enemy, we can't retreat there.
                        break
                retreat_candidates.append(tile)
        
        effectivenesses = {}
        for tile in retreat_candidates:
            effectivenesses[tile.location] = self.effectiveness()
        best_tile = max(effectivenesses, key=effectivenesses.get)
        self.location = best_tile

        self.movement_free = 0

    async def crushing_loss(self, scaled_impact, battle_location):
        self.strength = max(0.0, self.strength - combat_settings["crush_loser_strength_loss"] * scaled_impact)
        self.morale = max(0.0, self.strength - combat_settings["crush_loser_morale_loss"] * scaled_impact)

        for tile in tile_list[battle_location].metroarea():
            if isinstance(tile, City) and (tile_list[battle_location] in tile.developed_area()) and tile.owner == self.owner:
                tile.stability = min(100, tile.stability + scaled_impact * combat_settings["crush_stability_modifier"])
                await tile.save()
        
        await self.retreat()

        self.movement_free = 0
    
    async def loss(self, scaled_impact, battle_location):
        self.strength = max(0.0, self.strength - combat_settings["loser_strength_loss"] * scaled_impact)
        self.morale = max(0.0, self.strength - combat_settings["loser_morale_loss"] * scaled_impact)

        for tile in tile_list[battle_location].metroarea():
            if isinstance(tile, City) and (tile_list[battle_location] in tile.developed_area()) and tile.owner == self.owner:
                tile.stability = min(100, tile.stability + scaled_impact * combat_settings["decisive_stability_modifier"])
                await tile.save()

        await self.retreat()
        
        self.movement_free = 0
    
    async def victory(self, scaled_impact, battle_location):
        self.strength = max(0.0, self.strength - combat_settings["winner_strength_loss"] * scaled_impact)
        self.morale = max(0.0, self.strength - combat_settings["winner_morale_loss"] * scaled_impact)

        for tile in tile_list[battle_location].metroarea():
            if isinstance(tile, City) and (tile_list[battle_location] in tile.developed_area()) and tile.owner == self.owner:
                tile.stability = min(100, tile.stability + scaled_impact * combat_settings["decisive_stability_modifier"])
                await tile.save()
        
        self.movement_free = 0
    
    async def crushing_victory(self, scaled_impact, battle_location):
        self.strength = max(0.0, self.strength - combat_settings["crush_winner_strength_loss"] * scaled_impact)
        self.morale = max(0.0, self.strength - combat_settings["crush_winner_morale_loss"] * scaled_impact)

        for tile in tile_list[battle_location].metroarea():
            if isinstance(tile, City) and (tile_list[battle_location] in tile.developed_area()) and tile.owner == self.owner:
                tile.stability = min(100, tile.stability + scaled_impact * combat_settings["crush_stability_modifier"])
                await tile.save()
          
    async def stalemate(self, scaled_impact, battle_location):
        self.strength = max(0.0, self.strength - combat_settings["stalemate_strength_loss"] * scaled_impact)
        self.morale = max(0.0, self.strength - combat_settings["stalemate_morale_loss"] * scaled_impact)

        for tile in tile_list[battle_location].metroarea():
            if isinstance(tile, City) and (tile_list[battle_location] in tile.developed_area()) and tile.owner == self.owner:
                tile.stability = min(100, tile.stability + scaled_impact * combat_settings["stalemate_stability_modifier"])
                await tile.save()
        
        self.movement_free = 0

    async def attack(self, target: "Unit", last_tile: Tile):
        from world.world import units
        self_eff = self.effectiveness(True, self.location)
        target_eff = target.effectiveness(False, self.location)
        
        battle_location = self.location
        attacking_team = [self]
        self_allies_eff = 0
        defending_team = [target]
        target_allies_eff = 0
        for tile in tile_list[battle_location].area():
            for unit in units:
                if unit.location == tile.location:
                    # This unit is in a neighboring tile!
                    if unit.owner == self.owner or unit.owner in nation_list[self.owner].allies:
                        attacking_team.append(unit)
                        self_allies_eff += unit.effectiveness(True, self.location)
                    elif unit.owner == target.owner or unit.owner in nation_list[target.owner].allies:
                        defending_team.append(unit)
                        target_allies_eff += unit.effectiveness(False, self.location)
        
        self_eff += combat_settings["ally_contribution"] * self_allies_eff
        target_eff += combat_settings["ally_contribution"] * target_allies_eff
        
        # All effectiveness modifiers must be done at this point

        normalizer = 1 / (self_eff + target_eff)
        self_bvc = (self_eff * normalizer)
        target_bvc = (target_eff * normalizer)
        gap = self_bvc - target_bvc

        stalemate_chance = max(0.0, combat_settings["base_stalemate_chance"] - ((gap ** 2) * combat_settings["base_stalemate_chance"]))
        non_stalemate_chance = 1 - stalemate_chance
        win_chance = self_bvc * non_stalemate_chance
        loss_chance = target_bvc * non_stalemate_chance

        roll = random.random()
        if roll <= win_chance:
            impact = win_chance - roll
            scaled_impact = math.sin(math.pi * impact / 2)
            # Attacker wins
            if impact <= crushing_chance(gap):
                # Crushing attacker victory
                await self.crushing_victory(scaled_impact, battle_location)
                await target.crushing_loss(scaled_impact, battle_location)

            else:
                # Minor attacker victory
                await self.victory()
                await target.loss()

        elif roll <= loss_chance + win_chance:
            impact = loss_chance + win_chance - roll
            scaled_impact = math.sin(math.pi * impact / 2)
            if impact <= crushing_chance(-gap):
                # Crushing attacker victory
                await target.crushing_victory(scaled_impact)
                await self.crushing_loss(scaled_impact)
            else:
                # Minor attacker victory
                await target.victory(scaled_impact)
                await self.loss(scaled_impact)
        else:
            # Stalemate
            scaled_impact = math.sin(math.pi * (1 - roll) / 2)
            self.stalemate(scaled_impact)
            target.stalemate(scaled_impact)

            self.location = last_tile
        
        await self.save()
        await target.save()

def crushing_chance(gap: float) -> float:
    """
    Takes a gap between unit strength and determines the probability of a crushing victory.
    This probability applies only to the unit from whose perspective the gap measurement was taken.
    """
    return max(0.0, min(1.0, combat_settings["base_crushing_chance"] + ((gap ** 3) * combat_settings["crushing_chance_modifier"])))