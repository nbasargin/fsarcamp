"""
F-SAR lookup table for geocoding between Azimuth-Range and Northing-Easting geo coordinates.
"""

import numpy as np
import pyproj
import fsarcamp as fc


class Geo2SlantRange:
    """
    F-SAR lookup table (LUT) for geocoding between Azimuth-Range and Northing-Easting geo coordinates.
    The first LUT axis refers to the northing coordinate, the second axis to the easting coordinate.
    """

    def __init__(self, path_lut_az, path_lut_rg):
        """
        Parameters
            path_lut_az - path to the azimuth lookup table (RAT file)
            path_lut_rg - path to the range lookup table (RAT file)
        """
        # read lookup tables
        f_az = fc.RatFile(path_lut_az)
        f_rg = fc.RatFile(path_lut_rg)
        # in the RAT file northing (first axis) is decreasing, and easting (second axis) is increasing
        # use flipud on northing to make both axes consistent: increasing index increases northing / easting
        self.lut_az = np.flipud(f_az.mread())  # reading with memory map: fast and read-only
        self.lut_rg = np.flipud(f_rg.mread())
        assert self.lut_az.shape == self.lut_rg.shape
        # read projection
        header_geo = f_az.Header.Geo  # assume lut az and lut rg headers are equal
        self.projection = self._create_projection(header_geo.zone, header_geo.hemisphere)
        # extent of the area
        self.pixels_north, self.pixels_east = self.lut_az.shape
        self.pixel_spacing_north = header_geo.ps_north
        self.pixel_spacing_east = header_geo.ps_east
        self.min_north = header_geo.min_north
        self.min_east = header_geo.min_east
        # max coordinates refer to the covered area, e.g. the last pixel of lut_az / lut_rg
        self.max_north = self.min_north + self.pixel_spacing_north * (self.pixels_north - 1)
        self.max_east = self.min_east + self.pixel_spacing_east * (self.pixels_east - 1)

    def _create_projection(self, zone, hemisphere):
        proj_params = {}
        proj_params["proj"] = "utm"
        proj_params["zone"] = np.abs(zone)  # negative zone indicates southern hemisphere (defined separaterly)
        proj_params["ellps"] = "WGS84"  # assume WGS84 ellipsoid
        proj_params["south" if hemisphere == 2 else "north"] = True
        return pyproj.Proj(**proj_params)
