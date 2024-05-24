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
            return shapely.Polygon(np.stack((point_az, point_rg), axis=1))
        else:
            raise RuntimeError(f"Unknown geometry type: {lut_shape.geom_type}")

    def load_fields(self, band=None, pass_name=None):
        gdf = gpd.read_file(self.shapefile_path)
        polygons_shapefile = gpd.GeoSeries(shapely.force_2d(gdf.geometry), crs=gdf.crs) # EPSG:31468 (3-degree Gauss-Kruger zone 4)
        polygons_long_lat = polygons_shapefile.to_crs(4326) # EPSG:4326 (longitude - latitude)
        polygons_easting_northing = polygons_shapefile.to_crs(32633) # EPSG:32633 (UTM zone 33N)        
        processed_df = gpd.GeoDataFrame({
            "num_crop_types": gdf["nu14_anz_n"], # number of different crop types on that field
            # crop code (defines what was planted) and the corresponding area, up to 5 different crops
            "crop_code_1": gdf["nu14_n_c1"], "crop_area_1": gdf["nu14_f_c1"],
            "crop_code_2": gdf["nu14_n_c2"], "crop_area_2": gdf["nu14_f_c2"],
            "crop_code_3": gdf["nu14_n_c3"], "crop_area_3": gdf["nu14_f_c3"],
            "crop_code_4": gdf["nu14_n_c4"], "crop_area_4": gdf["nu14_f_c4"],
            "crop_code_5": gdf["nu14_n_c5"], "crop_area_5": gdf["nu14_f_c5"],
            # geometry: field polygon in different projections
            "poly_shapefile": polygons_shapefile, # shapefile geometry (3-degree Gauss-Kruger zone 4)
            "poly_longitude_latitude": polygons_long_lat, # longitude latitude
            "poly_easting_northing": polygons_easting_northing, # LUT easting northing (UTM zone 33N)
        })
        if band is not None and pass_name is not None:
            # create field polygons in LUT and SLC pixel coordinates
            fsar_pass = self.cropex14campaign.get_pass(pass_name, band)
            lut = fsar_pass.load_gtc_lut()
            min_northing, min_easting = lut.c1 # max_northing, max_easting = lut.c2
            # translate each polygon to the LUT indices
            polygons_easting_northing_lut: gpd.GeoSeries = polygons_easting_northing.copy()
            polygons_easting_northing_lut.crs = None
            polygons_easting_northing_lut = polygons_easting_northing_lut.translate(-min_easting, -min_northing)
            print(polygons_easting_northing_lut)
            slc_poly_list = [self._geocode_shape(lut_poly, lut.lut_az, lut.lut_rg) for lut_poly in polygons_easting_northing_lut.to_list()]
            processed_df.assign(
                poly_easting_northing_lut = polygons_easting_northing_lut, # LUT pixel indices, easting northing
                poly_azimuth_range = gpd.GeoSeries(slc_poly_list), # SLC pixel indices, azimuth range
            )
        return processed_df

def main():
    shapefile_path = fc.get_polinsar_folder() / "Ground_truth/Wallerfing_campaign_May_August_2014/kmz-files/Land_use_Wallerfing_2014_shp+kmz/flugstreifen_wallerfing_feka2014.dbf"
    campaign = cr14.CROPEX14Campaign(fc.get_polinsar_folder() / "01_projects/CROPEX/CROPEX14")
    field_map = CROPEX14FieldMap(shapefile_path, campaign)
    fmap = field_map.load_fields("C", "14cropex0203")
    print(fmap)

if __name__ == "__main__":
    main()
