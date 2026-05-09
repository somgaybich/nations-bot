import random
import math

import scripts.database as db
import scripts.errors as errors

from game.constants import (combat_settings, current_season)

from world.map import Tile, move_in_direction
from world.world import nation_list, tile_list

class Unit:
    """
    A generalized class for a military unit.
    Strength & morale are on [0, 100], exp is positive
    Type is in ["army", "fleet"]
    """
    name: str
    """
    The name of the unit.
    """
    type: str
    """
    The type of the unit, either "army" or "fleet".
    """
    home: str
    """
    The region the unit was created in.
    """
    owner: int
    """
    The NID of the nation this unit belongs to.
    """
    movement_free: int
    """
    The number of tiles this unit is allowed to move this season.
    """
    location: tuple[int, int]
    """
    The tile this unit is located in.
    """
    strength: float
    """
    The overall effectiveness of this unit in combat, relative to 1.0.
    """
    morale: float
    """
    The morale of the unit's soldiers, relative to 1.0.
    """
    exp: int
    """
    The number of battles this unit has been in. (Currently does nothing)
    """
    status: str
    """
    Any special state the unit is currenlty in. Currently may only be 
    'TRAINING', but future features like 'EMBARKED' are planned to use this.
    """
    id: int | None
    """
    The database ID of this unit. Generally shouldn't be touched, use owner 
    and name as identifiers.
    """
    def __init__(self, name: str, type: str, home: str, owner: int, 
                 movement_free: int, location: tuple[int, int] = (0, 0), 
                 strength: float = 1.0, morale: float = 1.0, exp: int = 0, 
                 status: str = "", id: int | None = None):
        """
        :param name: The name of the unit.
        :param type: The type of the unit, either "army" or "fleet".
        :param home: The region the unit was created in.
        :param owner: The NID of the nation this unit belongs to.
        :param movement_free: The number of tiles left this unit is allowed to 
            move this season.
        :param location: The tile this unit is located in.
        :param strength: The overall effectiveness of this unit in combat, 
            relative to 1.0.
        :param morale: The morale of the unit's soldiers, relative to 1.0.
        :param exp: The number of battles this unit has been in. 
            (Currently does nothing)
        :param status: Any special state the unit is currenlty in. Currently 
            may only be 'TRAINING', but future features like 'EMBARKED' are 
            planned to use this.
        :param id: The database ID of this unit. Generally shouldn't be 
            touched, use owner and name as identifiers.
        :type name: str
        :type type: str
        :type home: str
        :type owner: str
        :type movement_free: int
        :type location: tuple[int, int]
        :type strength: float
        :type morale: float
        :type exp: int
        :type status: str
        :type id: int
        """
        self.id = id
        self.name = name
        self.type = type
        self.home = home
        self.owner = owner
        self.location = location
        self.strength = strength
        self.morale = morale
        self.exp = exp
        self.status = status
        self.movement_free = movement_free
    
    async def save(self):
        await db.save_unit(self)
    
    def effectiveness(self, attacking: bool, location: tuple[int, int] = (0, 0)) -> int:
        """
        Calculates the effective combat strength of this unit.

        :param attacking: Whether this unit is the attacker.
        :param location: Where the calculation will be done from. This allows 
            us to guess how effective a unit will be in a different location.
        :type attacking: bool
        :type location: tuple[int, int]
        """
        if location == (0, 0):
            location = self.location

        base_eff = self.morale * self.strength
        eff = base_eff

        home_region = nation_list[self.owner].regions[self.home]
        tile = tile_list[location]
        battle_terrain = tile.terrain
        home_tile = tile_list[home_region.location]
        
        if battle_terrain == home_tile.terrain.biome:
            eff += combat_settings["home_terrain_buff"]
        elif attacking:
            eff -= (battle_terrain.difficulty - 1) * combat_settings["terrain_difficulty_debuff"]
            
        if (tile in home_region.developed_area()):
            eff += combat_settings["home_city_buff"]
            if tile is home_tile:
                eff += combat_settings["home_city_buff"]
            
        allies = nation_list[self.owner].allies
        allies.append(self.owner)
        for nationid in allies:
            nation = nation_list[nationid]
            for region in nation.regions.values():
                area = region.tiles
                if location not in area:
                    continue
        
        if tile.structure.structure_type.fname == "Fort":
            eff += combat_settings["fort_buff"]
        else:
            for tile in tile.area():
                if tile.structure.structure_type.fname == "Fort":
                    eff += combat_settings["fort_area_buff"]
                    break
        
        return eff
    
    async def move(self, direction: str):
        """
        Moves a unit in a specific direction.
        
        :param direction: The direction to move. The reason we take a direction
            instead of a tile is so that this interfaces well with the UI,
            which does not ever touch coordinates to avoid the user having to
            understand axial coordinates.
        :type direction: str in ['n', 's'...]
        """
        from world.world import units
        new_tile, last_tile = move_in_direction(tile_list[self.location], 
                                                direction.lower())
        if new_tile.difficulty > self.movement_free:
            raise errors.OutOfMovement()
        if new_tile.terrain.biome == "high_mountains" and current_season == 3:
            raise errors.TileImpassable("armies cannot enter high mountains during winter")
        if not new_tile.terrain.is_land and self.type == "army":
            raise errors.TileImpassable("armies cannot enter water tiles")
        if not new_tile.terrain.is_water and self.type == "fleet":
            raise errors.TileImpassable("fleets can only move in water")
        
        self.location = new_tile.location
        self.movement_free -= new_tile.difficulty

        for unit in units:
            if (unit.location == new_tile.location 
                and unit.owner != self.owner and 
                not unit.owner in nation_list[self.owner].allies):
                await self.attack(unit, last_tile)
        
        await self.save()

    async def retreat(self):
        """
        Moves this unit to the neighboring tile where they'd be safest and sets
        its movement to 0.
        """
        from world.world import units
        
        retreat_candidates: list[Tile] = []
        for tile in tile_list[self.location].area():
            if tile.difficulty <= self.movement_free:
                for unit in units:
                    if unit.location == tile.location:
                        # This tile has an enemy, we can't retreat there.
                        break
                
                if (tile.terrain.is_water 
                    and not tile.is_coastal() 
                    and self.type == "army"):
                    break
                elif (tile.terrain.is_land 
                    and not tile.is_coastal() 
                    and self.type == "fleet"):
                    break
                
                retreat_candidates.append(tile)
        
        if len(retreat_candidates) == 0:
            # There's nowhere to go!
            return

        effectivenesses = {}
        for tile in retreat_candidates:
            effectivenesses[tile.location] = self.effectiveness(False, 
                                                                tile.location)
        best_tile = max(effectivenesses, key=effectivenesses.get)
        self.location = best_tile

        self.movement_free = 0

    async def crushing_loss(self, scaled_impact, battle_location):
        """
        Deals damage to this unit corresponding to a crushing loss and 
        retreats.

        :param scaled_impact: The actual result of the battle.
        :param battle_location: The location where the battle happened.
        :type scaled_impact: float
        :type battle_location: tuple[int, int]
        """
        self.strength = max(0.0, self.strength - combat_settings["crush_loser_strength_loss"] * scaled_impact)
        self.morale = max(0.0, self.strength - combat_settings["crush_loser_morale_loss"] * scaled_impact)

        nation = nation_list[self.owner]
        for region in nation.regions.values():
            if battle_location in region.tiles:
                authority = nation.authorities[region.authority]
                authority.cooperation = max(0.0, authority.cooperation - combat_settings["crush_coop_modifier"] * scaled_impact)

        await self.retreat()

        self.movement_free = 0
    
    async def loss(self, scaled_impact, battle_location):
        """
        Deals damage to this unit corresponding to a loss and retreats.

        :param scaled_impact: The actual result of the battle.
        :param battle_location: The location where the battle happened.
        :type scaled_impact: float
        :type battle_location: tuple[int, int]

        """
        self.strength = max(0.0, self.strength - combat_settings["loser_strength_loss"] * scaled_impact)
        self.morale = max(0.0, self.strength - combat_settings["loser_morale_loss"] * scaled_impact)

        nation = nation_list[self.owner]
        for region in nation.regions.values():
            if battle_location in region.tiles:
                authority = nation.authorities[region.authority]
                authority.cooperation = max(0.0, authority.cooperation - combat_settings["decisive_coop_modifier"] * scaled_impact)

        await self.retreat()
        
        self.movement_free = 0
    
    async def victory(self, scaled_impact, battle_location):
        """
        Deals damage to this unit corresponding to a victory.
        
        :param scaled_impact: The actual result of the battle.
        :param battle_location: The location where the battle happened.
        :type scaled_impact: float
        :type battle_location: tuple[int, int]
        """
        self.strength = max(0.0, self.strength - combat_settings["winner_strength_loss"] * scaled_impact)
        self.morale = max(0.0, self.strength - combat_settings["winner_morale_loss"] * scaled_impact)

        nation = nation_list[self.owner]
        for region in nation.regions.values():
            if battle_location in region.tiles:
                authority = nation.authorities[region.authority]
                authority.cooperation = min(1.0, authority.cooperation + combat_settings["decisive_coop_modifier"] * scaled_impact)
        
        self.movement_free = 0
    
    async def crushing_victory(self, scaled_impact, battle_location):
        """
        Deals damage to this unit corresponding to a crushing victory.

        :param scaled_impact: The actual result of the battle.
        :param battle_location: The location where the battle happened.
        :type scaled_impact: float
        :type battle_location: tuple[int, int]
        """
        self.strength = max(0.0, self.strength - combat_settings["crush_winner_strength_loss"] * scaled_impact)
        self.morale = max(0.0, self.strength - combat_settings["crush_winner_morale_loss"] * scaled_impact)

        nation = nation_list[self.owner]
        for region in nation.regions.values():
            if battle_location in region.tiles:
                authority = nation.authorities[region.authority]
                authority.cooperation = min(1.0, authority.cooperation + combat_settings["crush_coop_modifier"] * scaled_impact)
          
    async def stalemate(self, scaled_impact, battle_location):
        """
        Deals damage to this unit corresponding to a stalemate.

        :param scaled_impact: The actual result of the battle.
        :param battle_location: The location where the battle happened.
        :type scaled_impact: float
        :type battle_location: tuple[int, int]
        """
        self.strength = max(0.0, self.strength - combat_settings["stalemate_strength_loss"] * scaled_impact)
        self.morale = max(0.0, self.strength - combat_settings["stalemate_morale_loss"] * scaled_impact)

        nation = nation_list[self.owner]
        for region in nation.regions.values():
            if battle_location in region.tiles:
                authority = nation.authorities[region.authority]
                authority.cooperation = max(0.0, authority.cooperation - combat_settings["stalemate_coop_modifier"] * scaled_impact)
        
        self.movement_free = 0

    async def attack(self, target: "Unit", last_tile: tuple[int, int]):
        """
        Attacks another unit in this tile.

        :param target: The Unit to attack.
        :param last_tile: The tile this unit was last in. If the battle is a
            stalemate, it will move back to this tile.
        :type target: Unit
        :type last_tile: tuple[int, int]
        """
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
                    if (unit.owner == self.owner 
                        or unit.owner in nation_list[self.owner].allies):
                        attacking_team.append(unit)
                        self_allies_eff += unit.effectiveness(True, 
                                                              self.location)
                    elif (unit.owner == target.owner 
                          or unit.owner in nation_list[target.owner].allies):
                        defending_team.append(unit)
                        target_allies_eff += unit.effectiveness(False, 
                                                                self.location)
        
        self_eff += combat_settings["ally_contribution"] * self_allies_eff
        target_eff += combat_settings["ally_contribution"] * target_allies_eff
        
        # All effectiveness modifiers must be done at this point

        normalizer = 1 / (self_eff + target_eff)
        att_normalized_eff = (self_eff * normalizer)
        def_normalized_eff = (target_eff * normalizer)
        gap = att_normalized_eff - def_normalized_eff

        stalemate_chance = gap_stalemate_chance(gap)
        non_stalemate_chance = 1 - stalemate_chance
        win_chance = att_normalized_eff * non_stalemate_chance
        loss_chance = def_normalized_eff * non_stalemate_chance

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
                await self.victory(scaled_impact, battle_location)
                await target.loss(scaled_impact, battle_location)

        elif roll <= loss_chance + win_chance:
            impact = loss_chance + win_chance - roll
            scaled_impact = math.sin(math.pi * impact / 2)
            if impact <= crushing_chance(-gap):
                # Crushing defender victory
                await target.crushing_victory(scaled_impact)
                await self.crushing_loss(scaled_impact)
            else:
                # Minor defender victory
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
    Takes a gap between unit strength and determines the probability of a 
    crushing victory for the unit from whose perspective the gap measurement
    was taken.

    :param gap: The gap between the normalized effectivenesses of the involved
        units. 
    :type gap: float
    """
    return max(0.0, min(1.0, combat_settings["crush_a"] * (gap + 1) ** 2 - combat_settings["crush_b"]))

def gap_stalemate_chance(gap: float) -> float:
    """
    Takes a gap between unit strengths and determines the probability of a
    stalemate.
    :param gap: The gap between the normalized effectivenesses of the involved
        units. 
    :type gap: float
    """
    return combat_settings["base_stalemate_chance"] * (math.e ** (-10 * (gap ** 2)))