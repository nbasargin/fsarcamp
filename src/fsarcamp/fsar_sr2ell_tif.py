import numpy as np
import pyproj
import rasterio
import rasterio.transform
import shapely
import shapely.ops
import pandas as pd
from typing import Any


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
            self.transform = file_az.transform
            # crs and projection
            self.crs = file_az.crs
            self.projection = pyproj.CRS.from_user_input(self.crs)
            # az lut
            self.lut_az = file_az.read(1)

        with rasterio.open(path_lut_rg) as file_rg:
            # rg lut
            self.lut_rg = file_rg.read(1)

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
        # flipud required, because the last row of data corresponds to the minimum coordinate
        lut_rg = np.rint(np.flipud(self.lut_rg))
        lut_az = np.rint(np.flipud(self.lut_az))
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

    def _geocode_coords_longlat_to_lutindices(self, longitude, latitude):
        """
        Convert longitude-latitude coordinates to lookup table indices.
        """
        lut_lat_idx, lut_lon_idx = rasterio.transform.rowcol(self.transform, longitude, latitude)
        return lut_lat_idx, lut_lon_idx

    def _geocode_coords_lutindices_to_azrg(self, lut_lat_idx, lut_lon_idx):
        """
        Geocode lookup table indices to SLC geometry (azimuth-range).
        First, the appropriate pixels are selected in the lookup table.
        The lookup table then provides the azimuth and range values (float-valued) at the pixel positions.
        The azimuth and range values are invalid and set to NaN if any of the following is true:
        - input lookup table indices are are NaN
        - input lookup table indices are outside of the lookup table
        - retrieved azimuth or range values are negative (meaning the area is not covered by the SLC)
        """
        lut_lat_idx = np.array(lut_lat_idx)
        lut_lon_idx = np.array(lut_lon_idx)
        # if some coords are NaN or outside of the lut, set them to valid values before lookup, mask out later
        max_lat_idx, max_lon_idx = self.lut_az.shape
        invalid_idx = (
            np.isnan(lut_lat_idx)
            | np.isnan(lut_lon_idx)
            | (lut_lat_idx < 0)
            | (lut_lat_idx >= max_lat_idx)
            | (lut_lon_idx < 0)
            | (lut_lon_idx >= max_lon_idx)
        )
        if np.isscalar(invalid_idx):
            if invalid_idx:
                return np.nan, np.nan  # only a single position provided and it is invalid
        else:  # not scalar
            lut_lat_idx[invalid_idx] = 0
            lut_lon_idx[invalid_idx] = 0
        # get azimuth and range positions
        lut_lat_idx = lut_lat_idx.astype(np.int64)
        lut_lon_idx = lut_lon_idx.astype(np.int64)
        az = self.lut_az[lut_lat_idx, lut_lon_idx]
        rg = self.lut_rg[lut_lat_idx, lut_lon_idx]
        # clear invalid azimuth and range
        invalid_results = invalid_idx | (az < 0) | (rg < 0)
        if np.isscalar(invalid_results):
            if invalid_results:
                return np.nan, np.nan  # only a single position computed and it is invalid
        else:  # not scalar
            az[invalid_results] = np.nan
            rg[invalid_results] = np.nan
        return az, rg

    def geocode_coords_longlat_to_azrg(self, longitude, latitude):
        lut_lat_idx, lut_lon_idx = self._geocode_coords_longlat_to_lutindices(longitude, latitude)
        az, rg = self._geocode_coords_lutindices_to_azrg(lut_lat_idx, lut_lon_idx)
        return az, rg

    # geocoding shapely geometry

    def _geocode_geometry_longlat_to_lutindices(self, geometry_longlat: shapely.Geometry):
        fn: Any = self._geocode_coords_longlat_to_lutindices
        return shapely.ops.transform(fn, geometry_longlat)

    def _geocode_geometry_lutindices_to_azrg(self, geometry_lutindices: shapely.Geometry):
        fn: Any = self._geocode_coords_lutindices_to_azrg
        return shapely.ops.transform(fn, geometry_lutindices)

    def geocode_geometry_longlat_to_azrg(self, geometry_longlat: shapely.Geometry):
        geometry_lutincides = self._geocode_geometry_longlat_to_lutindices(geometry_longlat)
        geometry_azrg = self._geocode_geometry_lutindices_to_azrg(geometry_lutincides)
        return geometry_azrg

    # geocoding pandas dataframe with longitude and latitude columns, adding additional columns

    def geocode_dataframe_longlat_to_azrg(self, df: pd.DataFrame):
        """
        Geocode a pandas dataframe with "longitude" and "latitude" columns to slant range geometry.
        Returns a new dataframe with additional "azimuth", "range" columns containing pixel indices within the SLC.
        """
        latitude = df["latitude"].to_numpy()
        longitude = df["longitude"].to_numpy()
        az, rg = self.geocode_coords_longlat_to_azrg(longitude, latitude)
        # extend data frame
        df_geocoded = df.assign(
            azimuth=az,
            range=rg,
        )
        return df_geocoded
