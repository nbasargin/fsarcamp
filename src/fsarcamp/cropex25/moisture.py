"""
Data loader for soil moisture ground measurements for the CROPEX 2025 F-SAR campaign.

PRELIMINARY!
"""

import pathlib
import pandas as pd
import fsarcamp.cropex25 as cr25


class CROPEX25Moisture:
    def __init__(self, data_folder):
        """
        Data loader for soil moisture ground measurements for the CROPEX 2025 campaign.
        `data_folder` defines the data folder that contains the CSV files with soil moisture measurements.
        The PRELIMINARY path on the DLR-HR server as of July 2025:
        "/data/HR_Data/Pol-InSAR_InfoRetrieval/01_projects/25CROPEX/Preliminary_Data"
        """
        self.data_folder = pathlib.Path(data_folder)

    def load_soil_moisture_points_eitelsried(self, period_name: str, region_name: str):
        """
        Load soil moisture ground measurements for the specified region/field and time period.

        Returns a pandas dataframe with following columns:
            "date_time" - date and time of the measurement
            "longitude", "latitude" - geographical coordinates
            "field_id" - indicates the field where the point was taken
            "point_id" - point ID
            "soil_moisture" - average soil moisture from several samples at that position, value ranges from 0 to 1
            "soil_moisture_1", ..., "soil_moisture_6" - individual moisture measurements at that position
        Optional, only for the Eitelsried fields:
            "mv_1", ..., "mv_6" - individual sensor readings in millivolt
        """
        region_to_field_id = {
            cr25.EITELSRIED_MAIZE: "Eitelsried_Maize",
            cr25.EITELSRIED_POTATO: "Eitelsried_Potato",
            cr25.EITELSRIED_WHEAT: "Eitelsried_Wheat",
        }
        period_to_date_flight = {
            cr25.APR_16: ("2025-04-16", ""),
            cr25.APR_22: ("2025-04-22", ""),
            cr25.APR_25: ("2025-04-25", ""),
            cr25.APR_28_MORN: ("2025-04-28", "_1"),
            cr25.APR_28_NOON: ("2025-04-28", "_2"),
            cr25.APR_28_EVEN: ("2025-04-28", "_3"),
            cr25.MAY_11: ("2025-05-11", ""),
            cr25.MAY_16: ("2025-05-16", ""),
            cr25.MAY_21: ("2025-05-21", ""),
            cr25.MAY_27: ("2025-05-27", ""),
            cr25.JUN_03_MORN: ("2025-06-03", "_1"),
            cr25.JUN_03_NOON: ("2025-06-03", "_2"),
            cr25.JUN_03_EVEN: ("2025-06-03", "_3"),
            cr25.JUN_06: ("2025-06-06", ""),
            cr25.JUN_12: ("2025-06-12", ""),
            cr25.JUN_18: ("2025-06-18", ""),
            cr25.JUN_24: ("2025-06-24", ""),
            cr25.JUN_30: ("2025-06-30", ""),
            cr25.JUL_03: ("2025-07-03", ""),
            cr25.JUL_09: ("2025-07-09", ""),
            cr25.JUL_15_MORN: ("2025-07-15", "_1"),
            cr25.JUL_15_NOON: ("2025-07-15", "_2"),
            cr25.JUL_15_EVEN: ("2025-07-15", "_3"),
            cr25.JUL_21: ("2025-07-21", ""),
        }
        field_id = region_to_field_id[region_name]
        date_str, flight_suffix = period_to_date_flight[period_name]
        file_path = self.data_folder / f"{date_str}_{field_id}/{date_str}_{field_id}_SoilMoisture{flight_suffix}.csv"
        df = pd.read_csv(file_path)
        # average soil moisture
        sm_vals = df[["soil_moisture_1", "soil_moisture_2", "soil_moisture_3", "soil_moisture_4", "soil_moisture_5", "soil_moisture_6"]]
        sm_avg = sm_vals.mean(axis=1)
        df = df.assign(soil_moisture=sm_avg)
        return df
