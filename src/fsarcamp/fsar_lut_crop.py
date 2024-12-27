"""
Data cropping in SLC and LUT coordinates for efficient processing and geocoding of small regions.
"""

import numpy as np
import fsarcamp as fc


class GeoCrop:
    """
    This class represents a region in northing-easting geometry.
    Lookup table indices are used to specify the extent.
    The main use case is the efficient processing and geocoding of small regions:
    - crop the lookup table to a small area of interest
    - find the corresponding patch in the SLC geometry
    - process only the relevant patch in the SLC geometry (outside of this class)
    - geocode the processed data
    """

    def __init__(self, lut: fc.Geo2SlantRange, min_north_idx, max_north_idx, min_east_idx, max_east_idx):
        """
        Crop LUT to a smaller geographical region.
        Then, find the relevant area in the SLC geometry (min and max indices for az & rg).
        Shift cropped LUT indices to point to the relevant area (az and rg indices go from 0 to max within the area).
        The radar image must be cropped separately.
        """
        self.min_north_idx = min_north_idx
        self.max_north_idx = max_north_idx
        self.min_east_idx = min_east_idx
        self.max_east_idx = max_east_idx
        # crop luts
        lut_az_crop = self._crop_data(lut.lut_az, min_north_idx, max_north_idx, min_east_idx, max_east_idx)
        lut_rg_crop = self._crop_data(lut.lut_rg, min_north_idx, max_north_idx, min_east_idx, max_east_idx)
        # make sure undefined indices (sometimes set to -9999) are nan
        lut_az_crop[lut_az_crop < 0] = np.nan
        lut_rg_crop[lut_rg_crop < 0] = np.nan
        if np.isnan(lut_az_crop).all() or np.isnan(lut_rg_crop).all():
            raise TypeError("The specified LUT region has no valid pixels")
        # find min/max indices
        min_az_idx = np.floor(np.nanmin(lut_az_crop)).astype(np.int64)
        max_az_idx = np.ceil(np.nanmax(lut_az_crop)).astype(np.int64) + 1
        min_rg_idx = np.floor(np.nanmin(lut_rg_crop)).astype(np.int64)
        max_rg_idx = np.ceil(np.nanmax(lut_rg_crop)).astype(np.int64) + 1
        # shift LUT indices, channels must be cropped separately using channel_crop_box
        lut_az_crop -= min_az_idx
        lut_rg_crop -= min_rg_idx
        # store results
        self.lut_az_crop = lut_az_crop
        self.lut_rg_crop = lut_rg_crop
        self.min_az_idx = min_az_idx
        self.max_az_idx = max_az_idx
        self.min_rg_idx = min_rg_idx
        self.max_rg_idx = max_rg_idx

    def _crop_data(self, data, min_x0, max_x0, min_x1, max_x1):
        """
        Crop an image of shape (x0, x1, ...) and return the copy of the region.
        Max index is not included into the image.
        """
        return np.copy(data[min_x0:max_x0, min_x1:max_x1])

    def crop_radar_image(self, radar_image):
        """
        Crop radar image (SLC coordinates) to the region covered by the cropped LUT.
        """
        return self._crop_data(radar_image, self.min_az_idx, self.max_az_idx, self.min_rg_idx, self.max_rg_idx)

    def crop_radar_image_1d_range(self, radar_image):
        """
        Crop a 1D image radar image (SLC coordinates) along the range axis.
        Usef for some older campaigns, e.g., where fe phase image only varies along the range and has no azimuth indices.
        """
        return np.copy(radar_image[self.min_rg_idx : self.max_rg_idx])

    def geocode_cropped_radar_image(self, cropped_radar_image):
        """
        Geocode the cropped radar image using the cropped lookup table.
        """
        return fc.nearest_neighbor_lookup(cropped_radar_image, self.lut_az_crop, self.lut_rg_crop)
