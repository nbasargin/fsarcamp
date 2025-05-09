"""
Geographical regions, areas, and fields during the HTERRA 2022 campaign.
"""

import shapely
import fsarcamp as fc

# Constants: identifiers for image areas / fields with intensive ground measurements
CREA_BS_QU = "CREA_BS_QU"  # CREA farm, bare soil field in April, quinoa in June (same field)
CREA_DW = "CREA_DW"  # CREA farm, durum wheat field in April
CREA_SF = "CREA_SF"  # CREA farm, sunflower field in June
CREA_MA = "CREA_MA"  # CREA farm, maize (corn) field in June
CAIONE_DW = "CAIONE_DW"  # Caione farm, two adjacent durum wheat fields in April
CAIONE_AA = "CAIONE_AA"  # Caione farm, alfalfa field in June
CAIONE_MA = "CAIONE_MA"  # Caione farm, two adjacent maize (corn) fields in June


class HTERRA22Regions(fc.GeocodedRegions):
    def __init__(self):
        super().__init__()
        self.set_geometry_longlat(
            CREA_BS_QU,
            shapely.Polygon(
                [
                    (15.49945445036212, 41.46256004052474),
                    (15.49923370053394, 41.46181944056512),
                    (15.5009002673631, 41.46133990448709),
                    (15.50131167926727, 41.46220840625713),
                    (15.499647238718, 41.46267787843318),
                ]
            ),
        )
        self.set_geometry_longlat(
            CREA_DW,
            shapely.Polygon(
                [
                    (15.49388005761628, 41.45762079746844),
                    (15.4955822069007, 41.45786827016247),
                    (15.49671861448681, 41.46057495230919),
                    (15.49611371403245, 41.46074026941788),
                    (15.49482941514133, 41.45984243393495),
                ]
            ),
        )
        self.set_geometry_longlat(
            CREA_SF,
            shapely.Polygon(
                [
                    (15.49897893406378, 41.45847770340942),
                    (15.49938015724782, 41.45849729910618),
                    (15.50001929533765, 41.45967017766751),
                    (15.49965426767975, 41.45977187127483),
                ]
            ),
        )
        self.set_geometry_longlat(
            CREA_MA,
            shapely.Polygon(
                [
                    (15.49893659570862, 41.45846242320994),
                    (15.49962944198435, 41.45978583958102),
                    (15.49908170156729, 41.45991545998699),
                    (15.49837804243928, 41.45860927626931),
                ]
            ),
        )
        caione_dw_east = shapely.Polygon(
            [
                (15.50736858915721, 41.49365182012422),
                (15.51070124342588, 41.49488531146037),
                (15.50943483341876, 41.49686379176898),
                (15.50612221845324, 41.49554014414127),
            ]
        )
        caione_dw_west = shapely.Polygon(
            [
                (15.5039005074962, 41.49201646903592),
                (15.5072521572648, 41.49358260910914),
                (15.50627767179986, 41.49508726098164),
                (15.50579943428415, 41.49491036654146),
                (15.50567156935834, 41.49494037827503),
                (15.50515878989113, 41.49569776591782),
                (15.50238165529786, 41.49431769079068),
            ]
        )
        self.set_geometry_longlat(CAIONE_DW, shapely.MultiPolygon([caione_dw_east, caione_dw_west]))
        self.set_geometry_longlat(
            CAIONE_AA,
            shapely.Polygon(
                [
                    (15.50837694655277, 41.49201095032425),
                    (15.50903717392474, 41.4909789533021),
                    (15.511388604622, 41.49177818866519),
                    (15.51070093332987, 41.49287029808573),
                ]
            ),
        )
        caione_ma_east = shapely.Polygon(
            [
                (15.50781554605022, 41.49298304110901),
                (15.50804735870737, 41.49262751558179),
                (15.51035270727568, 41.49346137156526),
                (15.51015592901653, 41.49385138143037),
            ]
        )
        caione_ma_west = shapely.Polygon(
            [
                (15.50382958088255, 41.4919279412825),
                (15.5045849009818, 41.49101757746755),
                (15.50788845445781, 41.49257372426316),
                (15.50724259508517, 41.49355385964274),
            ]
        )
        self.set_geometry_longlat(CAIONE_MA, shapely.MultiPolygon([caione_ma_east, caione_ma_west]))

