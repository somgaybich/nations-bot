from dataclasses import dataclass

@dataclass
class Trade:
    """
    Connects two markets in terms of a certain resource. A trade agreement may
    create multiple, as there is only one per resource.
    """
    nations: tuple[str, str]
    """
    The nations connected by this trade.
    """
    resource: str
    """
    The name of the resource being connected. See :class:`empty_inventory` for
    valid values.
    """
    id: int | None
    """
    The object ID of this trade.
    """