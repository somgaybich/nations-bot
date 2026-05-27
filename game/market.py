import logging 
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

from game.constants import empty_inventory

from world.world import markets, nation_list, regions

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
    surplus: dict[str, float]
    """
    The amount of each resource currently being overproduced in this market.
    Negative values represent deficits.
    See the structure of :class:`empty_inventory` for keys.
    """
    trades: list[Trade]
    def __init__(self, name: str, owner: int, regions: list[Region], 
                 surplus: dict[str, float] | None = None):
        """
        :param name: The name of this market, also the name of its founding 
            region.
        :param owner: The NID of the nation to whom this market belongs.
        :param regions: The regions that are a part of this market.
        :param surplus: The amount of each resource currently being 
            overproduced in this market. Negative values represent deficits.
        :type name: str
        :type owner: int
        :type regions: list[Region]
        :type surplus: dict[str, float]
        """
        self.name = name
        self.owner = owner
        self.regions = regions
        self.surplus = (surplus if surplus is not None 
                        else empty_inventory)
    
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