

import pathlib
import datetime
import re
import numpy as np
import pandas as pd
import fsarcamp as fc
import fsarcamp.cropex14 as cr14

class CROPEX14Biomass:
    def __init__(self, data_folder, cropex14campaign: cr14.CROPEX14Campaign, debug_logs=False):
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
        self.debug_logs = debug_logs

    def _to_float(self, value):
        try:
            if isinstance(value, str):
                matches = re.match("^(\d+)-(\d+)$", value)
                if matches:
                    # string a range of values like "9-10" -> take the average
                    val1 = float(matches.group(1))
                    val2 = float(matches.group(2))
                    result = (val1 + val2) / 2
                    if self.debug_logs: print(f"interpreting '{value}' as ({val1} + {val2}) / 2 = {result}")
                    return result
                if re.match("^(\d+),(\d+)$", value):
                    # comma used as decimal separator
                    result = float(value.replace(",", "."))
                    if self.debug_logs: print(f"interpreting '{value}' as {result}")
                    return result
            return float(value)
        except:
            return np.nan
    
    def _extend_df_coords(self, df, band, pass_name):
        fsar_pass = self.cropex14campaign.get_pass(pass_name, band)
        lut = fsar_pass.load_gtc_sr2geo_lut()
        northing = df["northing"].to_numpy().copy()
        easting = df["easting"].to_numpy().copy()
        lut_northing = (northing - lut.min_north) / lut.pixel_spacing_north
        lut_easting = (easting - lut.min_east) / lut.pixel_spacing_east
        point_az, point_rg = fc.geocode_north_east_to_az_rg(northing, easting, lut)
        # extend data frame
        df_extended = df.assign(
            lut_northing=lut_northing,
            lut_easting=lut_easting,
            azimuth=point_az,
            range=point_rg,
        )
        return df_extended

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
    
    def _get_additional_data(self):
        # data extracted manually from comments in excel sheets
        # date_time, point_id, veg_height, bbch, data_src
        rows = [
            # Wallerfing_soil_moisture_2014_04_09
            (datetime.datetime(2014, 4, 9, 10, 10), "W10_Triangular", 20, np.nan, "Wallerfing_soil_moisture_2014_04_09.xlsx"),
            (datetime.datetime(2014, 4, 9, 8, 55), "C1_Meteo", 0, np.nan, "Wallerfing_soil_moisture_2014_04_09.xlsx"), # bare soil
            (datetime.datetime(2014, 4, 9, 10, 10), "C2_Big", 0, np.nan, "Wallerfing_soil_moisture_2014_04_09.xlsx"), # bare soil
            # Wallerfing_soil_moisture_2014_04_10
            (datetime.datetime(2014, 4, 10, 8, 40), "C1_Meteo", 0, np.nan, "Wallerfing_soil_moisture_2014_04_10.xlsx"), # bare soil
            (datetime.datetime(2014, 4, 10, 9, 10), "C2_Big", 0, np.nan, "Wallerfing_soil_moisture_2014_04_10.xlsx"), # bare soil
            # Wallerfing_soil_moisture_2014_04_11            
            (datetime.datetime(2014, 4, 11, 11, 0), "W10_Triangular", 20, np.nan, "Wallerfing_soil_moisture_2014_04_11.xlsx"),
            (datetime.datetime(2014, 4, 11, 8, 25), "C1_Meteo", 0, np.nan, "Wallerfing_soil_moisture_2014_04_11.xlsx"), # bare soil
            (datetime.datetime(2014, 4, 11, 8, 55), "C2_Big", 0, np.nan, "Wallerfing_soil_moisture_2014_04_11.xlsx"), # bare soil
            # Wallerfing_soil_moisture_2014_05_15
            (datetime.datetime(2014, 5, 15, 11, 45), "W10_Triangular", 50, np.nan, "Wallerfing_soil_moisture_2014_05_15.xlsx"),
            (datetime.datetime(2014, 5, 15, 10, 0), "C1_Meteo", 5, np.nan, "Wallerfing_soil_moisture_2014_05_15.xlsx"), # maize 5 cm
            (datetime.datetime(2014, 5, 15, 9, 30), "C2_Big", 10, np.nan, "Wallerfing_soil_moisture_2014_05_15.xlsx"), # maize 10 cm
            # Wallerfing_soil_moisture_2014_05_22
            #   wheat: height 50-60 cm, bbch 30 (begin of stem elongation)
            (datetime.datetime(2014, 5, 22, 8, 45), "W10_Triangular", 55, 30, "Wallerfing_soil_moisture_2014_05_22.xlsx"),
            #   maize C2: height 15 cm, bbch 13 (3-4 leaves)
            (datetime.datetime(2014, 5, 22, 9, 45), "C1_Meteo", 15, 13, "Wallerfing_soil_moisture_2014_05_22.xlsx"),
            #   maize C2: height 10 cm, bbch 13 (3-4 leaves)
            (datetime.datetime(2014, 5, 22, 10, 30), "C2_Big", 10, 13, "Wallerfing_soil_moisture_2014_05_22.xlsx"),
            # Wallerfing_soil_moisture_2014_06_04
            (datetime.datetime(2014, 6, 4, 9, 0), "W10_Triangular", 69, np.nan, "Wallerfing_soil_moisture_2014_06_04.xlsx"),
            #   maize C1: height 40 cm, height 29 cm near meteo station, bbch 16 (6 leaves)
            (datetime.datetime(2014, 6, 4, 10, 15), "C1_Meteo", 40, 16, "Wallerfing_soil_moisture_2014_06_04.xlsx"),
            (datetime.datetime(2014, 6, 4, 10, 15), "C1_Meteo_near_station", 29, 16, "Wallerfing_soil_moisture_2014_06_04.xlsx"),
            (datetime.datetime(2014, 6, 4, 11, 20), "C2_Big", 28, 16, "Wallerfing_soil_moisture_2014_06_04.xlsx"),
            # Wallerfing_soil_moisture_2014_06_12
            #   maize C1: height 85-95 cm, height 50-60 cm near meteo station
            (datetime.datetime(2014, 6, 12, 9, 20), "C1_Meteo", 90, np.nan, "Wallerfing_soil_moisture_2014_06_12.xlsx"),
            (datetime.datetime(2014, 6, 12, 9, 20), "C1_Meteo_near_station", 55, np.nan, "Wallerfing_soil_moisture_2014_06_12.xlsx"),
            (datetime.datetime(2014, 6, 12, 10, 40), "C2_Big", 63, np.nan, "Wallerfing_soil_moisture_2014_06_12.xlsx"),
            # Wallerfing_soil_moisture_2014_06_18
            #   maize C1: height 118-125 cm, height 90 cm near meteo station
            (datetime.datetime(2014, 6, 18, 9, 10), "C1_Meteo", 121.5, np.nan, "Wallerfing_soil_moisture_2014_06_18.xlsx"),
            (datetime.datetime(2014, 6, 18, 9, 10), "C1_Meteo_near_station", 90, np.nan, "Wallerfing_soil_moisture_2014_06_18.xlsx"),
            #   maize C2: height 90-105 cm
            (datetime.datetime(2014, 6, 18, 10, 0), "C2_Big", 97.5, np.nan, "Wallerfing_soil_moisture_2014_06_18.xlsx"),
            #   Big field, cucumber: 27-31 cm, sugar beet 36 cm
            # Wallerfing_soil_moisture_2014_06_27
            #   wheat: height 75-80 cm
            (datetime.datetime(2014, 6, 27, 17, 15), "W10_Triangular", 77.5, np.nan, "Wallerfing_soil_moisture_2014_06_27.xlsx"),
            #   maize C1: point #1: 155-160 cm, point #3: 120-125 cm, point #9: 130-135 cm
            (datetime.datetime(2014, 6, 27, 16, 30), "C1_Meteo_point_1", 157.5, np.nan, "Wallerfing_soil_moisture_2014_06_27.xlsx"),
            (datetime.datetime(2014, 6, 27, 16, 30), "C1_Meteo_point_3", 122.5, np.nan, "Wallerfing_soil_moisture_2014_06_27.xlsx"),
            (datetime.datetime(2014, 6, 27, 16, 30), "C1_Meteo_point_9", 132.5, np.nan, "Wallerfing_soil_moisture_2014_06_27.xlsx"),
            #   maize C2: height 120-125 cm
            (datetime.datetime(2014, 6, 27, 16, 20), "C2_Big", 122.5, np.nan, "Wallerfing_soil_moisture_2014_06_27.xlsx"),
            #   Big field, cucumber: height 20-25 cm, row spacing 70 cm
            # Wallerfing_soil_moisture_2014_07_03
            #   wheat: point #3: height 75-80 cm, point #12: height 85-90 cm (slightly different crop)
            (datetime.datetime(2014, 7, 3, 14, 30), "W10_Triangular_point_3", 77.5, np.nan, "Wallerfing_soil_moisture_2014_07_03.xlsx"),
            (datetime.datetime(2014, 7, 3, 14, 30), "W10_Triangular_point_12", 87.5, np.nan, "Wallerfing_soil_moisture_2014_07_03.xlsx"),
            #   maize C1: point #1: 210-215 cm, point #2: 185-195 cm, point #4: 145-150 cm, point # 8: 170-175 cm, point #10: 175-185 cm
            (datetime.datetime(2014, 7, 3, 8, 45), "C1_Meteo_point_1", 212.5, np.nan, "Wallerfing_soil_moisture_2014_07_03.xlsx"),
            (datetime.datetime(2014, 7, 3, 8, 45), "C1_Meteo_point_2", 190, np.nan, "Wallerfing_soil_moisture_2014_07_03.xlsx"),
            (datetime.datetime(2014, 7, 3, 8, 45), "C1_Meteo_point_4", 147.5, np.nan, "Wallerfing_soil_moisture_2014_07_03.xlsx"),
            (datetime.datetime(2014, 7, 3, 8, 45), "C1_Meteo_point_8", 172.5, np.nan, "Wallerfing_soil_moisture_2014_07_03.xlsx"),
            (datetime.datetime(2014, 7, 3, 8, 45), "C1_Meteo_point_10", 180, np.nan, "Wallerfing_soil_moisture_2014_07_03.xlsx"),
            #   maize C2: point #2: 120-125 cm, point #5: 180-190 cm, point #12: 125-135 cm 
            (datetime.datetime(2014, 7, 3, 10, 20), "C2_Big_point_2", 122.5, np.nan, "Wallerfing_soil_moisture_2014_07_03.xlsx"),
            (datetime.datetime(2014, 7, 3, 10, 20), "C2_Big_point_5", 185, np.nan, "Wallerfing_soil_moisture_2014_07_03.xlsx"),
            (datetime.datetime(2014, 7, 3, 10, 20), "C2_Big_point_12", 130, np.nan, "Wallerfing_soil_moisture_2014_07_03.xlsx"),
            #   Big field, cucumber: height 25 cm, row spacing 60 cm, spacing between 2 cucumber rows 150 cm (?)
            # Wallerfing_soil_moisture_2014_07_18
            #   wheat: height 70-80 cm, phenology 61-63
            (datetime.datetime(2014, 7, 18, 10, 30), "W10_Triangular", 75, 62, "Wallerfing_soil_moisture_2014_07_18.xlsx"),
            #   maize C1: height point #1: 320-340 cm, point #4: 280 cm, point #6 280 cm, point #8: 290-300 cm, point #10: 280cm
            (datetime.datetime(2014, 7, 18, 9, 0), "C1_Meteo_point_1", 330, np.nan, "Wallerfing_soil_moisture_2014_07_18.xlsx"),
            (datetime.datetime(2014, 7, 18, 9, 0), "C1_Meteo_point_4", 280, np.nan, "Wallerfing_soil_moisture_2014_07_18.xlsx"),
            (datetime.datetime(2014, 7, 18, 9, 0), "C1_Meteo_point_6", 280, np.nan, "Wallerfing_soil_moisture_2014_07_18.xlsx"),
            (datetime.datetime(2014, 7, 18, 9, 0), "C1_Meteo_point_8", 295, np.nan, "Wallerfing_soil_moisture_2014_07_18.xlsx"),
            (datetime.datetime(2014, 7, 18, 9, 0), "C1_Meteo_point_10", 280, np.nan, "Wallerfing_soil_moisture_2014_07_18.xlsx"),
            #   maize C2: height point #1: 260-270 cm, corn is in flowering stage
            (datetime.datetime(2014, 7, 18, 8, 45), "C2_Big_point_1", 265, np.nan, "Wallerfing_soil_moisture_2014_07_18.xlsx"),
            #   Big field, cucumber: height 25-30 cm, potato: 55-60 cm, sugar beet: 60-65 cm
            # Wallerfing_soil_moisture_2014_07_24
            #   maize C1: height point #3: 288 cm, point #4: 320 cm, point #6: 320 cm, point #10: 300 cm
            (datetime.datetime(2014, 7, 24, 0, 0), "C1_Meteo_point_3", 288, np.nan, "Wallerfing_soil_moisture_2014_07_24.xlsx"),
            (datetime.datetime(2014, 7, 24, 0, 0), "C1_Meteo_point_4", 320, np.nan, "Wallerfing_soil_moisture_2014_07_24.xlsx"),
            (datetime.datetime(2014, 7, 24, 0, 0), "C1_Meteo_point_6", 320, np.nan, "Wallerfing_soil_moisture_2014_07_24.xlsx"),
            (datetime.datetime(2014, 7, 24, 0, 0), "C1_Meteo_point_10", 300, np.nan, "Wallerfing_soil_moisture_2014_07_24.xlsx"),
            #   maize C2: height point #1: 280 cm, point #6: 337 cm, point #15: 312 cm, point #47: 317 cm
            (datetime.datetime(2014, 7, 24, 9, 0), "C2_Big_point_1", 280, np.nan, "Wallerfing_soil_moisture_2014_07_24.xlsx"),
            (datetime.datetime(2014, 7, 24, 9, 0), "C2_Big_point_6", 337, np.nan, "Wallerfing_soil_moisture_2014_07_24.xlsx"),
            (datetime.datetime(2014, 7, 24, 9, 0), "C2_Big_point_15", 312, np.nan, "Wallerfing_soil_moisture_2014_07_24.xlsx"),
            (datetime.datetime(2014, 7, 24, 9, 0), "C2_Big_point_47", 317, np.nan, "Wallerfing_soil_moisture_2014_07_24.xlsx"),
            # Wallerfing_soil_moisture_2014_08_04
            #   maize C1: height 290 cm, another measurement 330-340 cm
            (datetime.datetime(2014, 8, 4, 11, 30), "C1_Meteo_a", 290, np.nan, "Wallerfing_soil_moisture_2014_08_04.xlsx"),
            (datetime.datetime(2014, 8, 4, 11, 30), "C1_Meteo_b", 335, np.nan, "Wallerfing_soil_moisture_2014_08_04.xlsx"),
            #   maize C2: height point #6: 320 cm
            (datetime.datetime(2014, 8, 4, 12, 37), "C2_Big_point_6", 320, np.nan, "Wallerfing_soil_moisture_2014_08_04.xlsx"),
            #   Big field, cucumber: height 20-30 cm, sugar beet: 50-60 cm
            # Wallerfing_soil_moisture_2014_08_21
            #   maize C1: height point #1: 338 cm, point #7: 302 cm
            (datetime.datetime(2014, 8, 21, 12, 20), "C1_Meteo_point_1", 338, np.nan, "Wallerfing_soil_moisture_2014_08_21.xlsx"),
            (datetime.datetime(2014, 8, 21, 12, 20), "C1_Meteo_point_7", 302, np.nan, "Wallerfing_soil_moisture_2014_08_21.xlsx"),
            #   maize C2: height point #1: 275-293 cm, point #7: 342 cm, point #14: 334 cm
            (datetime.datetime(2014, 8, 21, 9, 40), "C2_Big_point_1", 284, np.nan, "Wallerfing_soil_moisture_2014_08_21.xlsx"),
            (datetime.datetime(2014, 8, 21, 9, 40), "C2_Big_point_7", 342, np.nan, "Wallerfing_soil_moisture_2014_08_21.xlsx"),
            (datetime.datetime(2014, 8, 21, 9, 40), "C2_Big_point_14", 334, np.nan, "Wallerfing_soil_moisture_2014_08_21.xlsx"),
            #   Big field, cucumber: as last time, sugar beet: 50-55 cm
            # Wallerfing_soil_moisture_2014_08_24
            #   maize C1: height point #2: 325 cm
            (datetime.datetime(2014, 8, 24, 9, 15), "C1_Meteo_point_2", 325, np.nan, "Wallerfing_soil_moisture_2014_08_24.xlsx"),
            #   maize C2: height point #2: 315-320 cm, row spacing 18x76 (?)
            (datetime.datetime(2014, 8, 24, 10, 30), "C2_Big_point_2", 317.5, np.nan, "Wallerfing_soil_moisture_2014_08_24.xlsx"),
            #   Big field, cucumber: 15-25 (plants do not look fresh anymore), sugar beet: 50-55 cm
        ]
        # Note: latitude-longitude coordinates could be obtained for some points (where point numbers are defined)
        return pd.DataFrame(rows, columns=["date_time", "point_id", "veg_height", "bbch", "data_src"])

    def load_biomass_points(self, band=None, pass_name=None):
        """
        Load point biomass measurements.
        
        If band and pass_name are provided, the point coordinates (northing, easting) will be
        additionally geocoded to the RGI azimuth and range coordinates using the F-SAR GTC-LUT files.
        Note that no filtering is applied and all points are geocoded, even if they do not belong
        to the date of the specified F-SAR pass.
        
        Arguments:
            band: band ("X", "C", or "L"), optional
            pass_name: pass name, optional

        Returns:
            Pandas dataframe with following columns:
                "date_time" - date and time of the measurement, time is missing for some points and set to 0:00
                "point_id" - point ID, typically indicates field or crop type
                "longitude", "latitude" - geographical coordinates
                "northing", "easting" - geographical coordinates in the LUT coordinate system (UTM zone 33)
                "veg_height" - vegetation height in cm
                "row_orientation" - plant row orientation in degrees
                "row_spacing" - spacing between the plant rows in cm
                "plants_per_meter" - number of plants per meter (along a row)
                "bbch" - BBCH value, defines the plant development stage
                "weight_025m2", "weight_100m2" - biomass weight per 0.25 m^2 or per 1 m^2 (usually one of the values is provided)
                "weight_bag" - weight of the bag (in g) to store the biomass samples
                "sample1_wet", "sample2_wet" - weight of the fresh wet sample including the bag, in g
                "sample1_dry", "sample2_dry" - weight of the sample + bag after drying, in g
                "sample1_vwc_with_bag", "sample2_vwc_with_bag" - gravimetric moisture content, but includes the bag weight, not just the plant
                "sample1_vwc", "sample2_vwc" - gravimetric moisture content, bag weight removed
                "soil_moisture" - average volumetric soil moisture from several samples at that position, value ranges from 0 to 1
                "soil_moisture_1", ..., "soil_moisture_6" - individual volumetric soil moisture measurements at that position
                "data_src" - indicates the data source (e.g. name of the excel file)
            If band and pass_name are provided, additionals columns are added:
                "lut_northing", "lut_easting" - pixel coordinates within the LUT
                "azimuth", "range" - pixel coordinates within the SLC
        """
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
            self._get_additional_data(),
        ]
        combined_df = pd.concat(all_dfs, ignore_index=True)
        if band is not None and pass_name is not None:
            combined_df = self._extend_df_coords(combined_df, band, pass_name)
        return combined_df

if __name__ == "__main__":
    campaign = cr14.CROPEX14Campaign(fc.get_polinsar_folder() / "01_projects/CROPEX/CROPEX14")
    biomass_folder = fc.get_polinsar_folder() / "Ground_truth/Wallerfing_campaign_May_August_2014/Data/ground_measurements/biomass"
    biomass = CROPEX14Biomass(biomass_folder, campaign)
    df = biomass.load_biomass_points(band="L", pass_name="14cropex1114")

    barley = df[df["point_id"].str.startswith("C")]
    barley = barley.drop([
        "northing", "easting",
        "row_orientation", "row_spacing", "plants_per_meter",
        "weight_025m2", "weight_100m2", "weight_bag",
        "sample1_wet", "sample1_dry", "sample1_vwc_with_bag",
        "sample2_wet", "sample2_dry", "sample2_vwc_with_bag",
        "soil_moisture_1", "soil_moisture_2", "soil_moisture_3",
        "soil_moisture_4", "soil_moisture_5", "soil_moisture_6", "data_src",
        "lut_northing", "lut_easting", "azimuth", "range"
    ], axis=1)
    barley.to_csv("visualization/cropex_biomass_corn.csv", index=False)

    ## TODO: compare values with manual sheets from sarctd, add more values manually if needed
