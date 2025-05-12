"""
Interpolation of the soil moisture ground measurements to the SLC grid for the HTERRA 2022 campaign.
"""

import numpy as np
import scipy
import pandas as pd
import fsarcamp.hterra22 as ht22
import fsarcamp.deprecated.hterra22_moisture_old as ht22old

import fsarcamp.deprecated.hterra22_regions_old as ht22reg


class HTERRA22MoistureInterpolated: # !!!!
    def __init__(self, moisture: ht22old.HTERRA22MoistureOld): # !!!!
        """
        Interpolation of the soil moisture ground measurements to the SLC grid for the HTERRA 2022 campaign.

        Arguments:
            moisture: reference to the soil moisture loader (HTERRA22Moisture)

        Usage example (data paths valid for DLR-HR server as of May 2024):
            import fsarcamp as fc
            import fsarcamp.hterra22 as ht22
            campaign = ht22.HTERRA22Campaign(fc.get_polinsar_folder() / "01_projects/22HTERRA")
            moisture = ht22.HTERRA22Moisture(fc.get_polinsar_folder() / "Ground_truth/HTerra_soil_2022/DataPackage_final", campaign)
            interpolated_moisture = ht22.HTERRA22MoistureInterpolated(moisture)
        """
        self.moisture = moisture

    def _filter_point_subset(self, sm_df, field_stripes=None, point_ids=None):
        if field_stripes:
            sm_df = sm_df[sm_df["field"].isin(field_stripes)]
        if point_ids:
            sm_df = sm_df[sm_df["point_id"].isin(point_ids)]
        return sm_df

    def _form_interpolation_groups(self, band, region, time_period):
        """
        Return a list of pandas dataframes, each dataframe contains several points.
        Points within each dataframe are spatially close and soil moisture can be interpolated between them.
        Points in different dataframes should not be interpolated together but belong to the same region.
        """
        id_range = lambda first_id, last_id: [
            f"P{i}" for i in range(first_id, last_id + 1)
        ]  # first_id to last_id (including)
        df = self.moisture.load_soil_moisture_points(band, region, time_period)
        # split points into groups for specific fields and dates
        if region == ht22.CREA_BS_QU and time_period == ht22.APR_28_PM:
            return [
                self._filter_point_subset(df, point_ids=id_range(23, 77)),  # large convex rectangle
                self._filter_point_subset(df, point_ids=id_range(18, 28)),  # adjacent points
                self._filter_point_subset(df, point_ids=[*id_range(1, 3), *id_range(19, 22)]),  # adjacent points
            ]
        if region == ht22.CREA_DW and time_period in [ht22.APR_28_AM, ht22.APR_28_PM]:
            return [
                self._filter_point_subset(
                    df, field_stripes=["CREA_DURUMWHEAT26", "CREA_DURUMWHEAT27"]
                ),  # east part, 2 stripes
                self._filter_point_subset(df, field_stripes=["CREA_DURUMWHEAT29"]),  # west part
            ]
        if region == ht22.CAIONE_DW and time_period in [ht22.APR_28_AM, ht22.APR_28_PM]:
            return [
                self._filter_point_subset(df, field_stripes=["CAIONE1_DURUMWHEAT29"]),  # field 1, north part, 1 stripe
                self._filter_point_subset(
                    df, field_stripes=["CAIONE1_DURUMWHEAT24", "CAIONE1_DURUMWHEAT27"]
                ),  # field 1, south part, 2 stripes
                self._filter_point_subset(df, field_stripes=["CAIONE2_DURUMWHEAT29"]),  # field 2, north part, 1 stripe
                self._filter_point_subset(
                    df, field_stripes=["CAIONE2_DURUMWHEAT24", "CAIONE2_DURUMWHEAT27"]
                ),  # field 2, south part, 2 stripes
            ]
        if region == ht22.CAIONE_DW and time_period in [ht22.APR_29_AM, ht22.APR_29_PM]:
            return [
                self._filter_point_subset(
                    df, field_stripes=["CAIONE1_DURUMWHEAT24", "CAIONE1_DURUMWHEAT27", "CAIONE1_DURUMWHEAT28"]
                ),  # field 1, 3 stripes
                self._filter_point_subset(
                    df, field_stripes=["CAIONE2_DURUMWHEAT24", "CAIONE2_DURUMWHEAT27", "CAIONE2_DURUMWHEAT28"]
                ),  # field 2, 3 stripes
            ]
        if region == ht22.CAIONE_MA and time_period in [ht22.JUN_15_AM, ht22.JUN_15_PM, ht22.JUN_16_PM]:
            return [
                self._filter_point_subset(
                    df, field_stripes=["CAIONE_MAIS1", "CAIONE_MAIS2", "CAIONE_MAIS3"]
                ),  # west: 3 stripes
                self._filter_point_subset(df, field_stripes=["CAIONE_MAIS4"]),  # east: 1 stripe
            ]
        if region == ht22.CAIONE_MA and time_period in [ht22.JUN_16_AM]:
            mais12 = self._filter_point_subset(df, field_stripes=["CAIONE_MAIS1", "CAIONE_MAIS2"])
            # MAIS3: points P1-P25 are missing, P26 exists but distorts the interpolation, use P27-P52
            mais3 = self._filter_point_subset(df, field_stripes=["CAIONE_MAIS3"], point_ids=id_range(27, 52))
            return [
                pd.concat([mais12, mais3], ignore_index=True),  # west: 3 stripes
                self._filter_point_subset(df, field_stripes=["CAIONE_MAIS4"]),  # east: 1 stripe
            ]
        # if none of the cases above, all points are in the same interpolation group
        return [df]

    def load_soil_moisture_lut_raster(self, band, region_name, time_period_id):
        """
        Get interpolated soil moisture in LUT coordinate grid for the specified region and time period.
        Soil moisture values range from 0 (0%) to 1 (100%).
        """
        interpolation_groups = self._form_interpolation_groups(band, region_name, time_period_id)
        (northing_min, northing_max), (easting_min, easting_max) = ht22reg.get_region_lut_coordinates(band, region_name)
        region_shape = (northing_max - northing_min, easting_max - easting_min)
        interpolated_soil_moisture_lut = np.full(region_shape, fill_value=np.nan, dtype=np.float32)
        for sm_points in interpolation_groups:
            if sm_points.shape[0] == 0:
                continue
            lut_northing, lut_easting = sm_points["lut_northing"], sm_points["lut_easting"]
            soil_moisture = sm_points["soil_moisture"]
            axis_northing, axis_easting = np.arange(northing_min, northing_max), np.arange(easting_min, easting_max)
            grid_northing, grid_easting = np.meshgrid(axis_northing, axis_easting, indexing="ij")
            value_coords = np.array([lut_northing, lut_easting]).transpose((1, 0))
            interpolated_group = scipy.interpolate.griddata(
                value_coords, soil_moisture, (grid_northing, grid_easting), method="linear"
            ).astype(np.float32)
            valid_points = np.isfinite(interpolated_group)
            interpolated_soil_moisture_lut[valid_points] = interpolated_group[valid_points]
        return interpolated_soil_moisture_lut

    def load_soil_moisture_slc_raster(self, band, region_name, time_period_id):
        """
        Get interpolated soil moisture in SLC coordinate grid for the specified region and time period.
        Soil moisture values range from 0 (0%) to 1 (100%).
        """
        interpolation_groups = self._form_interpolation_groups(band, region_name, time_period_id)
        (az_min, az_max), (rg_min, rg_max) = ht22reg.get_region_radar_coordinates(band, region_name)
        region_shape = (az_max - az_min, rg_max - rg_min)
        interpolated_soil_moisture_slc = np.full(region_shape, fill_value=np.nan, dtype=np.float32)
        for sm_points in interpolation_groups:
            if sm_points.shape[0] == 0:
                continue
            point_az, point_rg = sm_points["azimuth"], sm_points["range"]
            soil_moisture = sm_points["soil_moisture"]
            axis_az, axis_rg = np.arange(az_min, az_max), np.arange(rg_min, rg_max)
            grid_az, grid_rg = np.meshgrid(axis_az, axis_rg, indexing="ij")
            value_coords = np.array([point_az, point_rg]).transpose((1, 0))
            interpolated_group = scipy.interpolate.griddata(
                value_coords, soil_moisture, (grid_az, grid_rg), method="linear", rescale=True
            ).astype(np.float32)
            valid_points = np.isfinite(interpolated_group)
            interpolated_soil_moisture_slc[valid_points] = interpolated_group[valid_points]
        return interpolated_soil_moisture_slc
