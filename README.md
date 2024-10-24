# Fire Susceptibility Mapping for Nepal

This project generates a fire susceptibility map for Nepal, using both static geographic data and dynamic forecast data. It incorporates environmental factors such as terrain elevation (DEM), slope, aspect, land use, distance to roads, distance to settlements, NDVI, and weather forecast variables like rainfall, wind speed, and relative humidity.

## Overview

This project calculates fire susceptibility across Nepal by combining seven static factors and weather forecasts to create a dynamic fire risk model. 

### Static Factors
- **DEM (Digital Elevation Model)**
- **Slope**
- **Aspect**
- **NDVI (Normalized Difference Vegetation Index)**
- **Land Use**
- **Distance from Roads**
- **Distance from Settlements**

### Dynamic Forecast Inputs
- **Rainfall**
- **Wind Speed**
- **Relative Humidity**

The goal is to classify these factors, assign weights, and generate fire risk maps using GDAL for raster operations.

## Installation

1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/yourusername/fire-susceptibility-nepal.git
   cd fire-susceptibility-nepal
   ```

2. Install the necessary dependencies using `requirements.txt`:
   ```bash
   conda create --name firesusceptibility --file requirements.txt
   conda activate firesusceptibility
   ```

3. Make sure you have [GDAL](https://gdal.org/download.html) installed, as it is required for raster data processing.

## Usage

1. Place the required input raster and vector files in the `./Input/Raw/` folder.
2. Forecast data should be in CSV format and placed in `./Input/Raw/yourfilename.csv`.

3. To generate the fire susceptibility map, run the `main.py` script:
   ```bash
   python main.py
   ```

The script will generate classified rasters for static factors, create a base fire susceptibility map, and use forecast data to update the fire susceptibility for each forecasted day.

## Inputs

### Static Rasters (in `./Input/Raw/`):
- `dem_utm45n.tif`: Digital Elevation Model
- `slope_utm45n.tif`: Slope of terrain
- `aspect_utm45n.tif`: Aspect (direction of slope)
- `ndvi_utm45n.tif`: Vegetation Index
- `lulc_utm45n.tif`: Land use and land cover
- `road_utm45n.tif`: Distance to roads
- `settlement_utm45n.tif`: Distance to settlements

### Forecast CSV (in `./Input/Raw/`):
- `yourfilename.csv`: Forecast data including rainfall, temperature (tmax), and relative humidity (rh).

## Outputs

- **Base Fire Susceptibility Map**: Generated using static factors.
- **Forecast Fire Susceptibility Maps**: Updated based on weather forecast, saved in `./Output/`.

## Project Structure

```plaintext
├── Input/
│   ├── Raw/
│   │   ├── dem_utm45n.tif
│   │   ├── slope_utm45n.tif
│   │   ├── aspect_utm45n.tif
│   │   ├── yourfilename.csv
│   │   └── ... (other input rasters)
│   └── temp/           # Temporary files
├── Output/              # Final maps generated
├── constants.py         # Contains classification parameters and file paths
├── functions.py         # Functions for raster classification, clipping, etc.
├── main.py              # Main script for running the project
├── requirements.txt     # Conda environment dependencies
└── README.md            # Project documentation
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

This `README.md` should help guide users to understand, install, and run your project successfully!
