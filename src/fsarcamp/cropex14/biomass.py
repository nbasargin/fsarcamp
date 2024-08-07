

import pathlib
import datetime
import re
import numpy as np
import pandas as pd
import fsarcamp as fc
import fsarcamp.cropex14 as cr14

class CROPEX14Biomass:
    def __init__(self, data_folder, cropex14campaign: cr14.CROPEX14Campaign, verbose=False):
        """
        Data loader for biomass ground measurements for the CROPEX 2014 campaign.

        Arguments:
            data_folder: path to the data folder that contains the XLSX files with biomass measurements
            cropex14campaign: reference to the F-SAR campaign, required to geocode points to the SLC coordinates

        Usage example (data paths valid for DLR-HR server as of August 2024):
            import fsarcamp as fc
            import fsarcamp.cropex14 as cr14
            campaign = cr14.CROPEX14Campaign(fc.get_polinsar_folder() / "01_projects/CROPEX/CROPEX14")
            biomass_folder = fc.get_polinsar_folder() / "Ground_truth/Wallerfing_campaign_May_August_2014/Data/ground_measurements/biomass"
            biomass = cr14.CROPEX14Biomass(biomass_folder, campaign)
        """
        self.data_folder = pathlib.Path(data_folder)
        self.cropex14campaign = cropex14campaign
        self.verbose = verbose

    def _to_float(self, value):
        try:
            if isinstance(value, str):
                matches = re.match("^(\d+)-(\d+)$", value)
                if matches:
                    # string a range of values like "9-10" -> take the average
                    val1 = float(matches.group(1))
                    val2 = float(matches.group(2))
                    result = (val1 + val2) / 2
                    if self.verbose: print(f"interpreting '{value}' as ({val1} + {val2}) / 2 = {result}")
                    return result
                if re.match("^(\d+),(\d+)$", value):
                    # comma used as decimal separator
                    result = float(value.replace(",", "."))
                    if self.verbose: print(f"interpreting '{value}' as {result}")
                    return result
            return float(value)
        except:
            return np.nan
        
    def _read_biomass_file(self, file_path):
        """
        Read the excel file with ground measurements.
        The excel files have a rather complicated formatting.
        Some values are missing, some are invalid, some have a range (e.g. 9-10).
        """
        df = pd.read_excel(file_path, sheet_name="Tabelle1", header=None)
        cols = df.shape[1]
        sheet_date = datetime.datetime.strptime(str(df.iat[0, 0]).replace("Date: ", ""), "%d.%m.%Y").date()
        df_rows = []
        for col in range(1, cols):
            point_id = df.iat[1, col]
            if str(point_id) == "nan":
                continue # data sheet 2014-07-30 has a comment that increases number of columns
            time = df.iat[3, col]
            if not isinstance(time, datetime.time):
                time = datetime.time(0, 0, 0) # do not accept "----" strings
            date_time = datetime.datetime.combine(sheet_date, time)            
            # collect df rows
            easting = self._to_float(df.iat[12, col])
            northing = self._to_float(df.iat[13, col])
            latitude = self._to_float(df.iat[8, col])
            longitude = self._to_float(df.iat[9, col])
            # vegetation parameters
            veg_height = self._to_float(df.iat[25, col]) # cm
            row_orientation = self._to_float(df.iat[28, col]) # degrees
            row_spacing = self._to_float(df.iat[29, col]) # cm
            plants_per_meter = self._to_float(df.iat[30, col])
            bbch = self._to_float(df.iat[31, col])
            weight_025m2 = self._to_float(df.iat[34, col]) # g (per 0.25 m^2)
            weight_100m2 = self._to_float(df.iat[35, col]) # g (per 1 m^2)
            weight_bag = self._to_float(df.iat[36, col]) # g
            # sample 1
            sample1_wet = self._to_float(df.iat[37, col]) # g
            sample1_dry = self._to_float(df.iat[38, col]) # g
            sample1_vwc_with_bag = self._to_float(df.iat[39, col]) / 100 # includes sample bag weight
            sample1_vwc = self._to_float(df.iat[40, col]) / 100
            # sample 2
            sample2_wet = self._to_float(df.iat[41, col]) # g
            sample2_dry = self._to_float(df.iat[42, col]) # g
            sample2_vwc_with_bag = self._to_float(df.iat[43, col]) / 100 # includes sample bag weight
            sample2_vwc = self._to_float(df.iat[44, col]) / 100
            # soil moisture, read only "vol.%", ignore "mV"
            # up to 6 individual measurements per point: soil_moisture_1 to soil_moisture_6 (some may be NaN)
            soil_moisture_vals = []
            for idx in range(54, 60):
                value = self._to_float(df.iat[idx, col]) / 100
                soil_moisture_vals.append(value)
            if np.sum(np.isfinite(soil_moisture_vals)) > 0:
                soil_moisture = np.nanmean(soil_moisture_vals)
            else:
                soil_moisture = np.nan
            data_src = file_path.name
            # collect row values
            df_rows.append((
                date_time, point_id, longitude, latitude, northing, easting,
                veg_height, row_orientation, row_spacing, plants_per_meter,
                bbch, weight_025m2, weight_100m2, weight_bag,
                sample1_wet, sample1_dry, sample1_vwc_with_bag, sample1_vwc,
                sample2_wet, sample2_dry, sample2_vwc_with_bag, sample2_vwc,
                soil_moisture, *soil_moisture_vals, data_src
            ))
        return pd.DataFrame(df_rows, columns=[
            "date_time", "point_id", "longitude", "latitude", "northing", "easting",
            "veg_height", "row_orientation", "row_spacing", "plants_per_meter",
            "bbch", "weight_025m2", "weight_100m2", "weight_bag",
            "sample1_wet", "sample1_dry", "sample1_vwc_with_bag", "sample1_vwc",
            "sample2_wet", "sample2_dry", "sample2_vwc_with_bag", "sample2_vwc",
            "soil_moisture", "soil_moisture_1", "soil_moisture_2", "soil_moisture_3",
            "soil_moisture_4", "soil_moisture_5", "soil_moisture_6", "data_src",
        ])
    
    def load_biomass_points(self, band=None, pass_name=None):
        all_dfs = [ 
            self._read_biomass_file(self.data_folder / "Veg_Wallerfing_2014_05_15.xlsx"),
            self._read_biomass_file(self.data_folder / "Veg_Wallerfing_2014_05_22.xlsx"),
            self._read_biomass_file(self.data_folder / "Veg_Wallerfing_2014_06_04.xlsx"),
            self._read_biomass_file(self.data_folder / "Veg_Wallerfing_2014_06_12.xlsx"),
            self._read_biomass_file(self.data_folder / "Veg_Wallerfing_2014_06_18.xlsx"),
            self._read_biomass_file(self.data_folder / "Veg_Wallerfing_2014_07_03.xlsx"),
            self._read_biomass_file(self.data_folder / "Veg_Wallerfing_2014_07_18.xlsx"),
            self._read_biomass_file(self.data_folder / "Veg_Wallerfing_2014_07_24.xlsx"),
            self._read_biomass_file(self.data_folder / "Veg_Wallerfing_2014_07_30.xlsx"),
            self._read_biomass_file(self.data_folder / "Veg_Wallerfing_2014_08_21.xlsx"),
        ]
        combined_df = pd.concat(all_dfs, ignore_index=True)
        # TODO geocoding to azimuth / range
        return combined_df

if __name__ == "__main__":
    campaign = cr14.CROPEX14Campaign(fc.get_polinsar_folder() / "01_projects/CROPEX/CROPEX14")
    biomass_folder = fc.get_polinsar_folder() / "Ground_truth/Wallerfing_campaign_May_August_2014/Data/ground_measurements/biomass"
    biomass = CROPEX14Biomass(biomass_folder, campaign, verbose=True)
    df = biomass.load_biomass_points()
    # TODO: compare values with manual sheets from sarctd, add more values manually if needed
    df.to_csv("visualization/cropex_biomass.csv", index=False)
