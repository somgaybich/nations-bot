from dataclasses import dataclass

### NOTE: This class does not actually have anything to do with the use of
### luxuries in city growth, and is only relevant to spawning behavior.
@dataclass
class LuxuryType:
    envs: dict[str, float]
    """
    The biomes that make this luxury more common. The values are a multiplier 
    applied to the matching environment bonus.
    """
    resource: str
    """
    The name of the resource associated with this luxury.
    """

luxury_types = [
    LuxuryType(
        envs={
            "high_mountains": 2,
            "mountains": 1
        },
        resource="jewelry"
    ),
    LuxuryType(
        envs={
            "hot_desert": 2, 
            "cold_desert": 2, 
            "hot_steppe": 1, 
            "cold_steppe": 1,
            "tundra": 0.5
        },
        resource="spice"
    ),
    LuxuryType(
        envs={
            "hot_steppe": 2, 
            "cold_steppe": 2
        },
        resource="horses"
    ),
    LuxuryType(
        envs={
            "ice_caps": 4, 
            "tundra": 3, 
            "cold_desert": 2,
            "cold_steppe": 0.5
        },
        resource="gems"
    ),
    LuxuryType(
        envs={
            "hot_desert": 2,
            "cold_desert": 2
        },
        resource="glass"
    )
]