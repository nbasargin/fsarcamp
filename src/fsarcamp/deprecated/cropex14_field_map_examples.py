import numpy as np
import shapely
import matplotlib.pyplot as plt
import fsarcamp as fc
import fsarcamp.cropex14 as cr14


def example_filter_fields_by_long_lat():
    """
    Look up a field by longitude latitude coordinates.
    """
    shapefile_path = (
        fc.get_polinsar_folder()
        / "Ground_truth/Wallerfing_campaign_May_August_2014/kmz-files/Land_use_Wallerfing_2014_shp+kmz/flugstreifen_wallerfing_feka2014.dbf"
    )
    campaign = cr14.CROPEX14Campaign(fc.get_polinsar_folder() / "01_projects/CROPEX/CROPEX14")
    field_map = cr14.CROPEX14FieldMap(shapefile_path, campaign)
    pass_name, band = "14cropex0203", "C"
    fields = field_map.load_fields(pass_name, band)
    # filter field by longitude, latitude
    longitude, latitude = 12.873469, 48.696072
    point = shapely.Point(longitude, latitude)
    fields = fields[fields["poly_longitude_latitude"].contains(point)]
    print(fields)


def example_load_field_by_id():
    """
    Look up a field by ID.
    """
    shapefile_path = (
        fc.get_polinsar_folder()
        / "Ground_truth/Wallerfing_campaign_May_August_2014/kmz-files/Land_use_Wallerfing_2014_shp+kmz/flugstreifen_wallerfing_feka2014.dbf"
    )
    campaign = cr14.CROPEX14Campaign(fc.get_polinsar_folder() / "01_projects/CROPEX/CROPEX14")
    field_map = cr14.CROPEX14FieldMap(shapefile_path, campaign)
    pass_name, band = "14cropex0203", "C"
    fields = field_map.load_field_by_id(cr14.CORN_C2, pass_name, band)
    print(fields)


def example_crop_mask_raster():
    shapefile_path = (
        fc.get_polinsar_folder()
        / "Ground_truth/Wallerfing_campaign_May_August_2014/kmz-files/Land_use_Wallerfing_2014_shp+kmz/flugstreifen_wallerfing_feka2014.dbf"
    )
    campaign = cr14.CROPEX14Campaign(fc.get_polinsar_folder() / "01_projects/CROPEX/CROPEX14")
    field_map = cr14.CROPEX14FieldMap(shapefile_path, campaign)
    pass_name, band = "14cropex0203", "C"
    fields = field_map.load_fields(pass_name, band)
    # filter fields that contain a single crop type
    fields = fields[fields["num_crop_types"] == 1]
    # filter fields that contain a specific crop
    crop_code = 411  # Silage maize (corn)
    fields = fields[fields["crop_code_1"] == crop_code]
    # add a data column that will be rasterized, note the float dtype (allow NaNs)
    fields["raster_data"] = 1.0  # fill all matching fields with 1.0
    # create rasters in LUT and SLC coordinates
    field_lut_raster = field_map.create_field_lut_raster(fields, "raster_data", pass_name, band, invalid_value=np.nan)
    field_slc_raster = field_map.create_field_slc_raster(fields, "raster_data", pass_name, band, invalid_value=np.nan)
    # load SLC data for the backdrop
    fsar_pass = campaign.get_pass("14cropex0203", "C")
    slc = fsar_pass.load_rgi_slc("hh")
    lut = fsar_pass.load_gtc_sr2geo_lut()
    hh_slc = np.abs(slc)
    vmax = np.mean(hh_slc) * 2
    hh_lut = fc.nearest_neighbor_lookup(hh_slc, lut.lut_az, lut.lut_rg)
    # plot rasters over the backdrop
    # SLC coordinates
    plt.figure(figsize=(12, 6))
    plt.title("Crop mask over HH SLC, SLC coordinates")
    plt.imshow(np.rot90(hh_slc, 3), vmin=0, vmax=vmax)
    plt.imshow(np.rot90(field_slc_raster, 3), vmin=0, vmax=1, cmap="jet")
    plt.savefig("visualization/crop_mask_slc.png", dpi=300)
    plt.close("all")
    # LUT coordinates
    plt.figure(figsize=(8, 8))
    plt.title("Crop mask over HH SLC, LUT coordinates")
    plt.imshow(hh_lut, vmin=0, vmax=vmax)
    plt.imshow(field_lut_raster, vmin=0, vmax=1, cmap="jet")
    plt.savefig("visualization/crop_mask_lut.png", dpi=300)
    plt.close("all")


if __name__ == "__main__":
    example_load_field_by_id()
