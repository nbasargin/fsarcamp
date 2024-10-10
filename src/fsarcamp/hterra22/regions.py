"""
Geographical regions, areas, and fields during the HTERRA 2022 campaign.
"""
import shapely
import fsarcamp as fc
import fsarcamp.hterra22 as ht22

# Constants: identifiers for image areas / fields with intensive ground measurements
CREA_BS_QU = "CREA-BS-QU" # CREA farm, bare soil field in April, quinoa in June (same field)
CREA_DW = "CREA-DW" # CREA farm, durum wheat field in April
CREA_SF = "CREA-SF" # CREA farm, sunflower field in June
CREA_MA = "CREA-MA" # CREA farm, maize (corn) field in June
CAIONE_DW = "CAIONE-DW" # Caione farm, two adjacent durum wheat fields in April
CAIONE_AA = "CAIONE-AA" # Caione farm, alfalfa field in June
CAIONE_MA = "CAIONE-MA" # Caione farm, two adjacent maize (corn) fields in June

class HTERRA22Regions:
    def __init__(self):
        self._polygons = {}
        self._polygons[CREA_BS_QU] = shapely.Polygon([
            (15.49945445036212, 41.46256004052474),
            (15.49923370053394, 41.46181944056512),
            (15.5009002673631, 41.46133990448709),
            (15.50131167926727, 41.46220840625713),
            (15.499647238718, 41.46267787843318),
            (15.49945445036212, 41.46256004052474),
        ])
        self._polygons[CREA_DW] = shapely.Polygon([
            (15.49388005761628, 41.45762079746844),
            (15.4955822069007, 41.45786827016247),
            (15.49671861448681, 41.46057495230919),
            (15.49611371403245, 41.46074026941788),
            (15.49482941514133, 41.45984243393495),
            (15.49388005761628, 41.45762079746844),
        ])
        self._polygons[CREA_SF] = shapely.Polygon([
            (15.49897893406378, 41.45847770340942),
            (15.49938015724782, 41.45849729910618),
            (15.50001929533765, 41.45967017766751),
            (15.49965426767975, 41.45977187127483),
            (15.49897893406378, 41.45847770340942),
        ])
        self._polygons[CREA_MA] = shapely.Polygon([
            (15.49892760581621, 41.45847176078325),
            (15.49960538119785, 41.45978058291423),
            (15.49912074996714, 41.45990655774668),
            (15.49841367659705, 41.45862236417256),
            (15.49892760581621, 41.45847176078325),
        ])
        caione_dw_east = shapely.Polygon([
            (15.50736858915721, 41.49365182012422),
            (15.5104830654899, 41.49478649669674),
            (15.50943483341876, 41.49686379176898),
            (15.50612221845324, 41.49554014414127),
            (15.50736858915721, 41.49365182012422),
        ])
        caione_dw_west = shapely.Polygon([
            (15.5039005074962, 41.49201646903592),
            (15.5072521572648, 41.49358260910914),
            (15.50628757108639, 41.49503832801321),
            (15.50572584065794, 41.49479330418192),
            (15.50515878989113, 41.49569776591782),
            (15.50238165529786, 41.49431769079068),
            (15.5039005074962, 41.49201646903592),
        ])
        self._polygons[CAIONE_DW] = shapely.MultiPolygon([caione_dw_east, caione_dw_west])
        self._polygons[CAIONE_AA] = shapely.Polygon([
            (15.50839036808084, 41.49194311029541),
            (15.50905268432904, 41.49098562845683),
            (15.51108977089435, 41.49174051516981),
            (15.51054757435483, 41.49273309952633),
            (15.50839036808084, 41.49194311029541),
        ])
        caione_ma_east = shapely.Polygon([
            (15.50781554605022, 41.49298304110901),
            (15.50802732558535, 41.49264709115235),
            (15.51031140489874, 41.49350210135282),
            (15.51015592901653, 41.49385138143037),
            (15.50781554605022, 41.49298304110901),
        ])
        caione_ma_west = shapely.Polygon([
            (15.50388295328997, 41.49193485226784),
            (15.50469666786303, 41.49098915417986),
            (15.50788845445781, 41.49257372426316),
            (15.50724259508517, 41.49355385964274),
            (15.50388295328997, 41.49193485226784),
        ])
        self._polygons[CAIONE_MA] = shapely.MultiPolygon([caione_ma_east, caione_ma_west])
    
    def get_geometry_longlat(self, region_name: str):
        """ Get region geometry (polygon or multipolygon) in longitude-latitude coordinates. """
        return self._polygons[region_name]

    def get_geometry_azrg(self, region_name: str, campaign: ht22.HTERRA22Campaign, pass_name: str, band: str):
        """
        Get region geometry (polygon or multipolygon) in azimuth-range coordinates for a specific band.
        Pass name can be any HTERRA pass since all passes of the same band have the same coordinate system.
        """
        poly_long_lat = self.get_geometry_longlat(region_name)
        fsar_pass = campaign.get_pass(pass_name, band)
        lut = fsar_pass.load_gtc_sr2geo_lut()
        return fc.geocode_geometry_longlat_to_azrg(poly_long_lat, lut)

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
        CREA_BS_QU: ((3671, 3885), (1791, 2023)),
        CREA_DW: ((3284, 3647), (1355, 1641)),
        CREA_SF: ((3339, 3565), (1769, 1930)),
        CREA_MA: ((3338, 3585), (1708, 1895)),
        # CAIONE farn
        CAIONE_DW: ((7110, 7654), (2080, 2765)),
        CAIONE_AA: ((6976, 7225), (2547, 2823)),
        CAIONE_MA: ((6962, 7340), (2149, 2757)),
    }
    (northing_min, northing_max), (easting_min, easting_max) = c_band_regions[region_name]
    if band == "C":
        return (northing_min, northing_max), (easting_min, easting_max)
    if band == "L":
        # L-band LUT covers very similar region to C-band LUT, with a small offset
        northing_offset = 60
        easting_offset = 0
        return (northing_min + northing_offset, northing_max + northing_offset), (easting_min + easting_offset, easting_max + easting_offset)
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
            CREA_BS_QU: ((8783, 9289), (1492, 1811)),
            CREA_DW: ((7833, 8706), (1012, 1378)),
            CREA_SF: ((7984, 8525), (1466, 1703)),
            CREA_MA: ((7979, 8570), (1396, 1662)),
            CAIONE_DW: ((17013, 18336), (1850, 2746)),
            CAIONE_AA: ((16717, 17316), (2428, 2820)),
            CAIONE_MA: ((16661, 17589), (1932, 2736)),
        },
        "C": {
            CREA_BS_QU: ((17303, 18315), (2980, 3619)),
            CREA_DW: ((15414, 17156), (2021, 2752)),
            CREA_SF: ((15707, 16788), (2928, 3402)),
            CREA_MA: ((15699, 16879), (2790, 3321)),
            CAIONE_DW: ((33750, 36386), (3697, 5490)),
            CAIONE_AA: ((33149, 34345), (4853, 5638)),
            CAIONE_MA: ((33045, 34891), (3860, 5468)),
        },
    }
    (az_min, az_max), (rg_min, rg_max) = region_definitions[band][region_name]
    return (az_min, az_max), (rg_min, rg_max)

def get_soil_texture_by_region(region_name):
    """ Get soil texture (sand and clay values) for the specified region. """
    if region_name in [CREA_BS_QU, CREA_DW, CREA_SF, CREA_MA]:
        crea_sand, crea_clay = 26.8, 32.4
        return crea_sand, crea_clay
    if region_name in [CAIONE_DW, CAIONE_AA, CAIONE_MA]:
        caione_sand, caione_clay = 24.5, 38.2
        return caione_sand, caione_clay
    raise Exception(f"Unknown region name: {region_name}")
