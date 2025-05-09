import pathlib
import datetime
import re
import numpy as np
import pandas as pd
import pyproj


class CROPEX14Biomass:
    def __init__(self, data_folder):
        """
        Data loader for biomass ground measurements for the CROPEX 2014 campaign.
        `data_folder` defines the data folder that contains the XLSX files with biomass measurements.
        The path on the DLR-HR server as of November 2024:
        "/data/HR_Data/Pol-InSAR_InfoRetrieval/Ground_truth/Wallerfing_campaign_May_August_2014/Data/ground_measurements/biomass"
        """
        self.data_folder = pathlib.Path(data_folder)

    def _to_float(self, value):
        try:
            if isinstance(value, str):
                matches = re.match("^(\d+)-(\d+)$", value)
                if matches:
                    # string a range of values like "9-10" -> take the average
                    val1 = float(matches.group(1))
                    val2 = float(matches.group(2))
                    result = (val1 + val2) / 2
                    return result
                if re.match("^(\d+),(\d+)$", value):
                    # comma used as decimal separator
                    result = float(value.replace(",", "."))
                    return result
            return float(value)
        except Exception:
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
                continue  # data sheet 2014-07-30 has a comment that increases number of columns
            time = df.iat[3, col]
            if not isinstance(time, datetime.time):
                time = datetime.time(0, 0, 0)  # do not accept "----" strings
            date_time = datetime.datetime.combine(sheet_date, time)
            # collect df rows
            easting = self._to_float(df.iat[12, col])
            northing = self._to_float(df.iat[13, col])
            latitude = self._to_float(df.iat[8, col])
            longitude = self._to_float(df.iat[9, col])
            # vegetation parameters
            veg_height = self._to_float(df.iat[25, col])  # cm
            row_orientation = self._to_float(df.iat[28, col])  # degrees
            row_spacing = self._to_float(df.iat[29, col])  # cm
            plants_per_meter = self._to_float(df.iat[30, col])
            bbch = self._to_float(df.iat[31, col])
            if df.iat[31, col] == "last stage":
                bbch = 91  # full ripe, ready for harvest
            weight_025m2 = self._to_float(df.iat[34, col])  # g (per 0.25 m^2)
            weight_100m2 = self._to_float(df.iat[35, col])  # g (per 1 m^2)
            weight_bag = self._to_float(df.iat[36, col])  # g
            # sample 1
            sample1_wet = self._to_float(df.iat[37, col])  # g
            sample1_dry = self._to_float(df.iat[38, col])  # g
            sample1_vwc_with_bag = self._to_float(df.iat[39, col]) / 100  # includes sample bag weight
            sample1_vwc = self._to_float(df.iat[40, col]) / 100
            # sample 2
            sample2_wet = self._to_float(df.iat[41, col])  # g
            sample2_dry = self._to_float(df.iat[42, col])  # g
            sample2_vwc_with_bag = self._to_float(df.iat[43, col]) / 100  # includes sample bag weight
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
            df_rows.append(
                (
                    date_time,
                    point_id,
                    longitude,
                    latitude,
                    northing,
                    easting,
                    veg_height,
                    row_orientation,
                    row_spacing,
                    plants_per_meter,
                    bbch,
                    weight_025m2,
                    weight_100m2,
                    weight_bag,
                    sample1_wet,
                    sample1_dry,
                    sample1_vwc_with_bag,
                    sample1_vwc,
                    sample2_wet,
                    sample2_dry,
                    sample2_vwc_with_bag,
                    sample2_vwc,
                    soil_moisture,
                    *soil_moisture_vals,
                    data_src,
                )
            )
        return pd.DataFrame(
            df_rows,
            columns=[
                "date_time",
                "point_id",
                "longitude",
                "latitude",
                "northing",
                "easting",
                "veg_height",
                "row_orientation",
                "row_spacing",
                "plants_per_meter",
                "bbch",
                "weight_025m2",
                "weight_100m2",
                "weight_bag",
                "sample1_wet",
                "sample1_dry",
                "sample1_vwc_with_bag",
                "sample1_vwc",
                "sample2_wet",
                "sample2_dry",
                "sample2_vwc_with_bag",
                "sample2_vwc",
                "soil_moisture",
                "soil_moisture_1",
                "soil_moisture_2",
                "soil_moisture_3",
                "soil_moisture_4",
                "soil_moisture_5",
                "soil_moisture_6",
                "data_src",
            ],
        )

    def _get_additional_data(self):
        # data extracted manually from comments in excel sheets
        # date_time, point_id, longitude, latitude, veg_height, bbch, data_src
        rows = [
            # Wallerfing_soil_moisture_2014_04_09
            (
                datetime.datetime(2014, 4, 9, 10, 10),
                "W10_Triangular",
                np.nan,
                np.nan,
                20,
                np.nan,
                "Wallerfing_soil_moisture_2014_04_09.xlsx",
            ),
            (
                datetime.datetime(2014, 4, 9, 8, 55),
                "C1_Meteo",
                np.nan,
                np.nan,
                0,
                np.nan,
                "Wallerfing_soil_moisture_2014_04_09.xlsx",
            ),  # bare soil
            (
                datetime.datetime(2014, 4, 9, 10, 10),
                "C2_Big",
                np.nan,
                np.nan,
                0,
                np.nan,
                "Wallerfing_soil_moisture_2014_04_09.xlsx",
            ),  # bare soil
            # Wallerfing_soil_moisture_2014_04_10
            (
                datetime.datetime(2014, 4, 10, 8, 40),
                "C1_Meteo",
                np.nan,
                np.nan,
                0,
                np.nan,
                "Wallerfing_soil_moisture_2014_04_10.xlsx",
            ),  # bare soil
            (
                datetime.datetime(2014, 4, 10, 9, 10),
                "C2_Big",
                np.nan,
                np.nan,
                0,
                np.nan,
                "Wallerfing_soil_moisture_2014_04_10.xlsx",
            ),  # bare soil
            # Wallerfing_soil_moisture_2014_04_11
            (
                datetime.datetime(2014, 4, 11, 11, 0),
                "W10_Triangular",
                np.nan,
                np.nan,
                20,
                np.nan,
                "Wallerfing_soil_moisture_2014_04_11.xlsx",
            ),
            (
                datetime.datetime(2014, 4, 11, 8, 25),
                "C1_Meteo",
                np.nan,
                np.nan,
                0,
                np.nan,
                "Wallerfing_soil_moisture_2014_04_11.xlsx",
            ),  # bare soil
            (
                datetime.datetime(2014, 4, 11, 8, 55),
                "C2_Big",
                np.nan,
                np.nan,
                0,
                np.nan,
                "Wallerfing_soil_moisture_2014_04_11.xlsx",
            ),  # bare soil
            # Wallerfing_soil_moisture_2014_05_15
            (
                datetime.datetime(2014, 5, 15, 11, 45),
                "W10_Triangular",
                np.nan,
                np.nan,
                50,
                np.nan,
                "Wallerfing_soil_moisture_2014_05_15.xlsx",
            ),
            (
                datetime.datetime(2014, 5, 15, 10, 0),
                "C1_Meteo",
                np.nan,
                np.nan,
                5,
                np.nan,
                "Wallerfing_soil_moisture_2014_05_15.xlsx",
            ),  # maize 5 cm
            (
                datetime.datetime(2014, 5, 15, 9, 30),
                "C2_Big",
                np.nan,
                np.nan,
                10,
                np.nan,
                "Wallerfing_soil_moisture_2014_05_15.xlsx",
            ),  # maize 10 cm
            # Wallerfing_soil_moisture_2014_05_22
            #   wheat: height 50-60 cm, bbch 30 (begin of stem elongation)
            (
                datetime.datetime(2014, 5, 22, 8, 45),
                "W10_Triangular",
                np.nan,
                np.nan,
                55,
                30,
                "Wallerfing_soil_moisture_2014_05_22.xlsx",
            ),
            #   maize C2: height 15 cm, bbch 13 (3-4 leaves)
            (
                datetime.datetime(2014, 5, 22, 9, 45),
                "C1_Meteo",
                np.nan,
                np.nan,
                15,
                13,
                "Wallerfing_soil_moisture_2014_05_22.xlsx",
            ),
            #   maize C2: height 10 cm, bbch 13 (3-4 leaves)
            (
                datetime.datetime(2014, 5, 22, 10, 30),
                "C2_Big",
                np.nan,
                np.nan,
                10,
                13,
                "Wallerfing_soil_moisture_2014_05_22.xlsx",
            ),
            # Wallerfing_soil_moisture_2014_06_04
            (
                datetime.datetime(2014, 6, 4, 9, 0),
                "W10_Triangular",
                np.nan,
                np.nan,
                69,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_04.xlsx",
            ),
            #   maize C1: height 40 cm, height 29 cm near meteo station, bbch 16 (6 leaves)
            (
                datetime.datetime(2014, 6, 4, 10, 15),
                "C1_Meteo",
                np.nan,
                np.nan,
                40,
                16,
                "Wallerfing_soil_moisture_2014_06_04.xlsx",
            ),
            (
                datetime.datetime(2014, 6, 4, 10, 15),
                "C1_Meteo_near_station",
                np.nan,
                np.nan,
                29,
                16,
                "Wallerfing_soil_moisture_2014_06_04.xlsx",
            ),
            (
                datetime.datetime(2014, 6, 4, 11, 20),
                "C2_Big",
                np.nan,
                np.nan,
                28,
                16,
                "Wallerfing_soil_moisture_2014_06_04.xlsx",
            ),
            # Wallerfing_soil_moisture_2014_06_12
            #   maize C1: height 85-95 cm, height 50-60 cm near meteo station
            (
                datetime.datetime(2014, 6, 12, 9, 20),
                "C1_Meteo",
                np.nan,
                np.nan,
                90,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_12.xlsx",
            ),
            (
                datetime.datetime(2014, 6, 12, 9, 20),
                "C1_Meteo_near_station",
                np.nan,
                np.nan,
                55,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_12.xlsx",
            ),
            (
                datetime.datetime(2014, 6, 12, 10, 40),
                "C2_Big",
                np.nan,
                np.nan,
                63,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_12.xlsx",
            ),
            # Wallerfing_soil_moisture_2014_06_18
            #   maize C1: height 118-125 cm, height 90 cm near meteo station
            (
                datetime.datetime(2014, 6, 18, 9, 10),
                "C1_Meteo",
                np.nan,
                np.nan,
                121.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_18.xlsx",
            ),
            (
                datetime.datetime(2014, 6, 18, 9, 10),
                "C1_Meteo_near_station",
                np.nan,
                np.nan,
                90,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_18.xlsx",
            ),
            #   maize C2: height 90-105 cm
            (
                datetime.datetime(2014, 6, 18, 10, 0),
                "C2_Big",
                np.nan,
                np.nan,
                97.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_18.xlsx",
            ),
            #   Big field, cucumber: 27-31 cm, sugar beet 36 cm
            # Wallerfing_soil_moisture_2014_06_27
            #   wheat: height 75-80 cm
            (
                datetime.datetime(2014, 6, 27, 17, 15),
                "W10_Triangular",
                np.nan,
                np.nan,
                77.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_27.xlsx",
            ),
            #   maize C1: point #1: 155-160 cm, point #3: 120-125 cm, point #9: 130-135 cm
            (
                datetime.datetime(2014, 6, 27, 16, 30),
                "C1_Meteo_point_1",
                12.87521,
                48.69478,
                157.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_27.xlsx",
            ),
            (
                datetime.datetime(2014, 6, 27, 16, 30),
                "C1_Meteo_point_3",
                12.87415,
                48.69449,
                122.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_27.xlsx",
            ),
            (
                datetime.datetime(2014, 6, 27, 16, 30),
                "C1_Meteo_point_9",
                12.87502,
                48.69415,
                132.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_27.xlsx",
            ),
            #   maize C2: height 120-125 cm
            (
                datetime.datetime(2014, 6, 27, 16, 20),
                "C2_Big",
                np.nan,
                np.nan,
                122.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_06_27.xlsx",
            ),
            #   Big field, cucumber: height 20-25 cm, row spacing 70 cm
            # Wallerfing_soil_moisture_2014_07_03
            #   wheat: point #3: height 75-80 cm, point #12: height 85-90 cm (slightly different crop)
            (
                datetime.datetime(2014, 7, 3, 14, 30),
                "W10_Triangular_point_3",
                12.85405,
                48.69044,
                77.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_03.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 3, 14, 30),
                "W10_Triangular_point_12",
                12.85452,
                48.68953,
                87.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_03.xlsx",
            ),
            #   maize C1: point #1: 210-215 cm, point #2: 185-195 cm, point #4: 145-150 cm, point # 8: 170-175 cm, point #10: 175-185 cm
            (
                datetime.datetime(2014, 7, 3, 8, 45),
                "C1_Meteo_point_1",
                12.87523,
                48.69476,
                212.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_03.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 3, 8, 45),
                "C1_Meteo_point_2",
                12.87476,
                48.69460,
                190,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_03.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 3, 8, 45),
                "C1_Meteo_point_4",
                12.87382,
                48.69438,
                147.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_03.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 3, 8, 45),
                "C1_Meteo_point_8",
                12.87452,
                48.69402,
                172.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_03.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 3, 8, 45),
                "C1_Meteo_point_10",
                12.87549,
                48.69429,
                180,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_03.xlsx",
            ),
            #   maize C2: point #2: 120-125 cm, point #5: 180-190 cm, point #12: 125-135 cm
            (
                datetime.datetime(2014, 7, 3, 10, 20),
                "C2_Big_point_2",
                12.87456,
                48.69619,
                122.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_03.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 3, 10, 20),
                "C2_Big_point_5",
                12.87308,
                48.69587,
                185,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_03.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 3, 10, 20),
                "C2_Big_point_12",
                12.87267,
                48.69652,
                130,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_03.xlsx",
            ),
            #   Big field, cucumber: height 25 cm, row spacing 60 cm, spacing between 2 cucumber rows 150 cm (?)
            # Wallerfing_soil_moisture_2014_07_18
            #   wheat: height 70-80 cm, phenology 61-63
            (
                datetime.datetime(2014, 7, 18, 10, 30),
                "W10_Triangular",
                np.nan,
                np.nan,
                75,
                62,
                "Wallerfing_soil_moisture_2014_07_18.xlsx",
            ),
            #   maize C1: height point #1: 320-340 cm, point #4: 280 cm, point #6 280 cm, point #8: 290-300 cm, point #10: 280cm
            (
                datetime.datetime(2014, 7, 18, 9, 0),
                "C1_Meteo_point_1",
                12.87525,
                48.69473,
                330,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_18.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 18, 9, 0),
                "C1_Meteo_point_4",
                12.87368,
                48.69439,
                280,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_18.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 18, 9, 0),
                "C1_Meteo_point_6",
                12.87351,
                48.69381,
                280,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_18.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 18, 9, 0),
                "C1_Meteo_point_8",
                12.87453,
                48.69403,
                295,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_18.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 18, 9, 0),
                "C1_Meteo_point_10",
                12.87552,
                48.69429,
                280,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_18.xlsx",
            ),
            #   maize C2: height point #1: 260-270 cm, corn is in flowering stage
            (
                datetime.datetime(2014, 7, 18, 8, 45),
                "C2_Big_point_1",
                12.87493,
                48.69627,
                265,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_18.xlsx",
            ),
            #   Big field, cucumber: height 25-30 cm, potato: 55-60 cm, sugar beet: 60-65 cm
            # Wallerfing_soil_moisture_2014_07_24
            #   maize C1: height point #3: 288 cm, point #4: 320 cm, point #6: 320 cm, point #10: 300 cm
            (
                datetime.datetime(2014, 7, 24, 0, 0),
                "C1_Meteo_point_3",
                12.87509,
                48.69416,
                288,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_24.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 24, 0, 0),
                "C1_Meteo_point_4",
                12.87471,
                48.69458,
                320,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_24.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 24, 0, 0),
                "C1_Meteo_point_6",
                12.87459,
                48.69404,
                320,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_24.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 24, 0, 0),
                "C1_Meteo_point_10",
                12.87349,
                48.69385,
                300,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_24.xlsx",
            ),
            #   maize C2: height point #1: 280 cm, point #6: 337 cm, point #15: 312 cm, point #47: 317 cm
            (
                datetime.datetime(2014, 7, 24, 9, 0),
                "C2_Big_point_1",
                12.87494,
                48.69625,
                280,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_24.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 24, 9, 0),
                "C2_Big_point_6",
                12.87247,
                48.69576,
                337,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_24.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 24, 9, 0),
                "C2_Big_point_15",
                12.87211,
                48.69645,
                312,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_24.xlsx",
            ),
            (
                datetime.datetime(2014, 7, 24, 9, 0),
                "C2_Big_point_47",
                12.87171,
                48.69511,
                317,
                np.nan,
                "Wallerfing_soil_moisture_2014_07_24.xlsx",
            ),
            # Wallerfing_soil_moisture_2014_08_04
            #   maize C1: height 290 cm, another measurement 330-340 cm
            (
                datetime.datetime(2014, 8, 4, 11, 30),
                "C1_Meteo_a",
                np.nan,
                np.nan,
                290,
                np.nan,
                "Wallerfing_soil_moisture_2014_08_04.xlsx",
            ),
            (
                datetime.datetime(2014, 8, 4, 11, 30),
                "C1_Meteo_b",
                np.nan,
                np.nan,
                335,
                np.nan,
                "Wallerfing_soil_moisture_2014_08_04.xlsx",
            ),
            #   maize C2: height point #6: 320 cm
            (
                datetime.datetime(2014, 8, 4, 12, 37),
                "C2_Big_point_6",
                12.87200,
                48.69564,
                320,
                np.nan,
                "Wallerfing_soil_moisture_2014_08_04.xlsx",
            ),
            #   Big field, cucumber: height 20-30 cm, sugar beet: 50-60 cm
            # Wallerfing_soil_moisture_2014_08_21
            #   maize C1: height point #1: 338 cm, point #7: 302 cm
            (
                datetime.datetime(2014, 8, 21, 12, 20),
                "C1_Meteo_point_1",
                12.87527,
                48.69476,
                338,
                np.nan,
                "Wallerfing_soil_moisture_2014_08_21.xlsx",
            ),
            (
                datetime.datetime(2014, 8, 21, 12, 20),
                "C1_Meteo_point_7",
                12.87406,
                48.69393,
                302,
                np.nan,
                "Wallerfing_soil_moisture_2014_08_21.xlsx",
            ),
            #   maize C2: height point #1: 275-293 cm, point #7: 342 cm, point #14: 334 cm
            (
                datetime.datetime(2014, 8, 21, 9, 40),
                "C2_Big_point_1",
                12.87499,
                48.69625,
                284,
                np.nan,
                "Wallerfing_soil_moisture_2014_08_21.xlsx",
            ),
            (
                datetime.datetime(2014, 8, 21, 9, 40),
                "C2_Big_point_7",
                12.87200,
                48.69569,
                342,
                np.nan,
                "Wallerfing_soil_moisture_2014_08_21.xlsx",
            ),
            (
                datetime.datetime(2014, 8, 21, 9, 40),
                "C2_Big_point_14",
                12.87162,
                48.69632,
                334,
                np.nan,
                "Wallerfing_soil_moisture_2014_08_21.xlsx",
            ),
            #   Big field, cucumber: as last time, sugar beet: 50-55 cm
            # Wallerfing_soil_moisture_2014_08_24
            #   maize C1: height point #2: 325 cm
            (
                datetime.datetime(2014, 8, 24, 9, 15),
                "C1_Meteo_point_2",
                12.87475,
                48.69457,
                325,
                np.nan,
                "Wallerfing_soil_moisture_2014_08_24.xlsx",
            ),
            #   maize C2: height point #2: 315-320 cm, row spacing 18x76 (?)
            (
                datetime.datetime(2014, 8, 24, 10, 30),
                "C2_Big_point_2",
                12.87406,
                48.69605,
                317.5,
                np.nan,
                "Wallerfing_soil_moisture_2014_08_24.xlsx",
            ),
            #   Big field, cucumber: 15-25 (plants do not look fresh anymore), sugar beet: 50-55 cm
        ]
        df = pd.DataFrame(
            rows, columns=["date_time", "point_id", "longitude", "latitude", "veg_height", "bbch", "data_src"]
        )
        # extend with northing easting coords
        latitude = df["latitude"].to_numpy()
        longitude = df["longitude"].to_numpy()
        invalid_coords = np.isnan(latitude) | np.isnan(longitude)
        proj_latlong = pyproj.Proj(proj="latlong", ellps="WGS84", datum="WGS84")
        proj_lut = pyproj.Proj("epsg:32633")  # UTM zone 33
        latlong_to_lut = pyproj.Transformer.from_proj(proj_latlong, proj_lut)
        easting, northing = latlong_to_lut.transform(longitude, latitude)
        easting[invalid_coords] = np.nan
        northing[invalid_coords] = np.nan
        df = df.assign(
            northing=northing,
            easting=easting,
        )
        return df

    def load_biomass_points(self):
        """
        Load point biomass measurements.
        Additional data points were manually added from the comments in soil moisture excel sheets.

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
        return combined_df
