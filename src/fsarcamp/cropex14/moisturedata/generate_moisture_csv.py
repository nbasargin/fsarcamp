"""
This script generates a CSV file with soil moisture data for the CROPEX 2014 F-SAR campaign.
The original data is available from the DLR ground measurement campaign.
A few additional soil moisture measurements are available in the biomass measurements, not included here.
"""
import datetime
import numpy as np
import pandas as pd
import pyproj
import fsarcamp as fc

# field names
name_triangular = "Triangular"
name_meteo = "Meteo"
name_big = "Big" # can further be subdivided into BigCorn, BugCucumbers, BugSugarBeet

def _to_float(value):
    try:
        return float(value)
    except:
        return np.nan
    
def _get_lat_long_to_lut_transformer():
    lut_proj = pyproj.Proj("epsg:32633") # UTM zone 33
    proj_latlong = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
    latlong_to_lut = pyproj.Transformer.from_proj(proj_latlong, lut_proj)
    return latlong_to_lut

def read_soil_moisture_sheet(file_path, sheet_name, num_rows, field_name, point_id_offset=0):
    """
    Read one sheet of the excel file with ground measurements.
    The excel files have a rather complicated formatting and suspicious values in some cases.
    """
    latlong_to_lut = _get_lat_long_to_lut_transformer()
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
        latitude = _to_float(df.iat[row, 2])
        longitude = _to_float(df.iat[row, 3])
        if np.isnan(latitude) or np.isnan(longitude):
            continue
        easting, northing = latlong_to_lut.transform(longitude, latitude)
        # read soil moisture (vol.%), other values in the sheet are not used here
        soil_moisture_vals = []
        for idx in range(4, 10):
            value = _to_float(df.iat[row, idx]) / 100
            soil_moisture_vals.append(value)
        if np.all(np.isnan(soil_moisture_vals)):
            continue
        soil_moisture = np.nanmean(soil_moisture_vals)
        df_rows.append((
            date_time, point_id, field_name, latitude, longitude, easting, northing,
            soil_moisture, *soil_moisture_vals,
        ))
    return pd.DataFrame(df_rows, columns=[
        "date_time", "point_id", "field", "latitude", "longitude", "easting", "northing", "soil_moisture", 
        "soil_moisture_1", "soil_moisture_2", "soil_moisture_3", "soil_moisture_4", "soil_moisture_5", "soil_moisture_6",
    ])       

def read_all():
    folder = fc.get_polinsar_folder() / "Ground_truth/Wallerfing_campaign_May_August_2014/Data/ground_measurements/soil_moisture"
    get_path = lambda suffix: folder / f"Wallerfing_soil_moisture_{suffix}"
    all_dfs = []
    # 2014_04_09
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_04_09.xlsx"), "Triangular Field", 11, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_04_09.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_04_09.xlsx"), "Big Field", 62, name_big))
    # 2014_04_10
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_04_10.xlsx"), "Triangular Field", 11, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_04_10.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_04_10.xlsx"), "Big Field", 47, name_big))
    # 2014_04_11
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_04_11.xlsx"), "Triangular Field", 11, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_04_11.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_04_11.xlsx"), "Big Field", 42, name_big))
    # 2014_05_15
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_05_15.xlsx"), "Triangular Field", 9, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_05_15.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_05_15.xlsx"), "Big Field", 51, name_big)) # one point is missing, can be obtained from cucumbers sheet
    # 2014_05_22
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_05_22.xlsx"), "Triangular Field", 11, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_05_22.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_05_22.xlsx"), "Big Field", 54, name_big))
    # 2014_06_04
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_04.xlsx"), "Triangular Field", 11, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_04.xlsx"), "Meteorological Station", 12, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_04.xlsx"), "Big Field", 46, name_big))
    # 2014_06_12
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_12.xlsx"), "Triangular Field", 8, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_12.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_12.xlsx"), "Big Field", 49, name_big))
    # 2014_06_18
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_18.xlsx"), "Triangular Field", 11, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_18.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_18.xlsx"), "Big Field", 50, name_big))
    # 2014_06_27 (part 1)
    triangular_2014_06_27 = read_soil_moisture_sheet(get_path("2014_06_27.xlsx"), "Triangular Field", 11, name_triangular)
    # point 3 (at index 2) longitude is incorrect, see comments in the spreadsheet
    if triangular_2014_06_27.at[2, "longitude"] == 12.85467:
        correct_long = 12.85407
        lat = triangular_2014_06_27["latitude"][2]
        easting, northing = _get_lat_long_to_lut_transformer().transform(correct_long, lat)
        triangular_2014_06_27.at[2, "longitude"] = 12.85407
        triangular_2014_06_27.at[2, "easting"] = easting
        triangular_2014_06_27.at[2, "northing"] = northing
    else:
        raise Exception("invalid correction attempted")
    all_dfs.append(triangular_2014_06_27)
    # 2014_06_27 (part 2)
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_27.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_06_27.xlsx"), "Big Bare Field", 49, name_big)) # sheet name is different here
    # 2014_07_03
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_07_03.xlsx"), "Triangular Field", 12, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_07_03.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_07_03.xlsx"), "Big Bare Field", 46, name_big)) # sheet name is different here
    # 2014_07_18
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_07_18.xlsx"), "Triangular Field", 12, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_07_18.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_07_18.xlsx"), "Big Bare Field", 50, name_big)) # sheet name is different here
    # 2014_07_24
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_07_24.xlsx"), "Triangular Field", 11, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_07_24.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_07_24.xlsx"), "Big Field", 52, name_big))
    # 2014_07_30
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_07_30(Only two Points).xlsx"), "Triangular Field", 2, name_triangular))
    # 2014_08_04
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_08_04.xlsx"), "Triangular Field", 11, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_08_04.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_08_04.xlsx"), "Big Field", 38, name_big))
    # 2014_08_21
    # two teams measured triangular field, two sheets available
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_08_21.xlsx"), "Triangular Field (1)", 6, name_triangular, point_id_offset=0))
    # time missing, one measurement incorrect in point 5 for mV, but vol.% is fine
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_08_21.xlsx"), "Triangular Field (2)", 5, name_triangular, point_id_offset=6))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_08_21.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_08_21.xlsx"), "Big Field", 52, name_big))
    # 2014_08_24
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_08_24.xlsx"), "Triangular Field", 11, name_triangular))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_08_24.xlsx"), "Meteorological Station", 10, name_meteo))
    all_dfs.append(read_soil_moisture_sheet(get_path("2014_08_24.xlsx"), "Big Field", 43, name_big))
    return pd.concat(all_dfs, ignore_index=True)

if __name__ == "__main__":    
    all_points = read_all()
    all_points.to_csv("visualization/cropex14_soil_moisture_v1.csv", index=False)
