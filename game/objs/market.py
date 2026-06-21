import logging 
from dataclasses import dataclass, field
from itertools import count

logger = logging.getLogger(__name__)

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