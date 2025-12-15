# F-SAR campaigns package
The main purpose of this package is to provide a convenient way to load the data of different F-SAR campaigns, including F-SAR radar data (e.g. SLC, incidence), geocoding lookup tables (LUT), and campaign ground measurements (if available).

## Installation
`pip install fsarcamp`

Alternatively, you can install the package in editable mode:
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
This package is not intended to be a universal data loader and only supports specific F-SAR campaigns.
See the list of campaigns and the available data below.

### CROPEX 2014
Campaign focusing on agricultural crops with many flights over 10 weeks.
X-, C-, and L-band are available, some dates have several baselines allowing tomography.

Several fields have been monitored during the campaign.
The measurement include crop height, water content, biomass, and soil moisture.

Following data loaders and definitions are available:
- `CROPEX14Campaign`: F-SAR data loader (SLC, incidence, lookup tables, etc.)
- `CROPEX14Biomass`: Point-wise biomass ground measurements collected by the ground teams over specific fields
- `CROPEX14Moisture`: Point-wise soil moisture ground measurements collected by the ground teams over specific fields
- `CROPEX14Regions`: Region definitions for the relevant fields (as polygons)

### HTERRA 2022
Campaign focusing on soil moisture in agricultural areas.
The campaign was executed in two missions, the first one in April and the second one in June.
There are 8 flights in total, most passes are zero-baseline, with a few exceptions.
C- and L-band are available.

Several fields were monitored during the campaign.
The measurements include a large number of soil moisture points for each flight and some biomass measurements.

Following data loaders and definitions are available:
- `HTERRA22Campaign`: F-SAR data loader (SLC, incidence, lookup tables, etc.)
- `HTERRA22Moisture`: Point-wise soil moisture ground measurements collected by the ground teams over specific fields
- `HTERRA22Regions`: Region definitions for the relevant fields (as polygons)

### CROPEX 2025 (AgriROSE-L)
Campaign focusing on agricultural crops and soil moisture with regular flights from April to July 2025.
X-, C-, S-, and L-band are available, most dates have several baselines allowing tomography.
Several fields have been monitored during the campaign with a focus on soil moisture and vegetation parameters.

Following data loaders and definitions are available:
- `CROPEX25Campaign`: F-SAR data loader (SLC, incidence, lookup tables, etc.)
- `CROPEX25Moisture`: Point-wise soil moisture ground measurements collected by the ground teams over specific fields
- `CROPEX25Regions`: Region definitions for the relevant fields (as polygons)

# Notes
This repository includes third party code obtained from `https://github.com/birgander2/PyRAT` to read RAT files.
Third party code is located in the `fsarcamp/src/fsarcamp/ste_io` folder and is licensed under the MPL-2.0 license.

# Changelog

## v3.1.1
Added
- Added `inv_value` to WindowedGeocoding

## v3.1.0
Added
- Added support for the T10 version (D-InSAR) for CROPEX 2025

## v3.0.1
Fixes
- fix WindowedGeocoding valid min index computation for LUTs with negative index values

## v3.0.0
Added
- Data loaders for the CROPEX 2025 campaign

Breaking changes
- GTC lookup tables have been adjusted to support different coordinates, a new class is provided
- Related geocoding functionality has been moved and adjusted: now the lookup tables are responsible for geocoding
- Deprecated modules and functions were removed
- Region definitions are now a plain dictionary, mapping names to polygons in longitude-latitude coordinates
- GeoCrop (region of a lookup table) was replaced by WindowedGeocoding with similar functionality
- interpolation functions have been changed to work on full LUT / SLC extent instead of regions

## v2.0.1
First publicly available version of this package.
Provides data loaders for the CROPEX 2014 and HTERRA 2022 campaigns.
