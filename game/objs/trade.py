from dataclasses import dataclass, field
from world.database import save_trade

@dataclass
class Trade:
    """
    Connects two nations in terms of a certain resource. A trade agreement may
    create multiple, as there is only one resource per trade object.
    """
    nations: list[int]
    """
    The NIDS of the nations connected by this trade. Will always be length 2.
    """
    resource: str
    """
    The name of the resource being connected. See :class:`empty_inventory` for
    valid values.
    """
    id: int | None = field(init=False)
    """
    The object ID of this trade.
    """

    async def save(self):
        await save_trade(self)