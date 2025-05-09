"""
Data loader for the CROPEX 2014 field map.
Provides field polygons and crop types.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from rasterio.features import rasterize
import fsarcamp as fc
import fsarcamp.cropex14 as cr14


class CROPEX14FieldMap:
    def __init__(self, shapefile_path, cropex14campaign: cr14.CROPEX14Campaign):
        self.shapefile_path = shapefile_path
        self.cropex14campaign = cropex14campaign
        # crop codes taken from "a6_codierung_fnn.pdf", more codes are available there
        self._crop_code_to_name_dict = {
            115: "Winter wheat",  # Winterweizen
            116: "Summer wheat",  # Sommerweizen
            131: "Winter barley",  # Wintergerste
            132: "Summer barley",  # Sommergerste
            140: "Oat",  # Hafer
            156: "Winter triticale",  # Wintertriticale
            157: "Summer triticale",  # Sommertriticale
            171: "Grain maize",  # Körnermais
            172: "Corn-Cob-Mix",  # Corn-Cob-Mix
            210: "Peas",  # Erbsen
            220: "Beans",  # Ackerbohnen
            311: "Winter rapeseed",  # Winterraps
            320: "Sunflowers",  # Sonnenblumen
            411: "Silage maize",  # Silomais
            422: "Clover / alfalfa mix",  # Kleegras, Klee-/Luzernegras-Gemisch
            423: "Alfalfa",  # Luzerne
            424: "Agricultural grass",  # Ackergras
            426: "Other cereals as whole plant silage",  # Sonstiges Getreide als Ganzpflanzensilage
            441: "Green areas",  # Grünlandeinsaat (Wiesen, Mähweiden, Weiden)
            451: "Grasslands (incl Orchards)",  # Wiesen (einschl. Streuobstwiesen)
            452: "Mowed pastures",  # Mähweiden
            453: "Pastures",  # Weiden
            460: "Summer pastures for sheep walking",  # Sommerweiden für Wanderschafe
            560: "Set aside arable land",  # Stillgelegte Ackerflächen i. R. von AUM
            567: "Disused permanent grassland",  # Stillgelegte Dauergrünlandflächen i. R. von AUM
            591: "Farmland out of production",  # Ackerland aus der Erzeugung genommen
            592: "Set aside Grassland",  # Dauergrünland aus der Erzeugung genommen
            611: "Potatoes",  # Frühkartoffeln
            612: "Other potatoes",  # Sonstige Speisekartoffeln
            613: "Industrial potatoes",  # Industriekartoffeln
            615: "Seed potatoes",  # Pflanzkartoffeln (alle Verwertungsformen)
            619: "Other potatoes",  # Sonstige Kartoffeln (z. B. Futterkartoffeln)
            640: "Starch potatoes",  # Stärkekartoffeln (Vertragsanbau)
            620: "Sugar beet",  # Zuckerrüben (ohne Samenvermehrung)
            630: "Jerusalem artichokes",  # Topinambur
            710: "Vegetables",  # Feldgemüse
            720: "Outdoor vegetables",  # Gemüse im Freiland (gärtnerischer Anbau)
            811: "Pome and stone fruit",  # Kern- und Steinobst
            812: "Orchard (without meadow / arable land)",  # Streuobst (ohne Wiesen-/Ackernutzung)
            824: "Hazelnuts",  # Haselnüsse
            846: "Christmas tree plantations outside the forest",  # Christbaumkulturen außerhalb des Waldes
            848: "Short rotation forest trees (rotation period max. 20 years)",  # Schnellwüchsige Forstgehölze (Umtriebszeit max. 20 Jahre)
            851: "Vines cultivated",  # Bestockte Rebfläche
            896: "Miscanthus",  # Chinaschilf (Miscanthus)
            897: "Other perennial energy crops",  # Sonstige mehrjährige Energiepflanzen (z. B. Riesenweizengras, Rutenhirse, Durchwachsene Silphie, Igniscum)
            890: "Other permanent crops",  # Sonstige Dauerkulturen
            920: "House garden",  # Nicht landw. genutzte Haus- und Nutzgärten
            980: "Sudan grass",  # Sudangras, Hirse
            990: "Other non used area",  # Sonstige nicht landw. genutzte Fläche
            996: "Storage field",  # Unbefestigte Mieten, Stroh-, Futter- und Dunglagerplätze (maximal ein Jahr) auf Ackerland
        }

    def _translate_to_lut_indices(self, easting_northing_shape, lut: fc.Geo2SlantRange):
        """
        Translate a shape in easting northing coordinates to the LUT frame of refence to get the pixel indices.
        Pixel spacing is 1 meter for the CROPEX14 campaign, no scaling is therefore needed.
        """
        easting_northing_lut_shape = shapely.affinity.translate(
            easting_northing_shape, xoff=-lut.min_east, yoff=-lut.min_north
        )
        minx, miny, maxx, maxy = easting_northing_lut_shape.bounds
        lut_northing_max, lut_easting_max = lut.lut_az.shape
        shape_valid = (minx >= 0) & (miny >= 0) & (maxx < lut_easting_max - 1) & (maxy < lut_northing_max - 1)
        if shape_valid:
            return easting_northing_lut_shape
        return None

    def _geocode_shape(self, lut_shape, lut: fc.Geo2SlantRange):
        """
        Geocode a polygon or a multi-polygon from LUT to SLC pixel indices.
        Coordinates for each polygon point are converted individually using the LUT.
        """
        if lut_shape is None:
            return None
        elif lut_shape.geom_type == "MultiPolygon":
            geocoded_polys = [self._geocode_shape(poly, lut) for poly in lut_shape.geoms]
            valid_polys = [poly for poly in geocoded_polys if poly is not None]
            if len(valid_polys) == 0:
                return None  # no valid polygons
            return shapely.MultiPolygon(valid_polys)
        elif lut_shape.geom_type == "Polygon":
            lut_northing_max, lut_easting_max = lut.lut_az.shape
            easting_lut, northing_lut = lut_shape.exterior.coords.xy
            lut_east_idx = np.rint(easting_lut).astype(np.int64)
            lut_north_idx = np.rint(northing_lut).astype(np.int64)
            invalid_indices = (
                (lut_east_idx < 0)
                | (lut_east_idx >= lut_easting_max)
                | (lut_north_idx < 0)
                | (lut_north_idx >= lut_northing_max)
            )
            if np.any(invalid_indices):
                return None  # some points invalid: outside of LUT
            point_az = lut.lut_az[lut_north_idx, lut_east_idx]
            point_rg = lut.lut_rg[lut_north_idx, lut_east_idx]
            if np.any(np.isnan(point_az)) or np.any(np.isnan(point_rg)) or np.any(point_az < 0) or np.any(point_rg < 0):
                return None  # some points invalid: outside of SLC
            return shapely.Polygon(np.stack((point_rg, point_az), axis=1))
        else:
            raise RuntimeError(f"Unknown geometry type: {lut_shape.geom_type}")

    def _geocode_dataframe(self, field_df, pass_name, band):
        """
        Geocode all fields in the dataframe to LUT and SLC coordinates.
        Field geometry is taken from the "poly_easting_northing" column.
        Two new columns are added: "poly_easting_northing_lut" and "poly_range_azimuth".
        """
        fsar_pass = self.cropex14campaign.get_pass(pass_name, band)
        lut = fsar_pass.load_gtc_sr2geo_lut()
        # translate each polygon to the LUT indices, then to SLC indices
        poly_e_n = field_df["poly_easting_northing"]
        poly_e_n_lut = [self._translate_to_lut_indices(en_poly, lut) for en_poly in poly_e_n.to_list()]
        poly_rg_az = [self._geocode_shape(lut_poly, lut) for lut_poly in poly_e_n_lut]
        geocoded_df = field_df.assign(
            poly_easting_northing_lut=gpd.GeoSeries(
                poly_e_n_lut, index=field_df.index
            ),  # LUT pixel indices, easting northing
            poly_range_azimuth=gpd.GeoSeries(poly_rg_az, index=field_df.index),  # SLC pixel indices, azimuth range
        )
        return geocoded_df

    def load_fields(self, pass_name=None, band=None):
        gdf = gpd.read_file(self.shapefile_path)
        poly_shapefile = gpd.GeoSeries(
            shapely.force_2d(gdf.geometry), crs=gdf.crs
        )  # EPSG:31468 (3-degree Gauss-Kruger zone 4)
        poly_long_lat = poly_shapefile.to_crs(4326)  # EPSG:4326 (longitude - latitude)
        poly_e_n = poly_shapefile.to_crs(32633)  # EPSG:32633 (UTM zone 33N)
        processed_df = gpd.GeoDataFrame(
            {
                "num_crop_types": gdf["nu14_anz_n"],  # number of different crop types on that field
                # crop code (defines what was planted) and the corresponding area, up to 5 different crops
                "crop_code_1": pd.to_numeric(gdf["nu14_n_c1"]),
                "crop_area_1": gdf["nu14_f_c1"],
                "crop_code_2": pd.to_numeric(gdf["nu14_n_c2"]),
                "crop_area_2": gdf["nu14_f_c2"],
                "crop_code_3": pd.to_numeric(gdf["nu14_n_c3"]),
                "crop_area_3": gdf["nu14_f_c3"],
                "crop_code_4": pd.to_numeric(gdf["nu14_n_c4"]),
                "crop_area_4": gdf["nu14_f_c4"],
                "crop_code_5": pd.to_numeric(gdf["nu14_n_c5"]),
                "crop_area_5": gdf["nu14_f_c5"],
                # geometry: field polygon in different projections
                "poly_shapefile": poly_shapefile,  # shapefile geometry (3-degree Gauss-Kruger zone 4)
                "poly_longitude_latitude": poly_long_lat,  # longitude latitude
                "poly_easting_northing": poly_e_n,  # LUT easting northing (UTM zone 33N)
            }
        )
        if band is None or pass_name is None:
            return processed_df
        return self._geocode_dataframe(processed_df, pass_name, band)

    def load_field_by_id(self, field_id, pass_name=None, band=None):
        """
        Load a field by ID. Returns a dataframe with the same columns as `load_fields`.
        Some IDs represent several fields (or field parts) grouped together, all corresponding polygons are returned.
        """
        fields = self.load_fields()
        # look up field polygons that contain specific points
        corn_c1_side = (12.875333, 48.694533)  # C1 field, polygon on the side
        corn_c1_center = (12.874096, 48.694220)  # C1 field, polygon in the center
        corn_c2 = (12.873469, 48.696072)  # C2 field
        points_on_field = {
            cr14.CORN_C1: [corn_c1_center, corn_c1_side],
            cr14.CORN_C2: [corn_c2],
            cr14.CORN_C3: [(12.875444, 48.697499)],
            cr14.CORN_C5: [(12.872011, 48.702637)],
            cr14.CORN_C6: [(12.869678, 48.703700)],
            cr14.WHEAT_W1: [(12.877348, 48.697276)],
            cr14.WHEAT_W2: [(12.873871, 48.700504)],
            cr14.WHEAT_W4: [(12.863705, 48.701121)],
            cr14.WHEAT_W5: [(12.868541, 48.701644)],
            cr14.WHEAT_W7: [(12.863067, 48.697123)],
            cr14.WHEAT_W10: [(12.854872, 48.690192)],
            cr14.BARLEY_B1: [(12.874718, 48.698977)],
            cr14.RAPESEED_R1: [(12.868209, 48.687849)],
            cr14.SUGAR_BEET_SB2: [(12.8630, 48.6947)],
        }[field_id]
        filtered_fields = pd.concat(
            [fields[fields["poly_longitude_latitude"].contains(shapely.Point(point))] for point in points_on_field]
        )
        if band is None or pass_name is None:
            return filtered_fields
        return self._geocode_dataframe(filtered_fields, pass_name, band)

    def _create_field_raster(
        self, field_df: gpd.GeoDataFrame, data_column_name, geometry_column_name, out_shape, invalid_value
    ):
        """
        Rasterize field data (in the `data_column_name` column) to field geometry (in the `geometry_column_name` column).
        Pixels that do not belong to any field are filled with `invalid_value`.
        Arguments:
            field_df - dataframe with the lut polygons ("poly_easting_northing_lut" column)
            data_column_name - name of the column in the dataframe where to take the data for each field
            geometry_column_name - name of the column with field geometry (polygons)
            out_shape - shape of the raster
            invalid_value - value to fill pixels that do not belong to any field
        """
        data_dtype = field_df[data_column_name].dtype
        rasterized_values = np.full(out_shape, fill_value=invalid_value, dtype=data_dtype)
        # group all fields with the same value into lists
        value_to_fields = dict()  # dict: data -> list of field polygons/shapes
        for row in field_df.itertuples():
            field_value = getattr(row, data_column_name)
            field_lut_poly = getattr(row, geometry_column_name)
            if field_lut_poly is None:
                continue
            if not field_value in value_to_fields:
                value_to_fields[field_value] = [field_lut_poly]
            else:
                value_to_fields[field_value].append(field_lut_poly)
        # rasterize fields with the same value together
        for field_value, field_polys in value_to_fields.items():
            rasterized_values = rasterize(
                field_polys, out_shape=out_shape, default_value=field_value, out=rasterized_values
            )
        return rasterized_values

    def create_field_lut_raster(
        self, field_df: gpd.GeoDataFrame, data_column_name, pass_name, band, invalid_value=np.nan
    ):
        """
        Rasterize field data (stored in the `data_column_name` column) to the LUT raster.
        Pixels that do not belong to any field are filled with `invalid_value`.
        Arguments:
            field_df - dataframe with data and lut geometry columns
            data_column_name - name of the column in the dataframe where to take the data for each field
            pass_name, band - F-SAR pass name and band (most passes have the same LUT coordinates but there are exceptions)
            invalid_value - value to fill pixels that do not belong to any field
        """
        lut = self.cropex14campaign.get_pass(pass_name, band).load_gtc_sr2geo_lut()
        return self._create_field_raster(
            field_df, data_column_name, "poly_easting_northing_lut", lut.lut_az.shape, invalid_value
        )

    def create_field_slc_raster(
        self, field_df: gpd.GeoDataFrame, data_column_name, pass_name, band, invalid_value=np.nan
    ):
        """
        Rasterize field data (stored in the `data_column_name` column) to the SLC raster.
        Pixels that do not belong to any field are filled with `invalid_value`.
        Arguments:
            field_df - dataframe with data and slc geometry columns
            data_column_name - name of the column in the dataframe where to take the data for each field
            pass_name, band - F-SAR pass name and band (each pass can have different SLC coordinate system)
            invalid_value - value to fill pixels that do not belong to any field
        """
        slc = self.cropex14campaign.get_pass(pass_name, band).load_rgi_slc("hh")
        return self._create_field_raster(field_df, data_column_name, "poly_range_azimuth", slc.shape, invalid_value)

    def crop_code_to_description(self, crop_code):
        return self._crop_code_to_name_dict[crop_code]
