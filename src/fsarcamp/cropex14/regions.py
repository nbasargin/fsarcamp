"""
Geographical regions, areas, and fields during the CROPEX 2014 campaign.
"""

# Constants: identifiers for image areas / fields

CORN_C1 = "CORN_C1" # corn field next to the meteorological station
CORN_C2 = "CORN_C2" # corn field on the big field
CORN_C3 = "CORN_C3"
CORN_C5 = "CORN_C5"
CORN_C6 = "CORN_C6"
WHEAT_W1 = "WHEAT_W1"
WHEAT_W2 = "WHEAT_W2"
WHEAT_W4 = "WHEAT_W4"
WHEAT_W5 = "WHEAT_W5"
WHEAT_W7 = "WHEAT_W7"
WHEAT_W10 = "WHEAT_W10" # triangular wheat field, X & C bands missing for 14cropex1503, L band has issues with 14cropex1114
BARLEY_B1 = "BARLEY_B1"
RAPESEED_R1 = "RAPESEED_R1"
SUGAR_BEET_SB2 = "SUGAR_BEET_SB2"

def field_to_long_lat_point(field_id):
    """
    CROPEX 2014 field ID to longitude-latitude coordinates.
    Returns a (longitude, latitude) tuple defining a point located on the field.
    """
    return {
        CORN_C1: (12.874096, 48.694220),
        CORN_C2: (12.873469, 48.696072),
        CORN_C3: (12.875444, 48.697499),
        CORN_C5: (12.872011, 48.702637),
        CORN_C6: (12.869678, 48.703700),
        WHEAT_W1: (12.877348, 48.697276),
        WHEAT_W2: (12.873871, 48.700504),
        WHEAT_W4: (12.863705, 48.701121),
        WHEAT_W5: (12.868541, 48.701644),
        WHEAT_W7: (12.863067, 48.697123),
        WHEAT_W10: (12.854872, 48.690192),
        BARLEY_B1: (12.874718, 48.698977),
        RAPESEED_R1: (12.868209, 48.687849),
        SUGAR_BEET_SB2: (12.8630, 48.6947),
    }[field_id]
