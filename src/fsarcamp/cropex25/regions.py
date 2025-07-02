"""
Geographical regions, areas, and fields during the CROPEX 2025 campaign.
"""

import shapely

# Eitelsried test site
EITELSRIED_MAIZE = "CR25-EITELSRIED-MAIZE"  # Region of the Eitelsried maize field covered by soil moisture measurements
EITELSRIED_POTATO = (
    "CR25-EITELSRIED-POTATO"  # Region of the Eitelsried potato field covered by soil moisture measurements
)
EITELSRIED_WHEAT = "CR25-EITELSRIED-WHEAT"  # Region of the Eitelsried wheat field covered by soil moisture measurements

# Puch test site definitions to be added

# Ditionary of polygons in longlat coordinates
CROPEX25Regions = {
    EITELSRIED_MAIZE: shapely.Polygon(
        [
            (11.17278645800869, 48.18502314439328),
            (11.17350812287046, 48.18533410463681),
            (11.17575055405398, 48.18603473687025),
            (11.17622832249746, 48.18624340815962),
            (11.17575118394909, 48.18771418684338),
            (11.17437262413883, 48.18867261913626),
            (11.17309875903978, 48.18801851173351),
            (11.17224292229551, 48.1870489939315),
            (11.17259093857684, 48.18509547481131),
        ]
    ),
    EITELSRIED_POTATO: shapely.Polygon(
        [
            (11.17278236457158, 48.184445194127),
            (11.17350421883094, 48.18445127163915),
            (11.17419613396293, 48.18434141285729),
            (11.18068775882051, 48.18586493367545),
            (11.18066893971662, 48.18669982899348),
            (11.1783290482405, 48.18617056616241),
            (11.17735890646289, 48.18648126004705),
            (11.17641604518258, 48.18616649245348),
            (11.17568606758535, 48.18593014618482),
            (11.17447266529804, 48.18558310574561),
            (11.17356657994018, 48.18528528587626),
            (11.17294867118114, 48.18502253862198),
            (11.17281083826994, 48.18484913217939),
        ]
    ),
    EITELSRIED_WHEAT: shapely.Polygon(
        [
            (11.1656491314938, 48.18142015022188),
            (11.16579405997857, 48.18009374605076),
            (11.16887186174786, 48.18065504855313),
            (11.16860243616368, 48.18158432340719),
            (11.16896274236345, 48.18269397442587),
            (11.16840499817774, 48.18297604799496),
            (11.16779513167568, 48.182847760896),
            (11.1671710032665, 48.18284265434719),
            (11.16535329596632, 48.18278574918555),
        ]
    ),
}
