"""
Data loader for the CROPEX 2014 field map.
Provides field polygons and crop types.
"""
import numpy as np
import geopandas as gpd
import shapely
import fsarcamp as fc
import fsarcamp.cropex14 as cr14

class CROPEX14FieldMap:
    
    def __init__(self, shapefile_path, cropex14campaign: cr14.CROPEX14Campaign):
        self.shapefile_path = shapefile_path
        self.cropex14campaign = cropex14campaign

    def load_fields(self, band=None, pass_name=None):
        gdf = gpd.read_file(self.shapefile_path)
        gdf = gdf.rename(columns={
            "nu14_anz_n": "num_crop_types",
            "nu14_n_c1": "crop_code_1", "nu14_f_c1": "crop_area_1",
            "nu14_n_c2": "crop_code_2", "nu14_f_c2": "crop_area_2",
            "nu14_n_c3": "crop_code_3", "nu14_f_c3": "crop_area_3",
            "nu14_n_c4": "crop_code_4", "nu14_f_c4": "crop_area_4",
            "nu14_n_c5": "crop_code_5", "nu14_f_c5": "crop_area_5",
        })
        polygon_shapefile = gpd.GeoSeries(shapely.force_2d(gdf.geometry), crs=gdf.crs) # EPSG:31468 (3-degree Gauss-Kruger zone 4)
        polygon_long_lat = polygon_shapefile.to_crs(4326) # EPSG:4326 (longitude - latitude)
        polygon_easting_northing = polygon_shapefile.to_crs(32633) # EPSG:32633 (UTM zone 33N)
        
        if band is not None and pass_name is not None:
            fsar_pass = self.cropex14campaign.get_pass(pass_name, band)
            lut = fsar_pass.load_gtc_lut()
            lut_northing_max, lut_easting_max = lut.lut_az.shape
            min_northing, min_easting = lut.c1 # max_northing, max_easting = lut.c2
            # translate each polygon to the LUT indices
            polygon_easting_northing_lut: gpd.GeoSeries = polygon_easting_northing.copy()
            polygon_easting_northing_lut.crs = None
            polygon_easting_northing_lut = polygon_easting_northing_lut.translate(-min_easting, -min_northing)
            for lut_poly in polygon_easting_northing_lut.to_list():
                easting_lut, northing_lut = lut_poly.exterior.coords.xy
                lut_east_idx = np.rint(easting_lut).astype(np.int64)
                lut_north_idx = np.rint(northing_lut).astype(np.int64)
                invalid_indices = (lut_east_idx < 0) | (lut_east_idx >= lut_easting_max) | (lut_north_idx < 0) | (lut_north_idx >= lut_northing_max)
                lut_east_idx[invalid_indices] = 0
                lut_north_idx[invalid_indices] = 0
                point_az = lut.lut_az[lut_north_idx, lut_east_idx]
                point_rg = lut.lut_rg[lut_north_idx, lut_east_idx]
                point_az[invalid_indices] = np.nan
                point_rg[invalid_indices] = np.nan
                print(point_az)
                print(point_rg)
                return
                # some points might be outside the LUT, need to discard the polygons (use None)
                # construct polygon here
            # construct geoseries here
        # return pandas dataframe with data columns and different geometries (shapefile, latlong, lut idx, slc coords)

def main():
    shapefile_path = fc.get_polinsar_folder() / "Ground_truth/Wallerfing_campaign_May_August_2014/kmz-files/Land_use_Wallerfing_2014_shp+kmz/flugstreifen_wallerfing_feka2014.dbf"
    campaign = cr14.CROPEX14Campaign(fc.get_polinsar_folder() / "01_projects/CROPEX/CROPEX14")
    field_map = CROPEX14FieldMap(shapefile_path, campaign)
    field_map.load_fields("C", "14cropex0203")

if __name__ == "__main__":
    main()
