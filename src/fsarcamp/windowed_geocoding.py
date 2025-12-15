import numpy as np
import fsarcamp as fc


class WindowedGeocoding:
    def __init__(self, lut: fc.SlantRange2Geo):
        self.lut = lut
        # replace invalid indices before calculating min/max, old LUTs have invalid indices set to -9999
        lut_az = np.copy(lut.lut_az)
        lut_rg = np.copy(lut.lut_rg)
        lut_az[lut_az < 0] = np.nan
        lut_rg[lut_rg < 0] = np.nan
        # find min/max indices of the window within the azrg image
        self.min_az_idx = np.floor(np.nanmin(lut_az)).astype(np.int64)
        self.max_az_idx = np.ceil(np.nanmax(lut_az)).astype(np.int64) + 1
        self.min_rg_idx = np.floor(np.nanmin(lut_rg)).astype(np.int64)
        self.max_rg_idx = np.ceil(np.nanmax(lut_rg)).astype(np.int64) + 1
        # store luts pointing to the window
        self.window_lut_az = lut_az - self.min_az_idx
        self.window_lut_rg = lut_rg - self.min_rg_idx

    def apply_window_to_image_azrg(self, img):
        """
        Crop the image in Azimuth-Range coordinates to the area relevant for geocoding.
        After processing the (smaller) area, geocoding can be performed with `geocode_windowed_image_azrg_to_crs`.
        """
        return img[self.min_az_idx : self.max_az_idx, self.min_rg_idx : self.max_rg_idx]

    def geocode_windowed_image_azrg_to_crs(self, cropped_img, inv_value=np.nan):
        """
        Geocode previously cropped image window to geographical coordinates of the lookup table.
        """
        return fc.nearest_neighbor_lookup(
            cropped_img, self.window_lut_az, self.window_lut_rg, inv_value=inv_value
        )
