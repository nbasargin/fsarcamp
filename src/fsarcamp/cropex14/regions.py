"""
Geographical regions, areas, and fields during the CROPEX 2014 campaign.
"""
import shapely
import fsarcamp as fc
import fsarcamp.cropex14 as cr14

# Constants: identifiers for image areas / fields

CORN_C1 = "CORN_C1" # corn field next to the meteorological station
CORN_C2 = "CORN_C2" # corn field on the big field
CORN_C3 = "CORN_C3"
CORN_C4 = "CORN_C4"
CORN_C5 = "CORN_C5"
CORN_C6 = "CORN_C6"
CORN_C7 = "CORN_C7"
WHEAT_W1 = "WHEAT_W1"
WHEAT_W2 = "WHEAT_W2"
WHEAT_W4 = "WHEAT_W4"
WHEAT_W5 = "WHEAT_W5"
WHEAT_W7 = "WHEAT_W7"
WHEAT_W10 = "WHEAT_W10" # triangular wheat field, X & C bands missing for 14cropex1503, L band has issues with 14cropex1114
BARLEY_B1 = "BARLEY_B1"
BARLEY_B2 = "BARLEY_B1"
RAPESEED_R1 = "RAPESEED_R1"
RAPESEED_R2 = "RAPESEED_R2"
SUGAR_BEET_SB2 = "SUGAR_BEET_SB2"

class CROPEX14Regions:
    def __init__(self):
        self._polygons = {}
        self._polygons[CORN_C1] = shapely.Polygon([
            (12.87565153019545, 48.695062374084),
            (12.87443964709708, 48.69475621158275),
            (12.87432120739955, 48.69492272164158),
            (12.87236475373997, 48.69447766408314),
            (12.87331081373207, 48.6931298725073),
            (12.87431769896898, 48.69330317558468),
            (12.87518800908378, 48.69373122750969),
            (12.87515369850598, 48.69395209895048),
            (12.87610118244794, 48.694325946684),
        ])
        self._polygons[CORN_C2] = shapely.Polygon([
            (12.87053464083966, 48.69431126433746),
            (12.87556291600652, 48.69538260549086),
            (12.87434155079981, 48.69725743323961),
            (12.86932052746421, 48.69624297290534),
        ])
        self._polygons[CORN_C3] = shapely.Polygon([
            (12.87423206863921, 48.69786699422387),
            (12.87503292015596, 48.6966669981401),
            (12.87649710017948, 48.69710797546402),
            (12.87579144333636, 48.69813526444589),
            (12.87521776635001, 48.69830026522834),
        ])
        self._polygons[CORN_C4] = shapely.Polygon([
            (12.86667679209596, 48.70085493760387),
            (12.86591512448132, 48.7000202848476),
            (12.86669914307551, 48.69917102763334),
            (12.86729643261144, 48.69917343926319),
            (12.87134371151156, 48.69997614248018),
            (12.86987469287968, 48.7013229189301),
            (12.86742964961173, 48.70011583037773),
        ])
        self._polygons[CORN_C5] = shapely.Polygon([
            (12.86952828295785, 48.70290591217594),
            (12.87121153062606, 48.70126457316773),
            (12.87456422478044, 48.70271679005035),
            (12.8736763092779, 48.70471900973932),
        ])
        self._polygons[CORN_C6] = shapely.Polygon([
            (12.86934953566826, 48.70303315653275),
            (12.87105100419957, 48.70370490751993),
            (12.86905222521365, 48.70545711933683),
            (12.86811134760546, 48.70409895533842),
        ])
        self._polygons[CORN_C7] = shapely.Polygon([
            (12.87002062244355, 48.70471930687006),
            (12.8711311707166, 48.70375623928727),
            (12.8720547522413, 48.70413807017619),
            (12.87084843387136, 48.70706999494057),
            (12.86998980042929, 48.7068711579618),
            (12.86946422990737, 48.7061225403409),
        ])        
        self._polygons[WHEAT_W1] = shapely.Polygon([
            (12.87739985741139, 48.69598564066508),
            (12.87793579026339, 48.69613446792475),
            (12.87771151438843, 48.69649164969105),
            (12.87856882222082, 48.69672653589513),
            (12.87702009676442, 48.69895014064039),
            (12.87612791670463, 48.69866196558353),
            (12.87592342869237, 48.69809962081447),
        ])
        self._polygons[WHEAT_W2] = shapely.Polygon([
            (12.87319707351549, 48.69932102127743),
            (12.87555163354478, 48.70040064203708),
            (12.87485616939753, 48.70191910704688),
            (12.87186062649847, 48.70063839588659),
        ])
        self._polygons[WHEAT_W4] = shapely.Polygon([
            (12.86222682887729, 48.69912784357434),
            (12.8664376546897, 48.69916050940325),
            (12.86569488842339, 48.69998727899745),
            (12.86657352739587, 48.70095425806488),
            (12.86478192149839, 48.70250432138592),
            (12.86618938234914, 48.70491424986728),
            (12.86446331189873, 48.705644801373),
            (12.8635819196304, 48.70645694167804),
            (12.86280005754055, 48.70486032378749),
            (12.86235390880689, 48.7031640587203),
            (12.86213582356656, 48.70214214838691),
            (12.86277302226429, 48.70182676265127),
            (12.86280063223434, 48.70129285719339),
            (12.86233896194054, 48.7009923422068),
        ])
        self._polygons[WHEAT_W5] = shapely.Polygon([
            (12.86748637224028, 48.70037212837406),
            (12.87018372544983, 48.70174044377272),
            (12.86880733336799, 48.70301639443337),
            (12.86682948479329, 48.70098316867468),
        ])
        self._polygons[WHEAT_W7] = shapely.Polygon([
            (12.86266622349172, 48.69575218179349),
            (12.86525834682962, 48.69631516092447),
            (12.86354512379898, 48.69892852467287),
            (12.86207128888195, 48.69886994059245),
            (12.8614750192452, 48.69768989793414),
        ])
        self._polygons[WHEAT_W10] = shapely.Polygon([
            (12.85358393267424, 48.69018959550732),
            (12.85423244864385, 48.68940177515939),
            (12.85835339911517, 48.68983552647251),
            (12.85573788299581, 48.69077907772343),
            (12.85352742431068, 48.69122816090613),
        ])
        self._polygons[BARLEY_B1] = shapely.Polygon([
            (12.8742032758246, 48.69799720324459),
            (12.87512474762211, 48.69841723744404),
            (12.87535239192262, 48.6988463280643),
            (12.87600948742225, 48.69879788040961),
            (12.87624378893904, 48.6988870174057),
            (12.87558782047011, 48.70034852856248),
            (12.87327656097556, 48.69924714500875),
        ])
        self._polygons[BARLEY_B2] = shapely.Polygon([
            (12.86426760041793, 48.69819788599162),
            (12.86783801910645, 48.69814731121294),
            (12.8677511540747, 48.69829182534194),
            (12.86418759777304, 48.69833445676718),
        ])
        self._polygons[RAPESEED_R1] = shapely.Polygon([
            (12.86591386891839, 48.68862240468886),
            (12.86654250137362, 48.68815504559571),
            (12.86716122884865, 48.68795791112865),
            (12.86768453832656, 48.68761320259622),
            (12.86789571135073, 48.6870794209554),
            (12.8706222240055, 48.68762437837421),
            (12.86951331444476, 48.68805702767348),
            (12.86801812028444, 48.68842491934695),
            (12.86660592919214, 48.68865726427504),
        ])
        self._polygons[RAPESEED_R2] = shapely.Polygon([
            (12.85918435041684, 48.68817800478436),
            (12.86104988131144, 48.68811698195302),
            (12.86085109239522, 48.68955652792251),
            (12.85904583579791, 48.68968137298259),
        ])
        self._polygons[SUGAR_BEET_SB2] = shapely.Polygon([
            (12.8614183554764, 48.69323870062198),
            (12.86657653507957, 48.69433842589564),
            (12.86538213489877, 48.69614868522724),
            (12.86010539487434, 48.69501375600024),
        ])

    def get_geometry_longlat(self, region_name: str):
        """ Get region geometry (polygon) in longitude-latitude coordinates. """
        return self._polygons[region_name]

    def get_geometry_lutindices(self, region_name: str, campaign: cr14.CROPEX14Campaign, pass_name: str, band: str):
        """ Get region geometry (polygon) where each vertex represents indices of the F-SAR GTC lookup table. """
        fsar_pass = campaign.get_pass(pass_name, band)
        lut = fsar_pass.load_gtc_sr2geo_lut()
        poly_longlat = self.get_geometry_longlat(region_name)
        poly_eastnorth = fc.geocode_geometry_longlat_to_eastnorth(poly_longlat, lut.projection)
        poly_lutindices = fc.geocode_geometry_eastnorth_to_lutindices(poly_eastnorth, lut)
        return poly_lutindices

    def get_geometry_azrg(self, region_name: str, campaign: cr14.CROPEX14Campaign, pass_name: str, band: str):
        """ Get region geometry (polygon) in azimuth-range coordinates of a specific F-SAR pass. """
        poly_long_lat = self.get_geometry_longlat(region_name)
        fsar_pass = campaign.get_pass(pass_name, band)
        lut = fsar_pass.load_gtc_sr2geo_lut()
        return fc.geocode_geometry_longlat_to_azrg(poly_long_lat, lut)

    def define_geometry(self, region_name: str, geometry_longlat: shapely.Geometry):
        """ Define a custom region in longitude-latitude coordinates. """
        self._polygons[region_name] = geometry_longlat
