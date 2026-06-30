import math
import random
from typing import TYPE_CHECKING

from game.data.constants import combat_settings, current_season, battle_result
from game.logic.map import get_area, move_in_direction, is_coastal

import scripts.errors as errors

if TYPE_CHECKING:
    from world.world import GameState
    from game.objs.region import Region
    from game.objs.unit import Unit
    from game.objs.tile import Tile

def at_war(region: "Region", state: "GameState"):
    """
    Returns True if there is a hostile unit in the area around the region's
    capital.
    """
    capital = state.tiles[region.location]
    sensitive_tiles = get_area(capital, state)
    for unit in state.units.values():
        if unit.location in sensitive_tiles:
            return True
    
    return False

def unit_effectiveness(
        unit: "Unit", 
        attacking: bool, 
        state: "GameState", 
        location: tuple[int, int] = (0, 0)
    ) -> int:
    """
    Calculates the effective combat strength of the target unit.

    :param attacking: Whether the target unit is the attacker.
    :param location: Where the calculation will be done from. This allows 
        us to guess how effective a unit will be in a different location.
    :type attacking: bool
    :type location: tuple[int, int]
    """
    if location == (0, 0):
        location = unit.location

    base_eff = unit.morale * unit.strength
    eff = base_eff

    home_region = state.regions[unit.home]
    tile = state.tiles[location]
    battle_terrain = tile.terrain
    home_tile = state.tiles[home_region.location]
    
    if battle_terrain == home_tile.terrain.biome:
        eff += combat_settings.home_terrain_buff
    elif attacking:
        eff -= (battle_terrain.difficulty - 1) * combat_settings.terrain_difficulty_debuff
        
    if (tile.location in home_region.tiles):
        eff += combat_settings.home_city_buff
        if tile is home_tile:
            eff += combat_settings.home_city_buff
        
    allies = state.nations[unit.owner].allies
    allies.append(unit.owner)
    for nationid in allies:
        nation = state.nations[nationid]
        for region_id in nation.regions:
            region = state.regions[region_id]
            region_area = region.tiles
            if location not in region_area:
                continue
    
    if tile.structure.structure_type.fname == "Fort":
        eff += combat_settings.fort_buff
    else:
        battle_area = get_area(tile, state)
        for tile in battle_area:
            if tile.structure.structure_type.fname == "Fort":
                eff += combat_settings.fort_area_buff
                break
    
    return eff

async def move_unit(unit: "Unit", direction: str, state: "GameState"):
    """
    Moves a unit in a specific direction.
    
    :param direction: The direction to move. The reason we take a direction
        instead of a tile is so that this interfaces well with the UI,
        which does not ever touch coordinates to avoid the user having to
        understand axial coordinates.
    :type direction: str in ['n', 's'...]
    """
    new_tile, last_tile = move_in_direction(state.tiles[unit.location], 
                                            direction.lower(), state)
    if new_tile.terrain.difficulty > unit.movement_free:
        raise errors.OutOfMovement()
    if new_tile.terrain.biome == "high_mountains" and current_season == 3:
        raise errors.TileImpassable("armies cannot enter high mountains during winter")
    if not new_tile.terrain.is_land and unit.type == "army":
        raise errors.TileImpassable("armies cannot enter water tiles")
    if not new_tile.terrain.is_water and unit.type == "fleet":
        raise errors.TileImpassable("fleets can only move in water")
    
    unit.location = new_tile.location
    unit.movement_free -= new_tile.terrain.difficulty

    for global_unit in state.units.values():
        if (global_unit.location == new_tile.location 
            and global_unit.owner != unit.owner and 
            not global_unit.owner in state.nations[unit.owner].allies):
            await battle(unit, global_unit, last_tile)
    
    await unit.save()

async def retreat(unit: "Unit", state: "GameState"):
    """
    Moves this unit to the neighboring tile where they'd be safest and sets
    its movement to 0.
    """
    retreat_candidates: list[Tile] = []
    for tile in get_area(state.tiles[unit.location], state):
        if tile.terrain.difficulty <= unit.movement_free:
            for unit in state.units.values():
                if unit.location == tile.location:
                    # This tile has an enemy, we can't retreat there.
                    break
            
            if (tile.terrain.is_water 
                and not is_coastal(tile)
                and unit.type == "army"):
                break
            elif (tile.terrain.is_land 
                and not is_coastal(tile)
                and unit.type == "fleet"):
                break
            
            retreat_candidates.append(tile)
    
    if len(retreat_candidates) == 0:
        # There's nowhere to go!
        return

    effectivenesses = {}
    for tile in retreat_candidates:
        effectivenesses[tile.location] = unit_effectiveness(
            unit, False, tile.location
        )
    best_tile = max(effectivenesses, key=effectivenesses.get)
    unit.location = best_tile

    unit.movement_free = 0
    await unit.save()

async def battle_resolve(
        unit: "Unit",
        scaled_impact: float,
        battle_location: tuple[int, int],
        state: "GameState",
        result: int
    ):
    """
    Deals damage to units depending on the scaled impact and the result of the
    battle. Applies stability debuffs, then retreats and sets movement to 0 if
    needed.
    """
    delta_strength = scaled_impact
    delta_morale = scaled_impact
    
    match result:
        case battle_result.CRUSHING_LOSS:
            delta_strength *= combat_settings.crush_loser_strength_mult
            delta_morale *= combat_settings.crush_loser_morale_mult
        case battle_result.LOSS:
            delta_strength *= combat_settings.loser_strength_mult
            delta_morale *= combat_settings.loser_morale_mult
        case battle_result.STALEMATE:
            delta_strength *= combat_settings.stalemate_strength_mult
            delta_morale *= combat_settings.stalemate_morale_mult
        case battle_result.VICTORY:
            delta_strength *= combat_settings.winner_strength_mult
            delta_morale *= combat_settings.winner_morale_mult
        case battle_result.CRUSHING_VICTORY:
            delta_strength *= combat_settings.crush_winner_strength_mult
            delta_morale *= combat_settings.crush_winner_morale_mult
    
    unit.strength -= delta_strength
    unit.morale -= delta_morale

    nation = state.nations[unit.owner]
    for region_id in nation.regions:
        region = state.regions[region_id]
        if battle_location in region.tiles:
            #FIXME: Modify stability
            pass
    
    if result in battle_result.RETREATS:
        await retreat(unit)
    
    if result in battle_result.LOSES_MOVEMENT:
        unit.movement_free = 0
    
    await unit.save()

def find_allies(
        unit: "Unit", 
        tile: "Tile", 
        state: "GameState"
    ) -> list["Unit"]:
    """
    Creates a list of the friendly units in the area of this unit.
    """
    unit_nation = state.nations[unit.owner]
    team = []

    for area_tile in get_area(tile, state):
        for global_unit in state.units.values():
            if global_unit.location == area_tile.location:
                # This unit is in a neighboring tile!
                if (global_unit.owner == unit.owner 
                    or global_unit.owner in unit_nation.allies):
                    team.append(global_unit)

def total_effectiveness(
        team: list["Unit"], 
        attacking: bool, 
        state: "GameState"
    ) -> float:
    """
    Finds the total sum effectiveness of a group of units. Sensitive to whether
    the units are attackers and the current game state.
    """
    total = 0
    for unit in team:
        total += unit_effectiveness(unit, attacking, state)
    return total

async def battle(
        attacker: "Unit", 
        defender: "Unit", 
        last_tile: tuple[int, int], 
        state: "GameState"
    ):
    """
    Attacks another unit in this tile.

    :param attacker: The Unit attacking.
    :param defender: The Unit defending.
    :param last_tile: The last location the attacker was in. If the battle is a
        stalemate, the attacker will move back to this location.
    :type attacker: Unit
    :type defender: Unit
    :type last_tile: tuple[int, int]
    """
    battle_location = attacker.location
    battle_tile = state.tiles[battle_location]
    attacker_allies = find_allies(attacker, battle_tile, state)
    defender_allies = find_allies(attacker, battle_tile, state)
    
    att_eff = unit_effectiveness(attacker, True, attacker.location)
    def_eff = unit_effectiveness(defender, False, attacker.location)
    
    att_allies_eff = total_effectiveness(attacker_allies, True, state)
    def_allies_eff = total_effectiveness(defender_allies, False, state)

    att_eff += att_allies_eff * combat_settings.ally_contribution
    def_eff += def_allies_eff * combat_settings.ally_contribution

    # Normalizing so that a roll on 0-1 maps to meaningful probabilities
    normalizer = 1 / (att_eff + def_eff)
    att_normalized_eff = (att_eff * normalizer)
    def_normalized_eff = (def_eff * normalizer)
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
            await battle_resolve(
                unit=attacker, 
                scaled_impact=scaled_impact, 
                battle_location=battle_location, 
                state=state, 
                result=battle_result.CRUSHING_VICTORY
            )
            await battle_resolve(
                unit=defender,
                scaled_impact=scaled_impact,
                battle_location=battle_location,
                state=state,
                result=battle_result.CRUSHING_LOSS
            )

        else:
            # Minor attacker victory
            await battle_resolve(
                unit=attacker, 
                scaled_impact=scaled_impact, 
                battle_location=battle_location, 
                state=state, 
                result=battle_result.VICTORY
            )
            await battle_resolve(
                unit=defender, 
                scaled_impact=scaled_impact, 
                battle_location=battle_location, 
                state=state, 
                result=battle_result.LOSS
            )

    elif roll <= loss_chance + win_chance:
        impact = loss_chance + win_chance - roll
        scaled_impact = math.sin(math.pi * impact / 2)
        if impact <= crushing_chance(-gap):
            # Crushing defender victory
            await battle_resolve(
                unit=defender, 
                scaled_impact=scaled_impact, 
                battle_location=battle_location, 
                state=state, 
                result=battle_result.CRUSHING_VICTORY
            )
            await battle_resolve(
                unit=attacker, 
                scaled_impact=scaled_impact, 
                battle_location=battle_location, 
                state=state, 
                result=battle_result.CRUSHING_LOSS
            )
        else:
            # Minor defender victory
            await battle_resolve(
                unit=defender, 
                scaled_impact=scaled_impact, 
                battle_location=battle_location, 
                state=state, 
                result=battle_result.VICTORY
            )
            await battle_resolve(
                unit=attacker, 
                scaled_impact=scaled_impact, 
                battle_location=battle_location, 
                state=state, 
                result=battle_result.LOSS
            )
    else:
        # Stalemate
        scaled_impact = math.sin(math.pi * (1 - roll) / 2)
        await battle_resolve(
            unit=attacker, 
            scaled_impact=scaled_impact, 
            battle_location=battle_location, 
            state=state, 
            result=battle_result.STALEMATE
        )
        await battle_resolve(
            unit=defender, 
            scaled_impact=scaled_impact, 
            battle_location=battle_location, 
            state=state, 
            result=battle_result.STALEMATE
        )

        attacker.location = last_tile
        attacker.movement_free = 0
    
    await attacker.save()
    await defender.save()

def crushing_chance(gap: float) -> float:
    """
    Takes a gap between unit strength and determines the probability of a 
    crushing victory for the unit from whose perspective the gap measurement
    was taken.

    :param gap: The gap between the normalized effectivenesses of the involved
        units. 
    :type gap: float
    """
    return max(0.0, min(1.0, combat_settings.crush_a * (gap + 1) ** 2 - combat_settings.crush_b))

def gap_stalemate_chance(gap: float) -> float:
    """
    Takes a gap between unit strengths and determines the probability of a
    stalemate.
    :param gap: The gap between the normalized effectivenesses of the involved
        units. 
    :type gap: float
    """
    return combat_settings.base_stalemate_chance * (math.e ** (-10 * (gap ** 2)))