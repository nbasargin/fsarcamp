"""
Data loader for soil moisture ground measurements for the HTERRA 2022 campaign.
"""
import pathlib
from datetime import datetime
import numpy as np
import scipy
import pandas as pd
import pyproj
import fsarcamp as fc
import fsarcamp.hterra22 as ht22

class HTERRA22Moisture:
    def __init__(self, data_folder):
        """
        The data_folder contains the CSV files with soil moisture measurements for the HTERRA22 campaign.
        Default location on DLR servers as of April 2024:
            fsarcamp.get_polinsar_folder() / "Ground_truth/HTerra_soil_2022/DataPackage_final"
        """
        self.data_folder = pathlib.Path(data_folder)
        
    def _read_csvs_from_folder(self, folder_path, file_names):
        """
        Read original CSV files, normalize column names, add UTM zone 33 coordinates (F-SAR LUT).
        """
        # transformation: latlong to LUT coords
        proj_hterra22 = pyproj.Proj("epsg:32633") # UTM zone 33
        proj_latlong = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
        latlong_to_lut = pyproj.Transformer.from_proj(proj_latlong, proj_hterra22)
        dfs = []
        for file in file_names:
            df_path = folder_path / file
            df = pd.read_csv(df_path)
            df = df.dropna()
            df = df.rename(columns={
                "DATE_TIME": "date_time",
                "POINT_ID": "point_id",
                "FIELD": "field",
                "LATITUDE": "latitude",
                "LONGITUDE": "longitude",
                # soil moisture is either available as SM_CAL_ALL or SM_CAL
                "SM_CAL_ALL": "soil_moisture",
                "SM_CAL": "soil_moisture",
            })
            df["date_time"] = pd.to_datetime(df["date_time"])
            # add easting and northing
            lat = df["latitude"].to_numpy()
            long = df["longitude"].to_numpy()
            easting, northing = latlong_to_lut.transform(long, lat)
            df["easting"] = easting
            df["northing"] = northing
            dfs.append(df)
        df = pd.concat(dfs, ignore_index=True)
        return df

    def read_hterra22_soil_moisture(self):
        april_caione = self._read_csvs_from_folder(
            self.data_folder / "April22/soil_moisture_sensors/CAIONE",
            ["CA1_DW_24.csv", "CA1_DW_27.csv", "CA1_DW_28.csv", "CA1_DW_29.csv", "CA2_DW_24.csv", "CA2_DW_27.csv", "CA2_DW_28.csv", "CA2_DW_29.csv"],
        )
        april_crea = self._read_csvs_from_folder(
            self.data_folder / "April22/soil_moisture_sensors/CREA",
            ["CREA_BS_APRIL.csv", "CREA_DW26.csv", "CREA_DW27.csv", "CREA_DW28.csv", "CREA_DW29.csv"],
        )
        june_caione = self._read_csvs_from_folder(
            self.data_folder / "June22/soil_moisture_sensors/CAIONE",
            ["CA_AA_1.csv", "CA_AA_2.csv", "CA_AA_3.csv", "CA_MA_1.csv", "CA_MA_2.csv", "CA_MA_3.csv", "CA_MA_4.csv"],
        )
        june_crea = self._read_csvs_from_folder(
            self.data_folder / "June22/soil_moisture_sensors/CREA",
            ["CREA_MA_1.csv", "CREA_MA_2.csv", "CREA_QUINOA.csv", "CREA_SF.csv"]
        )
        return pd.concat([april_caione, april_crea, june_caione, june_crea], ignore_index=True)
    
    # Additional grouping by region and time period below

    def _filter_soil_moisture_subset(self, sm_df, field_stripe, iso_date_from, iso_date_to, point_ids=None):
        """
        Filter dataframe with all points by field_stripe and date range.
        Optionally, select specific points by ID after filtering.
        Parameters:
            sm_df: dataframe with all soil moisture measurements
            field_stripe: field or stripe to take points from, should match the "field" column of the dataframe
            iso_date_from: start date and time, in ISO format like "2022-04-28T08:45:00"
            iso_date_to: end date and time, in ISO format like "2022-04-28T11:09:00"
            point_ids: optional list of specific points (e.g. ["P1", "P10"]) or None to include all points
        """
        date_from = datetime.fromisoformat(iso_date_from)
        date_to = datetime.fromisoformat(iso_date_to)
        sm_df_filtered = sm_df[(sm_df["field"] == field_stripe) & (sm_df["date_time"] >= date_from) & (sm_df["date_time"] <= date_to)]
        if point_ids is not None:
            sm_df_filtered = sm_df_filtered[sm_df_filtered["point_id"].isin(point_ids)]
        return sm_df_filtered

    def _pt_range(self, first_id, last_id):
        """ Range of point IDs from first_id to last_id (including the last value) """
        return [f"P{i}" for i in range(first_id, last_id + 1)]

    def _crea_bs_qu_interpolation_groups(self, sm_df, time_period_id):
        """ CREA_BS_QU region: bare soil field in April, quinoa in June """
        # June: bare soil
        if time_period_id == ht22.APR_28_AM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_BARESOIL", "2022-04-28T08:45:00", "2022-04-28T11:09:00")]
        if time_period_id == ht22.APR_28_PM:
            # Points P4-P17 are missing -> interpolation of all points produces some artifacts.
            # Therefore, interpolate in smaller groups
            start, end = "2022-04-28T14:13:00", "2022-04-28T16:39:00"
            return [
                self._filter_soil_moisture_subset(sm_df, "CREA_BARESOIL", start, end, point_ids=[*self._pt_range(23, 77)]), # large convex rectangle
                self._filter_soil_moisture_subset(sm_df, "CREA_BARESOIL", start, end, point_ids=[*self._pt_range(18, 28)]), # adjacent points
                self._filter_soil_moisture_subset(sm_df, "CREA_BARESOIL", start, end, point_ids=[*self._pt_range(1, 3), *self._pt_range(19, 22)]), # small area below
            ]
        if time_period_id == ht22.APR_29_AM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_BARESOIL", "2022-04-29 08:43:00", "2022-04-29 10:28:00")]
        if time_period_id == ht22.APR_29_PM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_BARESOIL", "2022-04-29 13:30:00", "2022-04-29 15:01:00")]    
        # April: quinoa
        if time_period_id == ht22.JUN_15_AM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_QUINOA", "2022-06-15 08:39:00", "2022-06-15 10:33:00")]
        if time_period_id == ht22.JUN_15_PM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_QUINOA", "2022-06-15 14:02:00", "2022-06-15 15:16:00")]
        if time_period_id == ht22.JUN_16_AM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_QUINOA", "2022-06-16 08:39:00", "2022-06-16 09:49:00")]
        if time_period_id == ht22.JUN_16_PM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_QUINOA", "2022-06-16 13:48:00", "2022-06-16 14:42:00")]
        return []

    def _crea_dw_interpolation_groups(self, sm_df, time_period_id):
        """ CREA durum wheat field in April """
        if time_period_id == ht22.APR_28_AM:
            # CREA_DW, east part, 2 stripes
            crea_dw_east_28am_1 = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT26", "2022-04-28T10:42:00", "2022-04-28T11:34:00")
            crea_dw_east_28am_2 = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT27", "2022-04-28T09:42:00", "2022-04-28T10:40:00")
            crea_dw_east_28am = pd.concat([crea_dw_east_28am_1, crea_dw_east_28am_2], ignore_index=True)
            # CREA_DW, west part
            crea_dw_west_28am = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT29", "2022-04-28T08:56:00", "2022-04-28T09:41:00")
            return [crea_dw_east_28am, crea_dw_west_28am]
        if time_period_id == ht22.APR_28_PM:
            # CREA_DW, east part, 2 stripes
            crea_dw_east_28pm_1 = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT26", "2022-04-28T16:11:00", "2022-04-28T16:50:00")
            crea_dw_east_28pm_2 = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT27", "2022-04-28T15:27:00", "2022-04-28T16:07:00")
            crea_dw_east_28pm = pd.concat([crea_dw_east_28pm_1, crea_dw_east_28pm_2], ignore_index=True)
            # CREA_DW, west part
            crea_dw_west_28pm = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT29", "2022-04-28T14:35:00", "2022-04-28T15:26:00")
            return [crea_dw_east_28pm, crea_dw_west_28pm]
        if time_period_id == ht22.APR_29_AM:
            crea_dw_29am_1 = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT26", "2022-04-29 10:32:00", "2022-04-29 11:21:00")
            crea_dw_29am_2 = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT27", "2022-04-29 09:40:00", "2022-04-29 10:31:00")
            crea_dw_29am_3 = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT28", "2022-04-29 08:50:00", "2022-04-29 09:38:00")
            return [pd.concat([crea_dw_29am_1, crea_dw_29am_2, crea_dw_29am_3], ignore_index=True)]
        if time_period_id == ht22.APR_29_PM:
            crea_dw_29pm_1 = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT26", "2022-04-29 15:07:00", "2022-04-29 15:55:00")
            crea_dw_29pm_2 = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT27", "2022-04-29 14:14:00", "2022-04-29 15:06:00")
            crea_dw_29pm_3 = self._filter_soil_moisture_subset(sm_df, "CREA_DURUMWHEAT28", "2022-04-29 13:35:00", "2022-04-29 14:09:00")
            return [pd.concat([crea_dw_29pm_1, crea_dw_29pm_2, crea_dw_29pm_3], ignore_index=True)]
        return []

    def _caione_dw_interpolation_groups(self, sm_df, time_period_id):
        """ CAIONE durum wheat fields in April """
        if time_period_id == ht22.APR_28_AM:
            # CAIONE_DW, field 1, north part, 1 stripe
            apr28am_f1_north = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT29", "2022-04-28T09:10:00", "2022-04-28T10:28:00")
            # CAIONE_DW, field 1, south part, 2 stripes
            apr28am_f1_south_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT24", "2022-04-28T13:25:00", "2022-04-28T13:50:00")
            apr28am_f1_south_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT27", "2022-04-28T11:48:00", "2022-04-28T12:52:00")
            apr28am_f1_south = pd.concat([apr28am_f1_south_1, apr28am_f1_south_2], ignore_index=True)
            # CAIONE_DW, field 2, north part, 1 stripe
            apr28am_f2_north = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT29", "2022-04-28T10:38:00", "2022-04-28T11:06:00")
            # CAIONE_DW, field 2, south part, 2 stripes
            apr28am_f2_south_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT24", "2022-04-28T13:50:00", "2022-04-28T14:13:00")
            apr28am_f2_south_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT27", "2022-04-28T12:57:00", "2022-04-28T13:25:00")
            apr28am_f2_south = pd.concat([apr28am_f2_south_1, apr28am_f2_south_2], ignore_index=True)
            return [apr28am_f1_north, apr28am_f1_south, apr28am_f2_north, apr28am_f2_south]
        if time_period_id == ht22.APR_28_PM:
            # CAIONE_DW, field 1, north part, 1 stripe
            apr28pm_f1_north = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT29", "2022-04-28T14:38:00", "2022-04-28T15:16:00")
            # CAIONE_DW, field 1, south part, 2 stripes
            apr28pm_f1_south_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT24", "2022-04-28T17:00:00", "2022-04-28T17:20:00")
            apr28pm_f1_south_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT27", "2022-04-28T16:05:00", "2022-04-28T16:30:00")
            apr28pm_f1_south = pd.concat([apr28pm_f1_south_1, apr28pm_f1_south_2], ignore_index=True)
            # CAIONE_DW, field 2, north part, 1 stripe
            apr28pm_f2_north = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT29", "2022-04-28T15:28:00", "2022-04-28T15:56:00")
            # CAIONE_DW, field 2, south part, 2 stripes
            apr28pm_f2_south_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT24", "2022-04-28T17:22:00", "2022-04-28T17:41:00")
            apr28pm_f2_south_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT27", "2022-04-28T16:31:00", "2022-04-28T16:59:00")
            apr28pm_f2_south = pd.concat([apr28pm_f2_south_1, apr28pm_f2_south_2], ignore_index=True)
            return [apr28pm_f1_north, apr28pm_f1_south, apr28pm_f2_north, apr28pm_f2_south]
        if time_period_id == ht22.APR_29_AM:
            # CAIONE_DW, field 1, 3 stripes
            apr29am_f1_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT24", "2022-04-29 10:38:00", "2022-04-29 11:22:00")
            apr29am_f1_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT27", "2022-04-29 12:17:00", "2022-04-29 12:35:00")
            apr29am_f1_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT28", "2022-04-29 09:50:00", "2022-04-29 10:30:00")
            apr29am_f1 = pd.concat([apr29am_f1_1, apr29am_f1_2, apr29am_f1_3], ignore_index=True)
            # CAIONE_DW, field 2, 3 stripes
            apr29am_f2_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT24", "2022-04-29 11:25:00", "2022-04-29 12:13:00")
            apr29am_f2_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT27", "2022-04-29 12:36:00", "2022-04-29 12:55:00")
            apr29am_f2_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT28", "2022-04-29 09:06:00", "2022-04-29 09:43:00")
            apr29am_f2 = pd.concat([apr29am_f2_1, apr29am_f2_2, apr29am_f2_3], ignore_index=True)
            return [apr29am_f1, apr29am_f2]
        if time_period_id == ht22.APR_29_PM:
            # CAIONE_DW, field 1, 3 stripes
            apr29pm_f1_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT24", "2022-04-29 15:04:00", "2022-04-29 15:19:00")
            apr29pm_f1_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT27", "2022-04-29 14:25:00", "2022-04-29 14:41:00")
            apr29pm_f1_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE1_DURUMWHEAT28", "2022-04-29 13:28:00", "2022-04-29 13:56:00")
            apr29pm_f1 = pd.concat([apr29pm_f1_1, apr29pm_f1_2, apr29pm_f1_3], ignore_index=True)
            # CAIONE_DW, field 2, 3 stripes
            apr29pm_f2_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT24", "2022-04-29 15:20:00", "2022-04-29 15:34:00")
            apr29pm_f2_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT27", "2022-04-29 14:45:00", "2022-04-29 15:03:00")
            apr29pm_f2_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE2_DURUMWHEAT28", "2022-04-29 13:57:00", "2022-04-29 14:23:00")
            apr29pm_f2 = pd.concat([apr29pm_f2_1, apr29pm_f2_2, apr29pm_f2_3], ignore_index=True)
            return [apr29pm_f1, apr29pm_f2]
        return []

    def _crea_sf_interpolation_groups(self, sm_df, time_period_id):
        """ CREA sunflower field in June """
        if time_period_id == ht22.JUN_15_AM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_SUNFLOWER", "2022-06-15 08:43:00", "2022-06-15 09:11:00")]
        if time_period_id == ht22.JUN_15_PM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_SUNFLOWER", "2022-06-15 14:14:00", "2022-06-15 14:50:00")]
        if time_period_id == ht22.JUN_16_AM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_SUNFLOWER", "2022-06-16 08:45:00", "2022-06-16 09:14:00")]
        if time_period_id == ht22.JUN_16_PM:
            return [self._filter_soil_moisture_subset(sm_df, "CREA_SUNFLOWER", "2022-06-16 13:56:00", "2022-06-16 14:13:00")]
        return []

    def _crea_ma_interpolation_groups(self, sm_df, time_period_id):
        """ CREA maize field in June """
        if time_period_id == ht22.JUN_15_AM:
            jun15am_1 = self._filter_soil_moisture_subset(sm_df, "CREA_MAIS1", "2022-06-15 09:46:00", "2022-06-15 10:29:00")
            jun15am_2 = self._filter_soil_moisture_subset(sm_df, "CREA_MAIS2", "2022-06-15 09:12:00", "2022-06-15 09:45:00")
            return [pd.concat([jun15am_1, jun15am_2], ignore_index=True)]
        if time_period_id == ht22.JUN_15_PM:
            jun15pm_1 = self._filter_soil_moisture_subset(sm_df, "CREA_MAIS1", "2022-06-15 15:28:00", "2022-06-15 16:17:00")
            jun15pm_2 = self._filter_soil_moisture_subset(sm_df, "CREA_MAIS2", "2022-06-15 14:51:00", "2022-06-15 15:26:00")
            return [pd.concat([jun15pm_1, jun15pm_2], ignore_index=True)]
        if time_period_id == ht22.JUN_16_AM:
            jun16am_1 = self._filter_soil_moisture_subset(sm_df, "CREA_MAIS1", "2022-06-16 09:56:00", "2022-06-16 10:27:00")
            jun16am_2 = self._filter_soil_moisture_subset(sm_df, "CREA_MAIS2", "2022-06-16 09:18:00", "2022-06-16 09:55:00")
            return [pd.concat([jun16am_1, jun16am_2], ignore_index=True)]
        if time_period_id == ht22.JUN_16_PM:
            jun16pm_1 = self._filter_soil_moisture_subset(sm_df, "CREA_MAIS1", "2022-06-16 14:47:00", "2022-06-16 14:54:00")
            jun16pm_2 = self._filter_soil_moisture_subset(sm_df, "CREA_MAIS2", "2022-06-16 14:14:00", "2022-06-16 14:24:00")
            return [pd.concat([jun16pm_1, jun16pm_2], ignore_index=True)]
        return []

    def _caione_aa_interpolation_groups(self, sm_df, time_period_id):
        """ CAIONE alfalfa field in June """
        if time_period_id == ht22.JUN_15_AM:
            jun15am_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA1", "2022-06-15 09:48:00", "2022-06-15 10:13:00")
            jun15am_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA2", "2022-06-15 10:26:00", "2022-06-15 10:38:00")
            jun15am_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA3", "2022-06-15 10:42:00", "2022-06-15 11:00:00")
            return [pd.concat([jun15am_1, jun15am_2, jun15am_3], ignore_index=True)]
        if time_period_id == ht22.JUN_15_PM:
            jun15pm_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA1", "2022-06-15 15:00:00", "2022-06-15 15:25:00")
            jun15pm_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA2", "2022-06-15 15:40:00", "2022-06-15 15:54:00")
            jun15pm_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA3", "2022-06-15 15:56:00", "2022-06-15 16:08:00")
            return [pd.concat([jun15pm_1, jun15pm_2, jun15pm_3], ignore_index=True)]
        if time_period_id == ht22.JUN_16_AM:
            jun16am_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA1", "2022-06-16 11:00:00", "2022-06-16 11:12:00")
            jun16am_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA2", "2022-06-16 09:13:00", "2022-06-16 09:56:00")
            jun16am_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA3", "2022-06-16 09:54:00", "2022-06-16 10:30:00")
            return [pd.concat([jun16am_1, jun16am_2, jun16am_3], ignore_index=True)]
        if time_period_id == ht22.JUN_16_PM:
            jun16pm_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA1", "2022-06-16 14:06:00", "2022-06-16 14:18:00")
            jun16pm_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA2", "2022-06-16 14:20:00", "2022-06-16 14:32:00")
            jun16pm_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE_ALFAALFA3", "2022-06-16 14:39:00", "2022-06-16 14:51:00")
            return [pd.concat([jun16pm_1, jun16pm_2, jun16pm_3], ignore_index=True)]
        return []

    def _caione_ma_interpolation_groups(self, sm_df, time_period_id):
        """ CAIONE maize field in June """
        if time_period_id == ht22.JUN_15_AM:
            # west: 3 strips
            jun15am_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS1", "2022-06-15 09:05:00", "2022-06-15 10:04:00")
            jun15am_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS2", "2022-06-15 10:05:00", "2022-06-15 11:07:00")
            jun15am_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS3", "2022-06-15 11:26:00", "2022-06-15 12:19:00")
            jun15am_123 = pd.concat([jun15am_1, jun15am_2, jun15am_3], ignore_index=True)
            # east: 1 strip
            jun15am_4 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS4", "2022-06-15 09:00:00", "2022-06-15 09:34:00")
            return [jun15am_123, jun15am_4]
        if time_period_id == ht22.JUN_15_PM:
            # west: 3 strips
            jun15pm_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS1", "2022-06-15 14:33:00", "2022-06-15 15:16:00")
            jun15pm_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS2", "2022-06-15 15:18:00", "2022-06-15 16:03:00")
            jun15pm_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS3", "2022-06-15 16:09:00", "2022-06-15 16:47:00")
            jun15pm_123 = pd.concat([jun15pm_1, jun15pm_2, jun15pm_3], ignore_index=True)
            # east: 1 strip
            jun15pm_4 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS4", "2022-06-15 14:33:00", "2022-06-15 14:57:00")
            return [jun15pm_123, jun15pm_4]
        if time_period_id == ht22.JUN_16_AM:
            # west: 3 strips
            jun16am_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS1", "2022-06-16 09:20:00", "2022-06-16 10:10:00")
            jun16am_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS2", "2022-06-16 10:11:00", "2022-06-16 11:13:00")
            jun16am_3_valid_points = self._pt_range(27, 52) # points P1-P25 are missing, P26 exists but distorts the interpolation, use P27-P52
            jun16am_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS3", "2022-06-16 11:41:00", "2022-06-16 12:05:00", point_ids=jun16am_3_valid_points)
            jun16am_123 = pd.concat([jun16am_1, jun16am_2, jun16am_3], ignore_index=True)
            # east: 1 strip
            jun16am_4 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS4", "2022-06-16 11:19:00", "2022-06-16 11:44:00")
            return [jun16am_123, jun16am_4]
        if time_period_id == ht22.JUN_16_PM:
            # west: 3 strips
            jun16pm_1 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS1", "2022-06-16 14:00:00", "2022-06-16 14:38:00")
            jun16pm_2 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS2", "2022-06-16 14:40:00", "2022-06-16 15:21:00")
            jun16pm_3 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS3", "2022-06-16 15:22:00", "2022-06-16 15:53:00")
            jun16pm_123 = pd.concat([jun16pm_1, jun16pm_2, jun16pm_3], ignore_index=True)
            # east: 1 strip
            jun16pm_4 = self._filter_soil_moisture_subset(sm_df, "CAIONE_MAIS4", "2022-06-16 15:05:00", "2022-06-16 15:31:00")
            return [jun16pm_123, jun16pm_4]
        return []

    def _get_soil_moisture_interpolation_groups(self, region_name, time_period_id):
        """
        Return a list of pandas dataframes, each dataframe contains several points.
        Points within each dataframe are spatially close and soil moisture can be interpolated between them.
        Points in different dataframes should not be interpolated together but belong to the same region.

        Note that two dataframes may contain the same point (required for interpolation).
        You may use drop_duplicates after concatenating all dataframes to remove duplicates.
        """
        sm_df = self.read_hterra22_soil_moisture()
        if region_name == "CREA_BS_QU_SMALL_DEBUG": return self._crea_bs_qu_interpolation_groups(sm_df, time_period_id) # smaller debug region
        if region_name == ht22.CREA_BS_QU: return self._crea_bs_qu_interpolation_groups(sm_df, time_period_id)
        if region_name == ht22.CREA_DW: return self._crea_dw_interpolation_groups(sm_df, time_period_id)
        if region_name == ht22.CREA_SF: return self._crea_sf_interpolation_groups(sm_df, time_period_id)
        if region_name == ht22.CREA_MA: return self._crea_ma_interpolation_groups(sm_df, time_period_id)
        if region_name == ht22.CREA:
            return [ # all CREA groups in one list
                *self._crea_bs_qu_interpolation_groups(sm_df, time_period_id),
                *self._crea_dw_interpolation_groups(sm_df, time_period_id),
                *self._crea_sf_interpolation_groups(sm_df, time_period_id),
                *self._crea_ma_interpolation_groups(sm_df, time_period_id),
            ]
        if region_name == ht22.CAIONE_DW: return self._caione_dw_interpolation_groups(sm_df, time_period_id)
        if region_name == ht22.CAIONE_AA: return self._caione_aa_interpolation_groups(sm_df, time_period_id)
        if region_name == ht22.CAIONE_MA: return self._caione_ma_interpolation_groups(sm_df, time_period_id)
        if region_name == ht22.CAIONE:
            return [ # all CAIONE groups in one list
                *self._caione_dw_interpolation_groups(sm_df, time_period_id),
                *self._caione_aa_interpolation_groups(sm_df, time_period_id),
                *self._caione_ma_interpolation_groups(sm_df, time_period_id),
            ]
        raise ValueError(f"Unsupported region {region_name}")

    def _extend_lut_and_slc_coordinates(self, sm_points, band):
        campaign = ht22.HTERRA22Campaign(fc.get_polinsar_folder() / "01_projects/22HTERRA")
        fsar_pass = campaign.get_pass("22hterra0104", band)
        lut = fsar_pass.load_gtc_lut()
        min_northing, min_easting = lut.c1 # max_northing, max_easting = lut.c2
        lut_northing = sm_points["northing"] - min_northing
        lut_easting = sm_points["easting"] - min_easting
        # slc coordinates, assuming LUT posting of 1 meter (True for HTERRA22 campaign)
        lut_northing_idx = np.rint(lut_northing).astype(np.int64)
        lut_easting_idx = np.rint(lut_easting).astype(np.int64)
        point_az = lut.lut_az[lut_northing_idx, lut_easting_idx]
        point_rg = lut.lut_rg[lut_northing_idx, lut_easting_idx]
        # extend data frame
        sm_points_extended = sm_points.assign(lut_northing=lut_northing, lut_easting=lut_easting, azimuth=point_az, range=point_rg)
        return sm_points_extended

    def _interpolate_points_to_lut_region(self, sm_points_extended, band, region_name):
        (northing_min, northing_max), (easting_min, easting_max) = ht22.get_region_lut_coordinates(band, region_name)
        lut_northing = sm_points_extended["lut_northing"]
        lut_easting = sm_points_extended["lut_easting"]
        soil_moisture = sm_points_extended["soil_moisture"]
        axis_northing, axis_easting = np.arange(northing_min, northing_max), np.arange(easting_min, easting_max)
        grid_northing, grid_easting = np.meshgrid(axis_northing, axis_easting, indexing="ij")
        value_coords = np.array([lut_northing, lut_easting]).transpose((1, 0))
        sm_grid_lut_region = scipy.interpolate.griddata(value_coords, soil_moisture, (grid_northing, grid_easting), method="linear")
        return sm_grid_lut_region.astype(np.float32)

    def _interpolate_points_to_slc_region(self, sm_points_extended, band, region_name):
        (az_min, az_max), (rg_min, rg_max) = ht22.get_region_radar_coordinates(band, region_name)
        point_az = sm_points_extended["azimuth"]
        point_rg = sm_points_extended["range"]
        soil_moisture = sm_points_extended["soil_moisture"]
        axis_az, axis_rg = np.arange(az_min, az_max), np.arange(rg_min, rg_max)
        grid_az, grid_rg = np.meshgrid(axis_az, axis_rg, indexing="ij")
        value_coords = np.array([point_az, point_rg]).transpose((1, 0))
        sm_grid_slc_region = scipy.interpolate.griddata(value_coords, soil_moisture, (grid_az, grid_rg), method="linear", rescale=True)
        return sm_grid_slc_region.astype(np.float32)

    def get_sm_points_extended(self, band, region_name, time_period_id):
        """
        Get soil moisture point measurements for the specified region and time period.
        Soil moisture values range from 0 (0%) to 1 (100%).
        """
        interpolation_groups = self._get_soil_moisture_interpolation_groups(region_name, time_period_id)
        if len(interpolation_groups) == 0:
            sm_points = pd.DataFrame(columns=["date_time", "point_id", "field", "longitude", "latitude", "soil_moisture", "easting", "northing"])
        else:
            sm_points = pd.concat(interpolation_groups, ignore_index=True)
        sm_points = sm_points.drop_duplicates()
        sm_points_extended = self._extend_lut_and_slc_coordinates(sm_points, band)
        return sm_points_extended

    def get_sm_raster_lut_region(self, band, region_name, time_period_id):
        """
        Get interpolated soil moisture in LUT coordinate grid for the specified region and time period.    
        Soil moisture values range from 0 (0%) to 1 (100%).
        """
        interpolation_groups = self._get_soil_moisture_interpolation_groups(region_name, time_period_id)
        (northing_min, northing_max), (easting_min, easting_max) = ht22.get_region_lut_coordinates(band, region_name)
        region_shape = (northing_max - northing_min, easting_max - easting_min)
        sm_raster_lut_region = np.full(region_shape, fill_value=np.nan, dtype=np.float32)
        for sm_points in interpolation_groups:
            sm_points_extended = self._extend_lut_and_slc_coordinates(sm_points, band)
            sm_interpolated = self._interpolate_points_to_lut_region(sm_points_extended, band, region_name)
            valid_points = np.isfinite(sm_interpolated)
            sm_raster_lut_region[valid_points] = sm_interpolated[valid_points]
        return sm_raster_lut_region

    def get_sm_raster_slc_region(self, band, region_name, time_period_id):
        """
        Get interpolated soil moisture in SLC coordinate grid for the specified region and time period.    
        Soil moisture values range from 0 (0%) to 1 (100%).
        """
        interpolation_groups = self._get_soil_moisture_interpolation_groups(region_name, time_period_id)
        (az_min, az_max), (rg_min, rg_max) = ht22.get_region_radar_coordinates(band, region_name)
        region_shape = (az_max - az_min, rg_max - rg_min)
        sm_raster_slc_region = np.full(region_shape, fill_value=np.nan, dtype=np.float32)
        for sm_points in interpolation_groups:
            sm_points_extended = self._extend_lut_and_slc_coordinates(sm_points, band)
            sm_interpolated = self._interpolate_points_to_slc_region(sm_points_extended, band, region_name)
            valid_points = np.isfinite(sm_interpolated)
            sm_raster_slc_region[valid_points] = sm_interpolated[valid_points]
        return sm_raster_slc_region
