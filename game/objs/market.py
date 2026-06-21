import logging 
from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from itertools import count

logger = logging.getLogger(__name__)

from game.data.industry import industry_types

if TYPE_CHECKING:
    from world.world import GameState

_id_generator = count(start=1)

@dataclass
class Market:
    """
    A market encompasses multiple regions and connects their economies. This
    allows resources to be "automatically traded" (shared) between regions. All
    transactions of the economy are actually of markets (even when they are 
    shown to the player as transactions of regions).
    """
    id: int | None = field(default_factory=_id_generator.__next__, init=False)
    """
    The object ID of this market. Unlike other object IDs, these are assigned
    on initialization of the market object. They are also not persistent
    between calls of :class:`build_markets`.
    """
    name: str
    """
    The name of this market, also the name of its founding region.
    """
    owner: int
    """
    The NID of the nation to whom this market belongs.
    """
    regions: list[int]
    """
    The IDs of the regions that are a part of this market.
    """

    def connected(self, target: int, state: "GameState") -> bool:
        """
        Determines if this market is connected to a region by its ID.
        :param target: The ID of the target to try to connect to.
        :type target: int
        """
        for region_id in self.regions:
            region = state.regions[region_id]
            if region.connected(target):
                return True
        
        return False

    def production(self, item: str, state: "GameState"):
        """
        Calculates the amount of an item produced by the regions in this
        market.
        """
        production = 0

        for region_id in self.regions:
            region = state.regions[region_id]
            for industry_name in region.industries:
                industry = industry_types[industry_name]
                output = industry.production(region, state)
                if output[0] != item:
                    continue
                production += output[1]
        
        return production

    def consumption(self, item: str, state: "GameState"):
        """
        Calculates the amount of an item that would ideally be consumed in this
        market. If the resource is in a deficit, this will not reflect actual
        change in resource volumes.
        """
        consumption = 0
        
        match item:
            case "food":
                for region_id in self.regions:
                    region = state.regions[region_id]
                    consumption += region.population
        
        return consumption

    def supply(self, item: str, state: "GameState") -> float:
        """
        Calculates the current supply of an item in this market, from
        production - consumption.
        """
        return (self.production(item, state) - self.consumption(item, state))
    
    def fulfillment(self, item: str, state: "GameState") -> float:
        """
        Calculates the fulfillment ratio of an item in this market. Returns 
        1.0 if produced > consumed, else returns produced/consumed.
        """
        if self.production(item, state) > self.consumption(item, state):
            return 1.0
        return self.production(item, state) / self.consumption(item, state)

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
                if (capital_market.connected(region_id, state) 
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
                    if (new_market.connected(region_id, state) 
                        and region_id not in new_market.regions):
                        new_market.regions.append(region_id)
                        state.regions[region_id].market = new_market.name
                        connecting = True
            
            state.markets[new_market.id] = new_market
            isolated -= set(new_market.regions)
