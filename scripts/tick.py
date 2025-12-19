from scripts.nations import Nation, nation_list, Subdivision, Econ, Gov

def tick():
    for nation in nation_list.values():
        gov = nation.gov
        gov.event_update()
        for system in gov.systems:
            gov.system_pi(system)
        gov.influence = gov.influence_cap - gov.upkeep()