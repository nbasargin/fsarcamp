"""
This script generates a CSV file with soil moisture data for the HTERRA 2022 F-SAR campaign.
The original data is provided as part of the ESA SARSimHT-NG project.
"""
import pandas as pd
import pyproj
import fsarcamp as fc

def read_original_csvs(folder_path, file_names):
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

def read_all():
    april_caione = read_original_csvs(
        fc.get_polinsar_folder() / "Ground_truth/HTerra_soil_2022/DataPackage_final/April22/soil_moisture_sensors/CAIONE",
        ["CA1_DW_24.csv", "CA1_DW_27.csv", "CA1_DW_28.csv", "CA1_DW_29.csv", "CA2_DW_24.csv", "CA2_DW_27.csv", "CA2_DW_28.csv", "CA2_DW_29.csv"],
    )
    april_crea = read_original_csvs(
        fc.get_polinsar_folder() / "Ground_truth/HTerra_soil_2022/DataPackage_final/April22/soil_moisture_sensors/CREA",
        ["CREA_BS_APRIL.csv", "CREA_DW26.csv", "CREA_DW27.csv", "CREA_DW28.csv", "CREA_DW29.csv"],
    )
    june_caione = read_original_csvs(
        fc.get_polinsar_folder() / "Ground_truth/HTerra_soil_2022/DataPackage_final/June22/soil_moisture_sensors/CAIONE",
        ["CA_AA_1.csv", "CA_AA_2.csv", "CA_AA_3.csv", "CA_MA_1.csv", "CA_MA_2.csv", "CA_MA_3.csv", "CA_MA_4.csv"],
    )
    june_crea = read_original_csvs(
        fc.get_polinsar_folder() / "Ground_truth/HTerra_soil_2022/DataPackage_final/June22/soil_moisture_sensors/CREA",
        ["CREA_MA_1.csv", "CREA_MA_2.csv", "CREA_QUINOA.csv", "CREA_SF.csv"]
    )
    return pd.concat([april_caione, april_crea, june_caione, june_crea], ignore_index=True)

if __name__ == "__main__":
    all_points = read_all()
    all_points.to_csv("visualization/hterra22_soil_moisture_v3.csv", index=False)
