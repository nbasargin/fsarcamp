import numpy as np
import rasterio
from rasterio import Affine
from rasterio.crs import CRS
import rasterio.transform
import shapely
import shapely.ops
import pyproj
from typing import Any

import fsarcamp as fc
import fsarcamp.cropex25 as cr25


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

    def get_proj(self):
        """Rasterio CRS to Pyproj projection."""
        return pyproj.CRS.from_user_input(self.crs)

    # geocoding azrg image to geographical coordinates

    def geocode_image_azrg_to_geo(self, img: np.ndarray, inv_value=np.nan) -> np.ndarray:
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

    def _geocode_coords_geo_to_rowcol(self, xs, ys):
        """
        Convert geographical coordinates (e.g. xs=longitude, ys=latitude) to lookup table indices (rows and columns).
        """
        rows, cols = rasterio.transform.rowcol(self.transform, xs, ys)
        return rows, cols

    def _geocode_coords_rowcol_to_azrg(self, rows, cols):
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

    def geocode_coords_geo_to_azrg(self, xs, ys):
        rows, cols = self._geocode_coords_geo_to_rowcol(xs, ys)
        az, rg = self._geocode_coords_rowcol_to_azrg(rows, cols)
        return az, rg

    # geocoding shapely geometry

    def _geocode_geometry_geo_to_rowcol(self, geometry_geo: shapely.Geometry):
        fn: Any = self._geocode_coords_geo_to_rowcol
        return shapely.ops.transform(fn, geometry_geo)

    def _geocode_geometry_rowcol_to_azrg(self, geometry_rowcol: shapely.Geometry):
        fn: Any = self._geocode_coords_rowcol_to_azrg
        return shapely.ops.transform(fn, geometry_rowcol)

    def geocode_geometry_geo_to_azrg(self, geometry_geo: shapely.Geometry):
        geometry_rowcol = self._geocode_geometry_geo_to_rowcol(geometry_geo)
        geometry_azrg = self._geocode_geometry_rowcol_to_azrg(geometry_rowcol)
        return geometry_azrg


def main():
    # can rasterio crs be used to geocode latlong to utm33n? like pyproj?
    # is the crs, bounds, and transform sufficient to construct the object

    # https://gis.stackexchange.com/questions/490186/getting-correct-bounds-of-clipped-geotiff-using-rasterio

    pass_name = "25cropex0505"
    band = "X"
    campaign = cr25.CROPEX25Campaign(fc.get_polinsar_folder() / "01_projects/25CROPEX")
    ps: cr25.CROPEX25Pass = campaign.get_pass(pass_name, band)  # type: ignore

    fname_lut_az = ps._gtc_folder() / "GTC-LUT" / f"sr2ell_az_{ps.pass_name}_{ps.band}_t01{ps.band}.tif"
    fname_lut_rg = ps._gtc_folder() / "GTC-LUT" / f"sr2ell_rg_{ps.pass_name}_{ps.band}_t01{ps.band}.tif"

    with rasterio.open(fname_lut_az) as file_az:
        # bounds
        bounds = file_az.bounds
        transform = file_az.transform
        # crs and projection
        crs = file_az.crs
        # self.projection = pyproj.CRS.from_user_input(self.crs)

        # az lut
        lut_az = file_az.read(1)

    with rasterio.open(fname_lut_rg) as file_rg:
        # rg lut
        lut_rg = file_rg.read(1)

    print("lut_az", type(lut_az), lut_az.shape, lut_az.dtype)
    print("lut_rg", type(lut_rg), lut_rg.shape, lut_rg.dtype)
    print("bounds", type(bounds), bounds)
    print("transform", type(transform), transform)
    print("crs", type(crs), crs)

    # lut = SlantRange2Geo(lut_az=lut_az, lut_rg=lut_rg, crs=crs, bounds=bounds, transform=transform)

    # can the affine transform be full reconstructed from lut shape and bounds?
    # rasterio uses transfrom and not bounds

    print()
    width, height = lut_az.shape
    transform2 = rasterio.transform.from_bounds(
        west=bounds.left, south=bounds.bottom, east=bounds.right, north=bounds.top, width=width, height=height
    )

    print(transform2)
    print(transform)

    bounds2 = rasterio.transform.array_bounds(width, height, transform)
    print(bounds)
    print(bounds2)


if __name__ == "__main__":
    main()
