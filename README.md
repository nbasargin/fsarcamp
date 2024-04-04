# F-SAR campaigns package

The main purpose of this package is to provide a convenient way to load the data of different F-SAR campaigns, including F-SAR radar data (e.g. SLC, incidence), geocoding look-up tables (LUT), and campaign ground measurements (if available).

## Editable installation
- Clone this repository to your machine.
- Then, activate the python environment (e.g. conda or venv) where the package should be installed.
- Run `pip install -e .` in the root folder of this package (where `pyproject.toml` is located).

## Campaign components

Each F-SAR campaign is represented by a python class e.g. `CROPEX14Campaign` that contains data about all available campaign flights and passes.
Using this class you can obtain instances of F-SAR passes e.g. `CROPEX14Pass` that provide loaders for the radar data (e.g. SLC, incidence).

In addition, each campaign can provide loaders for the ground measurements.
The data varies from campaign to campaign and may include useful constants (e.g. specific dates), region boundaries (e.g. fields), point measurements, etc.

## Supported campaigns

F-SAR campaigns are usually experimental and the folder structure or file naming slightly change over the years.
This package is not intended to be a universal data loader but supports only specific F-SAR campaigns.
See the list of campaigns and the available data below.

### CROPEX 2014

Campaign focusing on agricultural crops with many flights over 10 weeks.
X-, C-, and L-band are available, some dates have several baselines allowing  tomography.

Several fields have been monitored during the campaign.
The measurement include crop height, water content, biomass, and soil moisture.

! Data loaders are planned to be implemented !


### HTERRA 2022

Campaign focusing on soil moisture in agricultural areas.
The campaign was executed in two missions, the first one in April and the second one in June.
There are 8 flights in total, most passes are zero-baseline, with a few exceptions.
C- and L-band are avaialble.

Several fields were monitored during the campaign.
The measurements include a large number of soil moisture points for each flight and some biomass measurements.

! Data loaders are planned to be implemented !


## License

Most of the code in this repository is open (MIT license).

Some source files have been obtained from other repositories, e.g. `https://gitlab.dlr.de/hr-stetools/stetools` and `https://gitlab.dlr.de/hr-rko-ir-pol-insar/common_code`.
The origin of third-party code is explicitly stated in the docstrings, refer to the original repository for the license.

Some campaign loaders provide (pre-processed) ground measurement data.
The origin of the data is noted in the docstrings of the pre-processing scripts.
The licence for the pre-processed data remains the same as for the original ground measurements.
