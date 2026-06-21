from typing import TYPE_CHECKING

from game.data.industry import industry_types

if TYPE_CHECKING:
    from game.objs.market import Market
    from world.world import GameState

def is_connected(market: "Market", target: int, state: "GameState") -> bool:
    """
    Determines if this market is connected to a region by its ID.
    :param target: The ID of the target to try to connect to.
    :type target: int
    """
    for region_id in market.regions:
        region = state.regions[region_id]
        if region.connected(target):
            return True
    
    return False

def get_production(market: "Market", item: str, state: "GameState"):
    """
    Calculates the amount of an item produced by the regions in this
    market.
    """
    production = 0

    for region_id in market.regions:
        region = state.regions[region_id]
        for industry_name in region.industries:
            industry = industry_types[industry_name]
            output = industry.production(region, state)
            if output[0] != item:
                continue
            production += output[1]
    
    return production

def get_consumption(market: "Market", item: str, state: "GameState"):
    """
    Calculates the amount of an item that would ideally be consumed in this
    market. If the resource is in a deficit, this will not reflect actual
    change in resource volumes.
    """
    consumption = 0
    
    match item:
        case "food":
            for region_id in market.regions:
                region = state.regions[region_id]
                consumption += region.population
    
    return consumption

def get_supply(market: "Market", item: str, state: "GameState") -> float:
    """
    Calculates the current supply of an item in this market, from
    production - consumption.
    """
    return (get_production(market, item, state) - get_consumption(market, item, state))

def get_fulfillment(
        market: "Market", 
        item: str, 
        state: "GameState"
    ) -> float:
    """
    Calculates the fulfillment ratio of an item in this market. Returns 
    1.0 if produced > consumed, else returns produced/consumed.
    """
    production = get_production(market, item, state)
    consumption = get_consumption(market, item, state)
    if production > consumption:
        return 1.0
    return production / consumption

async def build_markets(state: "GameState"):
    state.markets.clear()
    
    for nation in state.nations.values():
        capital = nation.capital(state)
        capital_market = Market(
            name=capital.name,
            owner=nation.userid,
            regions=[capital]
        )
        
        nation_regions = nation.regions
        connecting = True
        while connecting:
            connecting = False
            for region_id in nation_regions:
                if (is_connected(capital_market, region_id, state) 
                    and region_id not in capital_market.regions):
                    capital_market.regions.append(region_id)
                    state.regions[region_id].market = capital_market.name
                    connecting = True

        state.markets[capital_market.id] = capital_market

        isolated_ids = set(nation_regions) - set(capital_market.regions)
        isolated = [state.regions[id] for id in isolated_ids]
        while len(isolated) != 0:
            sorted_regions = sorted(
                isolated, 
                key=lambda region: region.population, 
                reverse=True
            )
            largest = sorted_regions[0]
            new_market = Market(
                name=largest.name,
                owner=nation.userid,
                regions=[largest]
            )
            
            connecting = True
            while connecting:
                connecting = False
                for region_id in isolated_ids:
                    if (is_connected(new_market, region_id, state) 
                        and region_id not in new_market.regions):
                        new_market.regions.append(region_id)
                        state.regions[region_id].market = new_market.name
                        connecting = True
            
            state.markets[new_market.id] = new_market
            isolated -= set(new_market.regions)
