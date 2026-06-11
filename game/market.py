import logging 
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

from world.world import markets, nation_list

if TYPE_CHECKING:
    from game.region import Region

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
    def __init__(self, name: str, owner: int, regions: list[Region]):
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
    
    async def save(self):
        """
        Saves this market to the database.
        """
        # FIXME: Do database stuff
        pass

    async def delete(self):
        """
        Deletes this market from the database.
        """
        # FIXME: Do database stuff
        markets.pop(self)
        nation_list[self.owner].markets.pop(self)

    async def merge_markets(self, target: "Market"):
        """
        Subsumes another market into this one.
        :param target: The market to merge with. This market will no longer
            exist.
        :type target: Market
        """
        for region in target.regions:
            self.regions.append(region)
            region.market = self.name
            await region.save()
        
        await self.save()
        await target.delete()

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
            for industry in region.industries:
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