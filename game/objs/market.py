import logging 
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

from game.objs.industry import industry_types

from world.world import markets, regions, nation_list

if TYPE_CHECKING:
    from game.objs.region import Region

class Trade:
    """
    Connects two markets in terms of a certain resource. A trade agreement may
    create multiple, as there is only one per resource.
    """
    markets: tuple[str, str]
    """
    The markets connected by this trade.
    """
    connections: list[tuple[str, str]]
    """
    A list of tuples of region names. Represents the possible trade routes
    that resources could flow from one market to another through. These pairs
    of regions must touch or both be based around coastal cities.
    """
    resource: str
    """
    The name of the resource being connected. See :class:`empty_inventory` for
    valid values.
    """
    def __init__(self, markets, connections, resource):
        """
        :param markets: The markets connected by this trade.
        """
        self.markets = markets
        self.connections = connections
        self.resource = resource

class Market:
    """
    A market encompasses multiple regions and connects their economies. This
    allows resources to be "automatically traded" (shared) between regions. All
    transactions of the economy are actually of markets (even when they are 
    shown to the player as transactions of regions).
    """
    name: str
    """
    The name of this market, also the name of its founding region.
    """
    owner: int
    """
    The NID of the nation to whom this market belongs.
    """
    regions: list["Region"]
    """
    The regions that are a part of this market.
    """
    trades: list[Trade]
    def __init__(self, name: str, owner: int, regions: list["Region"]):
        """
        :param name: The name of this market, also the name of its founding 
            region.
        :param owner: The NID of the nation to whom this market belongs.
        :param regions: The regions that are a part of this market.
        :type name: str
        :type owner: int
        :type regions: list[Region]
        """
        self.name = name
        self.owner = owner
        self.regions = regions

    def connected(self, target: str) -> bool:
        """
        Determines if this market is connected to a region.
        :param target: The name of the target to try to connect to.
        :type target: str
        """
        for region in self.regions:
            if region.connected(target):
                return True
        
        return False

    def production(self, item: str):
        """
        Calculates the amount of an item produced by the regions in this
        market.
        """
        production = 0

        for region in self.regions:
            for industry_name in region.industries:
                industry = industry_types[industry_name]
                output = industry.production(region)
                if output[0] != item:
                    continue
                production += output[1]
        
        return production

    def consumption(self, item: str):
        """
        Calculates the amount of an item that would ideally be consumed in this
        market. If the resource is in a deficit, this will not reflect actual
        change in resource volumes.
        """
        consumption = 0
        
        match item:
            case "food":
                for region in self.regions:
                    consumption += region.population
        
        return consumption

    def supply(self, item: str) -> float:
        """
        Calculates the current supply of an item in this market, from
        production - consumption.
        """
        return (self.production(item) - self.consumption(item))
    
    def fulfillment(self, item: str) -> float:
        """
        Calculates the fulfillment ratio of an item in this market. Returns 
        1.0 if produced > consumed, else returns produced/consumed.
        """
        if self.production(item) > self.consumption(item):
            return 1.0
        return self.production(item) / self.consumption(item)

async def build_markets():
    markets.reset()
    
    for nation in nation_list.values():
        capital = nation.capital()
        capital_market = Market(
            name=capital.name,
            owner=nation.userid,
            regions=[capital]
        )
        
        nation_regions = nation.regions.values()
        connecting = True
        while connecting:
            connecting = False
            for region in nation_regions:
                if (capital_market.connected(region.name) 
                    and region not in capital_market.regions):
                    capital_market.regions.append(region)
                    region.market = capital_market.name
                    connecting = True

        markets[capital.name] = capital_market

        isolated = set(nation_regions) - set(capital_market.regions)
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
                for region in isolated:
                    if (new_market.connected(region.name) 
                        and region not in new_market.regions):
                        new_market.regions.append(region)
                        region.market = new_market.name
                        connecting = True
            
            markets[largest.name] = new_market
            isolated -= set(new_market.regions)
