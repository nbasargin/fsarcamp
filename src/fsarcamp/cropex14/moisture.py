"""
Data loader for soil moisture ground measurements for the CROPEX 2014 F-SAR campaign.
Note: a few additional soil moisture measurements are available in the biomass measurements, not included here.
"""
import pathlib
import datetime
import numpy as np
import pandas as pd
import fsarcamp as fc
import fsarcamp.cropex14 as cr14

class CROPEX14Moisture:
    def __init__(self, data_folder, cropex14campaign: cr14.CROPEX14Campaign):
        """
        Data loader for soil moisture ground measurements for the CROPEX 2014 campaign.

        Arguments:
            data_folder: path to the data folder that contains the XLSX files with soil moisture measurements
            cropex14campaign: reference to the F-SAR campaign, required to geocode points to the SLC coordinates

        Usage example (data paths valid for DLR-HR server as of May 2024):
            import fsarcamp as fc
            import fsarcamp.cropex14 as cr14
            campaign = cr14.CROPEX14Campaign(fc.get_polinsar_folder() / "01_projects/CROPEX/CROPEX14")
            moisture_folder = fc.get_polinsar_folder() / "Ground_truth/Wallerfing_campaign_May_August_2014/Data/ground_measurements/soil_moisture"
            moisture = cr14.CROPEX14Moisture(moisture_folder, campaign)
        """
        self.data_folder = pathlib.Path(data_folder)
        self.cropex14campaign = cropex14campaign

    def _to_float(self, value):
        try:
            return float(value)
        except:
            return np.nan

    def _read_soil_moisture_sheet(self, file_path, sheet_name, num_rows, field_name, point_id_offset=0):
        """
        Read one sheet of the excel file with ground measurements.
        The excel files have a rather complicated formatting and suspicious values in some cases.
        """
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        date_string = f"{df.iat[4, 4]} {df.iat[4, 6]} {df.iat[4, 8]}" # string like "22 April 2014"
        date = datetime.datetime.strptime(date_string, "%d %B %Y")
        time = df.iat[5, 4]
        if not isinstance(time, datetime.time):
            time = datetime.time(0, 0, 0)
        date_time = datetime.datetime.combine(date, time)
        # collect df rows, each row has following colums:
        # date_time, point_id, field, latitude, longitude, easting, northing, soil_moisture
        # and 6 individual measurements per point: soil_moisture_1 to soil_moisture_6 (some may be NaN)
        # soil moisture values range from 0 to 1 (100%) and represent the volumetric moisture
        df_rows = []
        for row in range(19, 19 + num_rows):
            point_number = int(df.iat[row, 1])
            point_id = f"P_{point_number + point_id_offset}"
            # coords
            latitude = self._to_float(df.iat[row, 2])
            longitude = self._to_float(df.iat[row, 3])
            if np.isnan(latitude) or np.isnan(longitude):
                continue
            # read soil moisture (vol.%), other values in the sheet are not used here
            soil_moisture_vals = []
            for idx in range(4, 10):
                value = self._to_float(df.iat[row, idx]) / 100
                soil_moisture_vals.append(value)
            if np.all(np.isnan(soil_moisture_vals)):
                continue
            soil_moisture = np.nanmean(soil_moisture_vals)
            df_rows.append((
                date_time, point_id, field_name, longitude, latitude,
                soil_moisture, *soil_moisture_vals,
            ))
        return pd.DataFrame(df_rows, columns=[
            "date_time", "point_id", "field", "longitude", "latitude", "soil_moisture",
            "soil_moisture_1", "soil_moisture_2", "soil_moisture_3", "soil_moisture_4", "soil_moisture_5", "soil_moisture_6",
        ])

    def _extend_df_coords(self, df, band, pass_name):
        fsar_pass = self.cropex14campaign.get_pass(pass_name, band)
        lut = fsar_pass.load_gtc_sr2geo_lut()
        latitude = df["latitude"].to_numpy()
        longitude = df["longitude"].to_numpy()
        northing, easting = fc.geocode_lat_lon_to_north_east(longitude, latitude, lut)
        lut_northing = (northing - lut.min_north) / lut.pixel_spacing_north
        lut_easting = (easting - lut.min_east) / lut.pixel_spacing_east
        point_az, point_rg = fc.geocode_north_east_to_az_rg(northing, easting, lut)
        # extend data frame
        df_extended = df.assign(
            northing=northing,
            easting=easting,
            lut_northing=lut_northing,
            lut_easting=lut_easting,
            azimuth=point_az,
            range=point_rg,
        )
        return df_extended

    def load_soil_moisture_points(self, band=None, pass_name=None):
        """
        Load point soil moisture measurements. If band and pass_name are provided, the points coordinates
        (longitude, latitude) will be additionally geocoded to the RGI azimuth and range coordinates using the F-SAR GTC-LUT files.

        Arguments:
            band: band ("X", "C", or "L"), optional
            pass_name: pass name, optional

        Returns:
            Pandas dataframe with following columns:
                "date_time" - date and time of the measurement, time is missing for some points and set to 0:00
                "point_id" - point ID, based on the row number of the excel sheet
                "field" - indicates the field where the point was taken ("Triangular", "Meteo", or "Big")
                "longitude", "latitude" - geographical coordinates
                "soil_moisture" - average soil moisture from several samples at that position, value ranges from 0 to 1
                "soil_moisture_1", ..., "soil_moisture_6" - individual moisture measurements at that position
            If band and pass_name are provided, additionals columns are added:
                "northing", "easting" - geographical coordinates in the LUT coordinate system (UTM zone 33)
                "lut_northing", "lut_easting" - pixel coordinates within the LUT
                "azimuth", "range" - pixel coordinates within the SLC
        """
        get_path = lambda suffix: self.data_folder / f"Wallerfing_soil_moisture_{suffix}"
        all_dfs = []
        # field names
        name_triangular = "Triangular"
        name_meteo = "Meteo"
        name_big = "Big" # can further be subdivided into BigCorn, BugCucumbers, BugSugarBeet
        # 2014_04_09
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_04_09.xlsx"), "Triangular Field", 11, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_04_09.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_04_09.xlsx"), "Big Field", 62, name_big))
        # 2014_04_10
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_04_10.xlsx"), "Triangular Field", 11, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_04_10.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_04_10.xlsx"), "Big Field", 47, name_big))
        # 2014_04_11
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_04_11.xlsx"), "Triangular Field", 11, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_04_11.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_04_11.xlsx"), "Big Field", 42, name_big))
        # 2014_05_15
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_05_15.xlsx"), "Triangular Field", 9, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_05_15.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_05_15.xlsx"), "Big Field", 51, name_big)) # one point is missing, can be obtained from cucumbers sheet
        # 2014_05_22
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_05_22.xlsx"), "Triangular Field", 11, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_05_22.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_05_22.xlsx"), "Big Field", 54, name_big))
        # 2014_06_04
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_04.xlsx"), "Triangular Field", 11, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_04.xlsx"), "Meteorological Station", 12, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_04.xlsx"), "Big Field", 46, name_big))
        # 2014_06_12
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_12.xlsx"), "Triangular Field", 8, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_12.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_12.xlsx"), "Big Field", 49, name_big))
        # 2014_06_18
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_18.xlsx"), "Triangular Field", 11, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_18.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_18.xlsx"), "Big Field", 50, name_big))
        # 2014_06_27 (part 1)
        triangular_2014_06_27 = self._read_soil_moisture_sheet(get_path("2014_06_27.xlsx"), "Triangular Field", 11, name_triangular)
        # point 3 (at index 2) longitude is incorrect, see comments in the spreadsheet
        if triangular_2014_06_27.at[2, "longitude"] == 12.85467:
            triangular_2014_06_27.at[2, "longitude"] = 12.85407
        else:
            raise Exception("invalid correction attempted")
        all_dfs.append(triangular_2014_06_27)
        # 2014_06_27 (part 2)
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_27.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_06_27.xlsx"), "Big Bare Field", 49, name_big)) # sheet name is different here
        # 2014_07_03
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_07_03.xlsx"), "Triangular Field", 12, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_07_03.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_07_03.xlsx"), "Big Bare Field", 46, name_big)) # sheet name is different here
        # 2014_07_18
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_07_18.xlsx"), "Triangular Field", 12, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_07_18.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_07_18.xlsx"), "Big Bare Field", 50, name_big)) # sheet name is different here
        # 2014_07_24
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_07_24.xlsx"), "Triangular Field", 11, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_07_24.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_07_24.xlsx"), "Big Field", 52, name_big))
        # 2014_07_30
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_07_30(Only two Points).xlsx"), "Triangular Field", 2, name_triangular))
        # 2014_08_04
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_08_04.xlsx"), "Triangular Field", 11, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_08_04.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_08_04.xlsx"), "Big Field", 38, name_big))
        # 2014_08_21
        # two teams measured triangular field, two sheets available
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_08_21.xlsx"), "Triangular Field (1)", 6, name_triangular, point_id_offset=0))
        # time missing, one measurement incorrect in point 5 for mV, but vol.% is fine
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_08_21.xlsx"), "Triangular Field (2)", 5, name_triangular, point_id_offset=6))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_08_21.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_08_21.xlsx"), "Big Field", 52, name_big))
        # 2014_08_24
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_08_24.xlsx"), "Triangular Field", 11, name_triangular))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_08_24.xlsx"), "Meteorological Station", 10, name_meteo))
        all_dfs.append(self._read_soil_moisture_sheet(get_path("2014_08_24.xlsx"), "Big Field", 43, name_big))
        all_points = pd.concat(all_dfs, ignore_index=True)
        if band is not None and pass_name is not None:
            all_points = self._extend_df_coords(all_points, band, pass_name)
        return all_points
