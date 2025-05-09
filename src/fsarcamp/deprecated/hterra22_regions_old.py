import fsarcamp.hterra22 as ht22
# older region definitions


def get_region_lut_coordinates(band, region_name):
    """
    Return the extent of the specified region in LUT coordinates (e.g. products geocoded with LUT).
    The region contains all soil moisture measurements for the specified field/area + border of about 50 meters.

    Return two tuples with min and max coordinates: (northing_min, northing_max), (easting_min, easting_max)
    The tuples apply to the first (northing) and second (easting) LUT axes, respectively.
    """
    c_band_regions = {
        # CREA farm
        ht22.CREA_BS_QU: ((3671, 3885), (1791, 2023)),
        ht22.CREA_DW: ((3284, 3647), (1355, 1641)),
        ht22.CREA_SF: ((3339, 3565), (1769, 1930)),
        ht22.CREA_MA: ((3338, 3585), (1708, 1895)),
        # CAIONE farn
        ht22.CAIONE_DW: ((7110, 7654), (2080, 2765)),
        ht22.CAIONE_AA: ((6976, 7225), (2547, 2823)),
        ht22.CAIONE_MA: ((6962, 7340), (2149, 2757)),
    }
    (northing_min, northing_max), (easting_min, easting_max) = c_band_regions[region_name]
    if band == "C":
        return (northing_min, northing_max), (easting_min, easting_max)
    if band == "L":
        # L-band LUT covers very similar region to C-band LUT, with a small offset
        northing_offset = 60
        easting_offset = 0
        return (northing_min + northing_offset, northing_max + northing_offset), (
            easting_min + easting_offset,
            easting_max + easting_offset,
        )
    raise Exception(f"Unsupported band {band}")


def get_slc_shape(band):
    return {"L": (27136, 4536), "C": (54016, 9072)}[band]


def get_region_radar_coordinates(band, region_name):
    """
    Return the extent of the specified region in radar coordinates (e.g. SLC files).
    The region contains all soil moisture measurements for the specified field/area + border of about 50 meters.
    Return two tuples with min and max coordinates: (az_min, az_max), (rg_min, rg_max).
    The tuples apply to the first (azimuth) and second (range) SLC axes, respectively.
    Usage: (az_min, az_max), (rg_min, rg_max) = get_region_radar_coordinates(...)
    """
    region_definitions = {
        "L": {
            ht22.CREA_BS_QU: ((8783, 9289), (1492, 1811)),
            ht22.CREA_DW: ((7833, 8706), (1012, 1378)),
            ht22.CREA_SF: ((7984, 8525), (1466, 1703)),
            ht22.CREA_MA: ((7979, 8570), (1396, 1662)),
            ht22.CAIONE_DW: ((17013, 18336), (1850, 2746)),
            ht22.CAIONE_AA: ((16717, 17316), (2428, 2820)),
            ht22.CAIONE_MA: ((16661, 17589), (1932, 2736)),
        },
        "C": {
            ht22.CREA_BS_QU: ((17303, 18315), (2980, 3619)),
            ht22.CREA_DW: ((15414, 17156), (2021, 2752)),
            ht22.CREA_SF: ((15707, 16788), (2928, 3402)),
            ht22.CREA_MA: ((15699, 16879), (2790, 3321)),
            ht22.CAIONE_DW: ((33750, 36386), (3697, 5490)),
            ht22.CAIONE_AA: ((33149, 34345), (4853, 5638)),
            ht22.CAIONE_MA: ((33045, 34891), (3860, 5468)),
        },
    }
    (az_min, az_max), (rg_min, rg_max) = region_definitions[band][region_name]
    return (az_min, az_max), (rg_min, rg_max)


def get_soil_texture_by_region(region_name):
    """Get soil texture (sand and clay values) for the specified region."""
    if region_name in [ht22.CREA_BS_QU, ht22.CREA_DW, ht22.CREA_SF, ht22.CREA_MA]:
        crea_sand, crea_clay = 26.8, 32.4
        return crea_sand, crea_clay
    if region_name in [ht22.CAIONE_DW, ht22.CAIONE_AA, ht22.CAIONE_MA]:
        caione_sand, caione_clay = 24.5, 38.2
        return caione_sand, caione_clay
    raise Exception(f"Unknown region name: {region_name}")
