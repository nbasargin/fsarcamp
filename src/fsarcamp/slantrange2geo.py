import numpy as np
import rasterio
from rasterio import Affine
from rasterio.crs import CRS
import rasterio.transform
import rasterio.plot
import rasterio.windows
import shapely
import shapely.ops
import pyproj
from typing import Any
import fsarcamp as fc


class SlantRange2Geo:
    """
    F-SAR lookup table (LUT) for geocoding between geographical (e.g. Longitude-Latitude)
    and slant range (Azimuth-Range) coordinates.

    The geographical coordinates are defined by the CRS and can vary between campaigns.
    Usually, either Longitude-Latitude or UTM Easting-Northing are used.
    """

    def __init__(self, lut_az, lut_rg, crs: CRS, transform: Affine):
        self.lut_az = lut_az
        self.lut_rg = lut_rg
        self.crs = crs
        self.transform = transform

    def get_bounds(self):
        """Return the bounds of this lookup table in geographical coordinates."""
        width, height = self.lut_az.shape
        west, south, east, north = rasterio.transform.array_bounds(width, height, self.transform)
        return west, south, east, north

    def get_plotting_extent(self):
        """Return the bounds in the matplotlib order (for matplotlib.pyplot.imshow)."""
        left, right, bottom, top = rasterio.plot.plotting_extent(self.lut_az, self.transform)
        return left, right, bottom, top

    def get_proj(self):
        """Rasterio CRS to Pyproj projection."""
        return pyproj.CRS.from_user_input(self.crs)

    # lut transformations

    def crop_to_geometry_crs(self, geometry_crs):
        """
        Crop this lookup table to the bounding box of the provided geometry.
        The geometry CRS must match the CRS of this lookup table.
        """
        height, width = self.lut_az.shape
        minx, miny, maxx, maxy = shapely.total_bounds(geometry_crs)
        bounds_window = rasterio.windows.from_bounds(minx, miny, maxx, maxy, self.transform)
        # Round and clip the window to fit within the raster
        bounds_window = bounds_window.round()
        col_off = max(0, int(bounds_window.col_off))
        row_off = max(0, int(bounds_window.row_off))
        col_end = min(width, int(bounds_window.col_off + bounds_window.width))
        row_end = min(height, int(bounds_window.row_off + bounds_window.height))
        if col_off >= col_end or row_off >= row_end:
            raise ValueError("Geometry is completely outside the raster bounds.")
        clipped_window = rasterio.windows.Window.from_slices((row_off, row_end), (col_off, col_end))
        # Crop the lut using the clipped window
        cropped_lut_az = self.lut_az[row_off:row_end, col_off:col_end]
        cropped_lut_rg = self.lut_rg[row_off:row_end, col_off:col_end]
        cropped_transform = rasterio.windows.transform(clipped_window, self.transform)
        return SlantRange2Geo(lut_az=cropped_lut_az, lut_rg=cropped_lut_rg, crs=self.crs, transform=cropped_transform)

    # geocoding azrg image to geographical coordinates

    def geocode_image_azrg_to_crs(self, img: np.ndarray, inv_value=np.nan) -> np.ndarray:
        """
        Geocode an image from Azimuth-Range to geographical coordinates of this lookup table.
        Nearest neighbor lookup is used (faster but less accurate than interpolation).

        img: numpy array of shape (az, rg, *C) where C are the optional channels (or other dimensions)
            the first two dimensions of the image correspond to the azimuth and range, respectively
        inv_value: constant value to fill pixels with invalid indices, optional, default: numpy.nan

        Returns:
            numpy array of shape (rows, cols, *C), where (rows, cols) is the shape of the lut_az and lut_rg lookup tables.
            The pixel values are looked up from img at indices (lut_az, lut_rg).
            Pixels where the indices are invalid (e.g., outside of the img) are filled with inv_value.
            The CRS and spatial coverage match the CRS and spatial coverage of this lookup table.
        """
        return fc.nearest_neighbor_lookup(img, self.lut_az, self.lut_rg, inv_value=inv_value)

    # geocoding coordinate arrays

    def geocode_coords_longlat_to_crs(self, longitude, latitude):
        """
        Convert Longitude-Latitude coordinates to the CRS of this lookup table.
        If CRS of this lookup table is already EPSG:4326, this function returns the original coordinates.
        """
        if self.crs.to_epsg() == 4326:
            return longitude, latitude  # this lookup table is 4326, coordinates already matching
        proj_longlat = pyproj.Proj(proj="longlat", ellps="WGS84", datum="WGS84")
        longlat_to_crs = pyproj.Transformer.from_proj(proj_longlat, self.get_proj())
        xs, ys = longlat_to_crs.transform(longitude, latitude)
        return xs, ys

    def geocode_coords_crs_to_rowcol(self, xs, ys):
        """
        Convert geographical coordinates (matching the CRS) to lookup table indices (rows and columns).
        """
        rows, cols = rasterio.transform.rowcol(self.transform, xs, ys)
        return rows, cols

    def geocode_coords_rowcol_to_azrg(self, rows, cols):
        """
        Geocode lookup table indices (rows and columns) to SLC geometry (azimuth-range).
        First, the appropriate pixels are selected in the lookup table.
        The lookup table then provides the azimuth and range values (float-valued) at the pixel positions.
        The azimuth and range values are invalid and set to NaN if any of the following is true:
        - input lookup table indices are are NaN
        - input lookup table indices are outside of the lookup table
        - retrieved azimuth or range values are negative (meaning the area is not covered by the SLC)
        """
        rows = np.array(rows)
        cols = np.array(cols)
        # if some coords are NaN or outside of the lut, set them to valid values before lookup, mask out later
        max_row, max_col = self.lut_az.shape
        invalid_idx = np.isnan(rows) | np.isnan(cols) | (rows < 0) | (rows >= max_row) | (cols < 0) | (cols >= max_col)
        if np.isscalar(invalid_idx):
            if invalid_idx:
                return np.nan, np.nan  # only a single position provided and it is invalid
        else:  # not scalar
            rows[invalid_idx] = 0
            cols[invalid_idx] = 0
        # get azimuth and range positions
        rows = rows.astype(np.int64)
        cols = cols.astype(np.int64)
        az = self.lut_az[rows, cols]
        rg = self.lut_rg[rows, cols]
        # clear invalid azimuth and range
        invalid_results = invalid_idx | (az < 0) | (rg < 0)
        if np.isscalar(invalid_results):
            if invalid_results:
                return np.nan, np.nan  # only a single position computed and it is invalid
        else:  # not scalar
            az[invalid_results] = np.nan
            rg[invalid_results] = np.nan
        return az, rg

    def geocode_coords_crs_to_azrg(self, xs, ys):
        rows, cols = self.geocode_coords_crs_to_rowcol(xs, ys)
        az, rg = self.geocode_coords_rowcol_to_azrg(rows, cols)
        return az, rg

    def geocode_coords_longlat_to_azrg(self, longitude, latitude):
        xs, ys = self.geocode_coords_longlat_to_crs(longitude, latitude)
        rows, cols = self.geocode_coords_crs_to_rowcol(xs, ys)
        az, rg = self.geocode_coords_rowcol_to_azrg(rows, cols)
        return az, rg

    # geocoding shapely geometry

    def geocode_geometry_longlat_to_crs(self, geometry_longlat: shapely.Geometry):
        fn: Any = self.geocode_coords_longlat_to_crs
        return shapely.ops.transform(fn, geometry_longlat)

    def geocode_geometry_crs_to_rowcol(self, geometry_crs: shapely.Geometry):
        fn: Any = self.geocode_coords_crs_to_rowcol
        return shapely.ops.transform(fn, geometry_crs)

    def geocode_geometry_rowcol_to_azrg(self, geometry_rowcol: shapely.Geometry):
        fn: Any = self.geocode_coords_rowcol_to_azrg
        return shapely.ops.transform(fn, geometry_rowcol)

    def geocode_geometry_crs_to_azrg(self, geometry_crs: shapely.Geometry):
        geometry_rowcol = self.geocode_geometry_crs_to_rowcol(geometry_crs)
        geometry_azrg = self.geocode_geometry_rowcol_to_azrg(geometry_rowcol)
        return geometry_azrg

    def geocode_geometry_longlat_to_azrg(self, geometry_longlat: shapely.Geometry):
        geometry_crs = self.geocode_geometry_longlat_to_crs(geometry_longlat)
        geometry_rowcol = self.geocode_geometry_crs_to_rowcol(geometry_crs)
        geometry_azrg = self.geocode_geometry_rowcol_to_azrg(geometry_rowcol)
        return geometry_azrg

    # geocoding pandas dataframes

    def geocode_dataframe_longlat(self, df):
        """
        Geocode a pandas dataframe with "longitude" and "latitude" columns to crs, rowcol, and slant range geometry.
        Returns a new dataframe with additional columns attached.
        """
        latitude = df["latitude"].to_numpy()
        longitude = df["longitude"].to_numpy()
        crs_x, crs_y = self.geocode_coords_longlat_to_crs(longitude, latitude)
        lut_row, lut_col = self.geocode_coords_crs_to_rowcol(crs_x, crs_y)
        az, rg = self.geocode_coords_rowcol_to_azrg(lut_row, lut_col)
        # extend data frame
        df_geocoded = df.assign(
            crs_x=crs_x,
            crs_y=crs_y,
            lut_row=lut_row,
            lut_col=lut_col,
            azimuth=az,
            range=rg,
        )
        return df_geocoded
