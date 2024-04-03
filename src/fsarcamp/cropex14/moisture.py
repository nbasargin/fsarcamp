"""
Data loader for soil moisture ground measurements for the CROPEX 2014 campaign.
"""

from importlib import resources as impresources
import pandas as pd
from fsarcamp.cropex14 import moisturedata

def get_cropex14_soil_moisture():
    """
    Load ground truth measurements for soil moisture during the CROPEX 14 campaign.
    Return a pandas dataframe. Soil moisture values range from 0 (0%) to 1 (100%).
    """
    inp_file = impresources.files(moisturedata) / "cropex14_soil_moisture_v1.csv"
    df = pd.read_csv(inp_file)
    df["date_time"] = pd.to_datetime(df["date_time"])
    return df
