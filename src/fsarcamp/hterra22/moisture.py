"""
Data loader for soil moisture ground measurements for the HTERRA 2022 campaign.
"""

import pathlib
from datetime import datetime
import pandas as pd
import fsarcamp.hterra22 as ht22


class HTERRA22Moisture:
    def __init__(self, data_folder):
        """
        Data loader for soil moisture ground measurements for the HTERRA 2022 campaign.
        `data_folder` defines the data folder that contains the CSV files with soil moisture measurements.
        The path on the DLR-HR server as of November 2024:
        "/data/HR_Data/Pol-InSAR_InfoRetrieval/Ground_truth/HTerra_soil_2022/DataPackage_final"
        """
        self.data_folder = pathlib.Path(data_folder)

    def _read_moisture_csv(self, file_path):
        df = pd.read_csv(file_path)
        df = df.dropna()
        df = df.rename(
            columns={
                "DATE_TIME": "date_time",
                "POINT_ID": "point_id",
                "FIELD": "field",
                "LATITUDE": "latitude",
                "LONGITUDE": "longitude",
                # soil moisture is either available as SM_CAL_ALL or SM_CAL
                "SM_CAL_ALL": "soil_moisture",
                "SM_CAL": "soil_moisture",
            }
        )
        df["date_time"] = pd.to_datetime(df["date_time"])
        return df

    def _filter_subset(self, sm_df, field_stripe, iso_date_from, iso_date_to):
        """
        Filter dataframe with all points by field_stripe and date range.
        Parameters:
            sm_df: dataframe with all soil moisture measurements
            field_stripe: field or stripe to take points from, should match the "field" column of the dataframe
            iso_date_from: start date and time, in ISO format like "2022-04-28T08:45:00"
            iso_date_to: end date and time, in ISO format like "2022-04-28T11:09:00"
        """
        date_from = datetime.fromisoformat(iso_date_from)
        date_to = datetime.fromisoformat(iso_date_to)
        sm_df_filtered = sm_df[
            (sm_df["field"] == field_stripe) & (sm_df["date_time"] >= date_from) & (sm_df["date_time"] <= date_to)
        ]
        return sm_df_filtered

    def load_soil_moisture_points(self):
        """
        Load all point soil moisture measurements.
        Returns a pandas dataframe with following columns:
            "date_time" - date and time of the measurement
            "point_id" - point ID
            "field" - indicates the field where the point was taken (including the field stripe)
            "longitude", "latitude" - geographical coordinates
            "soil_moisture" - calibrated soil moisture at that poition, value ranges from 0 to 1
        """
        # read all points
        dfs = []
        for filename in [
            "CA1_DW_24.csv",
            "CA1_DW_27.csv",
            "CA1_DW_28.csv",
            "CA1_DW_29.csv",
            "CA2_DW_24.csv",
            "CA2_DW_27.csv",
            "CA2_DW_28.csv",
            "CA2_DW_29.csv",
        ]:
            april_caione_folder = self.data_folder / "April22/soil_moisture_sensors/CAIONE"
            dfs.append(self._read_moisture_csv(april_caione_folder / filename))
        for filename in ["CREA_BS_APRIL.csv", "CREA_DW26.csv", "CREA_DW27.csv", "CREA_DW28.csv", "CREA_DW29.csv"]:
            april_crea_folder = self.data_folder / "April22/soil_moisture_sensors/CREA"
            dfs.append(self._read_moisture_csv(april_crea_folder / filename))
        for filename in [
            "CA_AA_1.csv",
            "CA_AA_2.csv",
            "CA_AA_3.csv",
            "CA_MA_1.csv",
            "CA_MA_2.csv",
            "CA_MA_3.csv",
            "CA_MA_4.csv",
        ]:
            june_caione_folder = self.data_folder / "June22/soil_moisture_sensors/CAIONE"
            dfs.append(self._read_moisture_csv(june_caione_folder / filename))
        for filename in ["CREA_MA_1.csv", "CREA_MA_2.csv", "CREA_QUINOA.csv", "CREA_SF.csv"]:
            june_crea_folder = self.data_folder / "June22/soil_moisture_sensors/CREA"
            dfs.append(self._read_moisture_csv(june_crea_folder / filename))
        points = pd.concat(dfs, ignore_index=True)
        return points

    def filter_points_by_period(self, points: pd.DataFrame, period_name: str):
        """
        Filter the points by the specified period.
        The period is specified by name, see `fsarcamp.hterra22.dates` for allowed values.
        """
        filter_dict = {
            ht22.APR_28_AM: [
                ("CREA_BARESOIL", "2022-04-28 08:45:00", "2022-04-28 11:09:00"),
                ("CREA_DURUMWHEAT26", "2022-04-28 10:42:00", "2022-04-28 11:34:00"),
                ("CREA_DURUMWHEAT27", "2022-04-28 09:42:00", "2022-04-28 10:40:00"),
                ("CREA_DURUMWHEAT29", "2022-04-28 08:56:00", "2022-04-28 09:41:00"),
                ("CAIONE1_DURUMWHEAT29", "2022-04-28 09:10:00", "2022-04-28 10:28:00"),
                ("CAIONE1_DURUMWHEAT24", "2022-04-28 13:25:00", "2022-04-28 13:50:00"),
                ("CAIONE1_DURUMWHEAT27", "2022-04-28 11:48:00", "2022-04-28 12:52:00"),
                ("CAIONE2_DURUMWHEAT29", "2022-04-28 10:38:00", "2022-04-28 11:06:00"),
                ("CAIONE2_DURUMWHEAT24", "2022-04-28 13:50:00", "2022-04-28 14:13:00"),
                ("CAIONE2_DURUMWHEAT27", "2022-04-28 12:57:00", "2022-04-28 13:25:00"),
            ],
            ht22.APR_28_PM: [
                ("CREA_BARESOIL", "2022-04-28 14:13:00", "2022-04-28 16:39:00"),
                ("CREA_DURUMWHEAT26", "2022-04-28 16:11:00", "2022-04-28 16:50:00"),
                ("CREA_DURUMWHEAT27", "2022-04-28 15:27:00", "2022-04-28 16:07:00"),
                ("CREA_DURUMWHEAT29", "2022-04-28 14:35:00", "2022-04-28 15:26:00"),
                ("CAIONE1_DURUMWHEAT29", "2022-04-28 14:38:00", "2022-04-28 15:16:00"),
                ("CAIONE1_DURUMWHEAT24", "2022-04-28 17:00:00", "2022-04-28 17:20:00"),
                ("CAIONE1_DURUMWHEAT27", "2022-04-28 16:05:00", "2022-04-28 16:30:00"),
                ("CAIONE2_DURUMWHEAT29", "2022-04-28 15:28:00", "2022-04-28 15:56:00"),
                ("CAIONE2_DURUMWHEAT24", "2022-04-28 17:22:00", "2022-04-28 17:41:00"),
                ("CAIONE2_DURUMWHEAT27", "2022-04-28 16:31:00", "2022-04-28 16:59:00"),
            ],
            ht22.APR_29_AM: [
                ("CREA_BARESOIL", "2022-04-29 08:43:00", "2022-04-29 10:28:00"),
                ("CREA_DURUMWHEAT26", "2022-04-29 10:32:00", "2022-04-29 11:21:00"),
                ("CREA_DURUMWHEAT27", "2022-04-29 09:40:00", "2022-04-29 10:31:00"),
                ("CREA_DURUMWHEAT28", "2022-04-29 08:50:00", "2022-04-29 09:38:00"),
                ("CAIONE1_DURUMWHEAT24", "2022-04-29 10:38:00", "2022-04-29 11:22:00"),
                ("CAIONE1_DURUMWHEAT27", "2022-04-29 12:17:00", "2022-04-29 12:35:00"),
                ("CAIONE1_DURUMWHEAT28", "2022-04-29 09:50:00", "2022-04-29 10:30:00"),
                ("CAIONE2_DURUMWHEAT24", "2022-04-29 11:25:00", "2022-04-29 12:13:00"),
                ("CAIONE2_DURUMWHEAT27", "2022-04-29 12:36:00", "2022-04-29 12:55:00"),
                ("CAIONE2_DURUMWHEAT28", "2022-04-29 09:06:00", "2022-04-29 09:43:00"),
            ],
            ht22.APR_29_PM: [
                ("CREA_BARESOIL", "2022-04-29 13:30:00", "2022-04-29 15:01:00"),
                ("CREA_DURUMWHEAT26", "2022-04-29 15:07:00", "2022-04-29 15:55:00"),
                ("CREA_DURUMWHEAT27", "2022-04-29 14:14:00", "2022-04-29 15:06:00"),
                ("CREA_DURUMWHEAT28", "2022-04-29 13:35:00", "2022-04-29 14:09:00"),
                ("CAIONE1_DURUMWHEAT24", "2022-04-29 15:04:00", "2022-04-29 15:19:00"),
                ("CAIONE1_DURUMWHEAT27", "2022-04-29 14:25:00", "2022-04-29 14:41:00"),
                ("CAIONE1_DURUMWHEAT28", "2022-04-29 13:28:00", "2022-04-29 13:56:00"),
                ("CAIONE2_DURUMWHEAT24", "2022-04-29 15:20:00", "2022-04-29 15:34:00"),
                ("CAIONE2_DURUMWHEAT27", "2022-04-29 14:45:00", "2022-04-29 15:03:00"),
                ("CAIONE2_DURUMWHEAT28", "2022-04-29 13:57:00", "2022-04-29 14:23:00"),
            ],
            ht22.JUN_15_AM: [
                ("CREA_QUINOA", "2022-06-15 08:39:00", "2022-06-15 10:33:00"),
                ("CREA_SUNFLOWER", "2022-06-15 08:43:00", "2022-06-15 09:11:00"),
                ("CREA_MAIS1", "2022-06-15 09:46:00", "2022-06-15 10:29:00"),
                ("CREA_MAIS2", "2022-06-15 09:12:00", "2022-06-15 09:45:00"),
                ("CAIONE_ALFAALFA1", "2022-06-15 09:48:00", "2022-06-15 10:13:00"),
                ("CAIONE_ALFAALFA2", "2022-06-15 10:26:00", "2022-06-15 10:38:00"),
                ("CAIONE_ALFAALFA3", "2022-06-15 10:42:00", "2022-06-15 11:00:00"),
                ("CAIONE_MAIS1", "2022-06-15 09:05:00", "2022-06-15 10:04:00"),
                ("CAIONE_MAIS2", "2022-06-15 10:05:00", "2022-06-15 11:07:00"),
                ("CAIONE_MAIS3", "2022-06-15 11:26:00", "2022-06-15 12:19:00"),
                ("CAIONE_MAIS4", "2022-06-15 09:00:00", "2022-06-15 09:34:00"),
            ],
            ht22.JUN_15_PM: [
                ("CREA_QUINOA", "2022-06-15 14:02:00", "2022-06-15 15:16:00"),
                ("CREA_SUNFLOWER", "2022-06-15 14:14:00", "2022-06-15 14:50:00"),
                ("CREA_MAIS1", "2022-06-15 15:28:00", "2022-06-15 16:17:00"),
                ("CREA_MAIS2", "2022-06-15 14:51:00", "2022-06-15 15:26:00"),
                ("CAIONE_ALFAALFA1", "2022-06-15 15:00:00", "2022-06-15 15:25:00"),
                ("CAIONE_ALFAALFA2", "2022-06-15 15:40:00", "2022-06-15 15:54:00"),
                ("CAIONE_ALFAALFA3", "2022-06-15 15:56:00", "2022-06-15 16:08:00"),
                ("CAIONE_MAIS1", "2022-06-15 14:33:00", "2022-06-15 15:16:00"),
                ("CAIONE_MAIS2", "2022-06-15 15:18:00", "2022-06-15 16:03:00"),
                ("CAIONE_MAIS3", "2022-06-15 16:09:00", "2022-06-15 16:47:00"),
                ("CAIONE_MAIS4", "2022-06-15 14:33:00", "2022-06-15 14:57:00"),
            ],
            ht22.JUN_16_AM: [
                ("CREA_QUINOA", "2022-06-16 08:39:00", "2022-06-16 09:49:00"),
                ("CREA_SUNFLOWER", "2022-06-16 08:45:00", "2022-06-16 09:14:00"),
                ("CREA_MAIS1", "2022-06-16 09:56:00", "2022-06-16 10:27:00"),
                ("CREA_MAIS2", "2022-06-16 09:18:00", "2022-06-16 09:55:00"),
                ("CAIONE_ALFAALFA1", "2022-06-16 11:00:00", "2022-06-16 11:12:00"),
                ("CAIONE_ALFAALFA2", "2022-06-16 09:13:00", "2022-06-16 09:56:00"),
                ("CAIONE_ALFAALFA3", "2022-06-16 09:54:00", "2022-06-16 10:30:00"),
                ("CAIONE_MAIS1", "2022-06-16 09:20:00", "2022-06-16 10:10:00"),
                ("CAIONE_MAIS2", "2022-06-16 10:11:00", "2022-06-16 11:13:00"),
                ("CAIONE_MAIS3", "2022-06-16 11:41:00", "2022-06-16 12:05:00"),
                ("CAIONE_MAIS4", "2022-06-16 11:19:00", "2022-06-16 11:44:00"),
            ],
            ht22.JUN_16_PM: [
                ("CREA_QUINOA", "2022-06-16 13:48:00", "2022-06-16 14:42:00"),
                ("CREA_SUNFLOWER", "2022-06-16 13:56:00", "2022-06-16 14:13:00"),
                ("CREA_MAIS1", "2022-06-16 14:47:00", "2022-06-16 14:54:00"),
                ("CREA_MAIS2", "2022-06-16 14:14:00", "2022-06-16 14:24:00"),
                ("CAIONE_ALFAALFA1", "2022-06-16 14:06:00", "2022-06-16 14:18:00"),
                ("CAIONE_ALFAALFA2", "2022-06-16 14:20:00", "2022-06-16 14:32:00"),
                ("CAIONE_ALFAALFA3", "2022-06-16 14:39:00", "2022-06-16 14:51:00"),
                ("CAIONE_MAIS1", "2022-06-16 14:00:00", "2022-06-16 14:38:00"),
                ("CAIONE_MAIS2", "2022-06-16 14:40:00", "2022-06-16 15:21:00"),
                ("CAIONE_MAIS3", "2022-06-16 15:22:00", "2022-06-16 15:53:00"),
                ("CAIONE_MAIS4", "2022-06-16 15:05:00", "2022-06-16 15:31:00"),
            ],
        }
        filters = filter_dict[period_name]
        dataframes = [self._filter_subset(points, *reg_time_filter) for reg_time_filter in filters]
        result = pd.concat(dataframes, ignore_index=True)
        return result
