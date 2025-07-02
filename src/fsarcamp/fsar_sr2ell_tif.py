import numpy as np
import pyproj
import rasterio
import shapely
import pandas as pd


class SlantRange2EllTif:
    """
    F-SAR lookup table (LUT) for geocoding from Longitude-Latitude to Azimuth-Range coordinates.
    The first LUT axis refers to the latitude, the second axis to the longitude.
    The values in the LUT refer to the azimuth / range indices in the slant range coordinates.

    This class supports the (newer) TIFF format of the lookup tables.
    """

    def __init__(self, path_lut_az, path_lut_rg):
        """
        Parameters
            path_lut_az - path to the azimuth lookup table (TIFF file)
            path_lut_rg - path to the range lookup table (TIFF file)
        """
        with rasterio.open(path_lut_az) as file_az:
            # bounds
            t_left, t_bottom, t_right, t_top = file_az.bounds
            self.min_lon = t_left
            self.max_lon = t_right
            self.min_lat = t_bottom
            self.max_lat = t_top
            # crs and projection
            self.crs = file_az.crs
            self.projection = pyproj.CRS.from_user_input(self.crs)
            # az lut
            tiff_band = 1
            self.lut_az = np.flipud(file_az.read(tiff_band))
            # flipud required, because the last row of data corresponds to the minimum coordinate
        with rasterio.open(path_lut_rg) as file_rg:
            # rg lut
            tiff_band = 1
            self.lut_rg = np.flipud(file_rg.read(tiff_band))

    # geocoding azrg image to longlat

    def geocode_image_azrg_to_longlat(self, img: np.ndarray, inv_value=np.nan) -> np.ndarray:
        """
        Geocode an image from Azimuth-Range to Longitude-Latitude coordinates
        Nearest neighbor lookup is used (faster but less accurate than interpolation).

        img: numpy array of shape (az, rg, *C) where C are the optional channels (or other dimensions)
            the first two dimensions of the image correspond to the azimuth and range, respectively
        inv_value: constant value to fill pixels with invalid indices, optional, default: numpy.nan

        Returns:
        numpy array of shape (n_lat, n_long, *C), with pixel values looked up from img at indices (lut_az, lut_rg).
        Here, (n_lat, n_long) is the shape of the lut_az and lut_rg lookup tables.
        Pixels where the indices are invalid (e.g., outside of the img) are filled with inv_value.
        """
        # round values in lookup tables (this creates a copy of the LUT data, so inline operations are allowed later)
        lut_rg = np.rint(self.lut_rg)
        lut_az = np.rint(self.lut_az)
        # determine invalid positions
        max_az, max_rg = img.shape[0], img.shape[1]
        invalid_positions = (
            np.isnan(lut_az) | np.isnan(lut_rg) | (lut_az < 0) | (lut_az >= max_az) | (lut_rg < 0) | (lut_rg >= max_rg)
        )
        # set invalid positions to 0
        lut_az[invalid_positions] = 0
        lut_rg[invalid_positions] = 0
        # convert to integer indices
        lut_rg = lut_rg.astype(np.int64)
        lut_az = lut_az.astype(np.int64)
        # nearest neighbor lookup
        geocoded = img[lut_az, lut_rg]
        # apply invalid mask
        geocoded[invalid_positions] = inv_value
        return geocoded

    # geocoding coordinate arrays

    def geocode_coords_longlat_to_lutindices(self, longitude, latitude):
        pass

    def geocode_coords_lutindices_to_azrg(self, lut_x, lut_y):
        pass

    def geocode_coords_longlat_to_azrg(self, longitude, latitude):
        pass

    # geocoding shapely geometry

    def geocode_geometry_longlat_to_lutindices(self, geometry_eastnorth: shapely.Geometry):
        pass

    def geocode_geometry_lutindices_to_azrg(self, geometry_lutindices: shapely.Geometry):
        pass

    def geocode_geometry_longlat_to_azrg(self, geometry_longlat: shapely.Geometry):
        pass

    # geocoding pandas dataframe with longitude and latitude columns, adding additional columns

    def geocode_dataframe_longlat(self, df: pd.DataFrame):
        pass
