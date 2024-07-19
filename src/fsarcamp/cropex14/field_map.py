"""
Data loader for the CROPEX 2014 field map.
Provides field polygons and crop types.
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from rasterio.features import rasterize
import fsarcamp.cropex14 as cr14

class CROPEX14FieldMap:
    
    def __init__(self, shapefile_path, cropex14campaign: cr14.CROPEX14Campaign):
        self.shapefile_path = shapefile_path
        self.cropex14campaign = cropex14campaign
        # crop codes taken from "a6_codierung_fnn.pdf", more codes are available there
        self._crop_code_to_name_dict = {
            115: "Winter wheat", # Winterweizen
            116: "Summer wheat", # Sommerweizen
            131: "Winter barley", # Wintergerste
            132: "Summer barley", # Sommergerste
            140: "Oat", # Hafer
            156: "Winter triticale", # Wintertriticale
            157: "Summer triticale", # Sommertriticale
            171: "Grain maize", # Körnermais
            172: "Corn-Cob-Mix", # Corn-Cob-Mix
            210: "Peas", # Erbsen
            220: "Beans", # Ackerbohnen
            311: "Winter rapeseed", # Winterraps
            320: "Sunflowers", # Sonnenblumen
            411: "Silage maize", # Silomais
            422: "Clover / alfalfa mix", # Kleegras, Klee-/Luzernegras-Gemisch 
            423: "Alfalfa", # Luzerne
            424: "Agricultural grass", # Ackergras
            426: "Other cereals as whole plant silage", # Sonstiges Getreide als Ganzpflanzensilage
            441: "Green areas", # Grünlandeinsaat (Wiesen, Mähweiden, Weiden)
            451: "Grasslands (incl Orchards)", # Wiesen (einschl. Streuobstwiesen) 
            452: "Mowed pastures", # Mähweiden
            453: "Pastures", # Weiden
            460: "Summer pastures for sheep walking", # Sommerweiden für Wanderschafe
            560: "Set aside arable land", # Stillgelegte Ackerflächen i. R. von AUM
            567: "Disused permanent grassland", # Stillgelegte Dauergrünlandflächen i. R. von AUM
            591: "Farmland out of production", # Ackerland aus der Erzeugung genommen
            592: "Set aside Grassland", # Dauergrünland aus der Erzeugung genommen
            611: "Potatoes", # Frühkartoffeln
            612: "Other potatoes", # Sonstige Speisekartoffeln
            613: "Industrial potatoes", # Industriekartoffeln
            615: "Seed potatoes", # Pflanzkartoffeln (alle Verwertungsformen)
            619: "Other potatoes", # Sonstige Kartoffeln (z. B. Futterkartoffeln) 
            640: "Starch potatoes", # Stärkekartoffeln (Vertragsanbau)
            620: "Sugar beet", # Zuckerrüben (ohne Samenvermehrung)
            630: "Jerusalem artichokes", # Topinambur
            710: "Vegetables", # Feldgemüse
            720: "Outdoor vegetables", # Gemüse im Freiland (gärtnerischer Anbau)
            811: "Pome and stone fruit", # Kern- und Steinobst
            812: "Orchard (without meadow / arable land)", # Streuobst (ohne Wiesen-/Ackernutzung)
            824: "Hazelnuts", # Haselnüsse
            846: "Christmas tree plantations outside the forest", # Christbaumkulturen außerhalb des Waldes
            848: "Short rotation forest trees (rotation period max. 20 years)", # Schnellwüchsige Forstgehölze (Umtriebszeit max. 20 Jahre)
            851: "Vines cultivated", # Bestockte Rebfläche
            896: "Miscanthus", # Chinaschilf (Miscanthus) 
            897: "Other perennial energy crops", # Sonstige mehrjährige Energiepflanzen (z. B. Riesenweizengras, Rutenhirse, Durchwachsene Silphie, Igniscum)
            890: "Other permanent crops", # Sonstige Dauerkulturen        
            920: "House garden", # Nicht landw. genutzte Haus- und Nutzgärten
            980: "Sudan grass", # Sudangras, Hirse
            990: "Other non used area", # Sonstige nicht landw. genutzte Fläche
            996: "Storage field", # Unbefestigte Mieten, Stroh-, Futter- und Dunglagerplätze (maximal ein Jahr) auf Ackerland
        }

    def _geocode_shape(self, lut_shape, lut_az, lut_rg):
        """
        Geocode a polygon or a multi-polygon from LUT to SLC pixel indices.
        Coordinates for each polygon point are converted individually using the LUT.
        """
        if lut_shape.geom_type == "MultiPolygon":
            geocoded_polys = [self._geocode_shape(poly, lut_az, lut_rg) for poly in lut_shape.geoms]
            valid_polys = [poly for poly in geocoded_polys if poly is not None]
            if len(valid_polys) == 0:
                return None # no valid polygons
            return shapely.MultiPolygon(valid_polys)
        elif lut_shape.geom_type == "Polygon":
            lut_northing_max, lut_easting_max = lut_az.shape
            easting_lut, northing_lut = lut_shape.exterior.coords.xy
            lut_east_idx = np.rint(easting_lut).astype(np.int64)
            lut_north_idx = np.rint(northing_lut).astype(np.int64)
            invalid_indices = (lut_east_idx < 0) | (lut_east_idx >= lut_easting_max) | (lut_north_idx < 0) | (lut_north_idx >= lut_northing_max)
            lut_east_idx[invalid_indices] = 0
            lut_north_idx[invalid_indices] = 0
            point_az = lut_az[lut_north_idx, lut_east_idx]
            point_rg = lut_rg[lut_north_idx, lut_east_idx]
            point_az[invalid_indices] = np.nan
            point_rg[invalid_indices] = np.nan
            if np.any(np.isnan(point_az)) or np.any(np.isnan(point_rg)):
                return None # some points invalid
            return shapely.Polygon(np.stack((point_rg, point_az), axis=1))
        else:
            raise RuntimeError(f"Unknown geometry type: {lut_shape.geom_type}")

    def load_fields(self, pass_name=None, band=None):
        gdf = gpd.read_file(self.shapefile_path)
        polygons_shapefile = gpd.GeoSeries(shapely.force_2d(gdf.geometry), crs=gdf.crs) # EPSG:31468 (3-degree Gauss-Kruger zone 4)
        polygons_long_lat = polygons_shapefile.to_crs(4326) # EPSG:4326 (longitude - latitude)
        polygons_easting_northing = polygons_shapefile.to_crs(32633) # EPSG:32633 (UTM zone 33N)        
        processed_df = gpd.GeoDataFrame({
            "num_crop_types": gdf["nu14_anz_n"], # number of different crop types on that field
            # crop code (defines what was planted) and the corresponding area, up to 5 different crops
            "crop_code_1": pd.to_numeric(gdf["nu14_n_c1"]), "crop_area_1": gdf["nu14_f_c1"],
            "crop_code_2": pd.to_numeric(gdf["nu14_n_c2"]), "crop_area_2": gdf["nu14_f_c2"],
            "crop_code_3": pd.to_numeric(gdf["nu14_n_c3"]), "crop_area_3": gdf["nu14_f_c3"],
            "crop_code_4": pd.to_numeric(gdf["nu14_n_c4"]), "crop_area_4": gdf["nu14_f_c4"],
            "crop_code_5": pd.to_numeric(gdf["nu14_n_c5"]), "crop_area_5": gdf["nu14_f_c5"],
            # geometry: field polygon in different projections
            "poly_shapefile": polygons_shapefile, # shapefile geometry (3-degree Gauss-Kruger zone 4)
            "poly_longitude_latitude": polygons_long_lat, # longitude latitude
            "poly_easting_northing": polygons_easting_northing, # LUT easting northing (UTM zone 33N)
        })
        if band is not None and pass_name is not None:
            # create field polygons in LUT and SLC pixel coordinates
            fsar_pass = self.cropex14campaign.get_pass(pass_name, band)
            lut = fsar_pass.load_gtc_sr2geo_lut()
            # translate each polygon to the LUT indices
            polygons_easting_northing_lut: gpd.GeoSeries = polygons_easting_northing.copy()
            polygons_easting_northing_lut.crs = None
            polygons_easting_northing_lut = polygons_easting_northing_lut.translate(-lut.min_east, -lut.min_north)
            slc_poly_list = [self._geocode_shape(lut_poly, lut.lut_az, lut.lut_rg) for lut_poly in polygons_easting_northing_lut.to_list()]
            processed_df = processed_df.assign(
                poly_easting_northing_lut = polygons_easting_northing_lut, # LUT pixel indices, easting northing
                poly_range_azimuth = gpd.GeoSeries(slc_poly_list), # SLC pixel indices, azimuth range
            )
        return processed_df

    def load_field_by_id(self, field_id, pass_name=None, band=None):
        """
        Load a field by ID. Returns a dataframe with the same columns as `load_fields`.
        Most fields are defined by a single polygon but some have multiple.
        """
        fields = self.load_fields(pass_name, band)
        # look up field polygons that contain specific points
        points_on_field = {
            cr14.CORN_C1: [(12.874096, 48.694220), (12.875333, 48.694533)],
            cr14.CORN_C1_CENTER: [(12.874096, 48.694220)],
            cr14.CORN_C2: [(12.873469, 48.696072)],
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
        filtered_fields = [fields[fields["poly_longitude_latitude"].contains(shapely.Point(point))] for point in points_on_field]
        return pd.concat(filtered_fields)

    def _create_field_raster(self, field_df: gpd.GeoDataFrame, data_column_name, geometry_column_name, out_shape, invalid_value):
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
        value_to_fields = dict() # dict: data -> list of field polygons/shapes
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
            rasterized_values = rasterize(field_polys, out_shape=out_shape, default_value=field_value, out=rasterized_values)
        return rasterized_values

    def create_field_lut_raster(self, field_df: gpd.GeoDataFrame, data_column_name, pass_name, band, invalid_value=np.nan):
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
        return self._create_field_raster(field_df, data_column_name, "poly_easting_northing_lut", lut.lut_az.shape, invalid_value)
    
    def create_field_slc_raster(self, field_df: gpd.GeoDataFrame, data_column_name, pass_name, band, invalid_value=np.nan):
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
