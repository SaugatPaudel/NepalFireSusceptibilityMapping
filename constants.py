from dataclasses import dataclass
from pathlib import Path

# Classification parameters
# classification_ranges:
#     (None, 50, 1),  values < 50 are classified as 1
#     (50, 100, 2),  values from >=50 to <100 are classified as 2
#     (100, 150, 3),  values from >=100 to <150 are classified as 3
#     (150, None, 4)  values >=150 are classified as 4


@dataclass(frozen=True)
class ClassificationParameters:
    dem: tuple[tuple] = (
        (None, 1000, 6),
        (1000, 2000, 4),
        (2000, 3000, 2),
        (3000, None, 1))

    slope: tuple[tuple] = (
        (None, 15, 6),
        (15, 30, 4),
        (30, 35, 2),
        (35, None, 1))

    lulc: tuple[tuple] = (
        (None, 2, 0),
        (2, 4, 9),
        (4, 11, 0),
        (11, None, 5))

    ndvi: tuple[tuple] = (
        (None, 0.3, 0),
        (0.3, 0.5, 4),
        (0.5, 0.7, 6),
        (0.7, None, 9))

    road: tuple[tuple] = (
        (None, 1000, 9),
        (1000, 2000, 6),
        (2000, 3000, 3),
        (3000, None, 1))

    settlement: tuple[tuple] = (
        (None, 1000, 9),
        (1000, 2000, 6),
        (2000, 3000, 3),
        (3000, None, 1))

    tmax: tuple[tuple] = (
        (None, 10, 1),
        (10, 15, 3),
        (15, 25, 6),
        (25, None, 9))

    rh: tuple[tuple] = (
        (None, 10, 6),
        (10, 30, 4),
        (30, 50, 2),
        (50, None, 1))

    ppt: tuple[tuple] = (
        (None, 1, 1),
        (1, 3, 0.1),
        (3, 5, 0.01),
        (5, None, 0))

    aspect: tuple[tuple] = (
        (0, 22.5, 2),  # N
        (22.5, 67.5, 3),  # NE
        (67.5, 112.5, 4),  # E
        (112.5, 157.5, 4),  # SE
        (157.5, 202.5, 5),  # S
        (202.5, 247.5, 1),  # SW
        (247.5, 292.5, 1),  # W
        (292.5, 337.5, 1),  # NW
        (337.5, 360, 2))  # N


@dataclass(frozen=True)
class FolderPaths:
    input: Path = Path('./Input/')
    output: Path = Path('./Output/')
    temporary: Path = Path('./Input/temp')

    def __post_init__(self):
        folder_paths = [self.input, self.output, self.temporary]
        missing_folder = [str(path) for path in folder_paths if not path.exists()]
        if missing_folder:
            raise FileNotFoundError(f"The following folders are missing: {', '.join(missing_folder)}")


@dataclass(frozen=True)
class RawVectorsFilePaths:
    buffered_boundary_utm45n: Path = Path('Input/Raw/nepal_boundary_buffered_3km_utm45n.shp')
    exact_boundary_utm45n: Path = Path('Input/Raw/nepal_boundary_exact_utm45n.shp')

    def __post_init__(self):
        file_paths = [self.buffered_boundary_utm45n, self.exact_boundary_utm45n]
        missing_files = [str(path) for path in file_paths if not path.exists()]
        if missing_files:
            raise FileNotFoundError(f"The following folders are missing: {', '.join(missing_files)}")


@ dataclass(frozen=True)
class RawRastersFilePaths:
    dem: Path = Path('Input/Raw/dem_utm45n.tif')
    slope: Path = Path('Input/Raw/slope_utm45n.tif')
    lulc: Path = Path('Input/Raw/lulc_utm45n.tif')
    ndvi: Path = Path('Input/Raw/ndvi_utm45n.tif')
    road: Path = Path('Input/Raw/road_utm45n.tif')
    settlement: Path = Path('Input/Raw/settlement_utm45n.tif')
    aspect: Path = Path('Input/Raw/aspect_utm45n.tif')

    def __post_init__(self):
        file_paths = [self.dem, self.slope, self.lulc, self.ndvi, self.road, self.settlement, self.aspect]
        missing_files = [str(path) for path in file_paths if not path.exists()]
        if missing_files:
            raise FileNotFoundError(f"The following files are missing: {', '.join(missing_files)}")


@dataclass(frozen=True)
class ClassifiedRastersFilePaths:
    dem: Path = Path('./Input/temp/cls_dem.tif')
    slope: Path = Path('./Input/temp/cls_slope.tif')
    lulc: Path = Path('./Input/temp/cls_lulc.tif')
    ndvi: Path = Path('./Input/temp/cls_ndvi.tif')
    road: Path = Path('./Input/temp/cls_road.tif')
    settlement: Path = Path('./Input/temp/cls_settlement.tif')
    aspect: Path = Path('./Input/temp/cls_aspect.tif')


@dataclass(frozen=True)
class FinalWeights:
    dem: float = 0.07
    slope: float = 0.11
    lulc: float = 0.24
    ndvi: float = 0.13
    road: float = 0.07
    settlement: float = 0.07
    tmax: float = 0.17
    rh: float = 0.07
    ppt: int = 1
    aspect: float = 0.07

    def __post_init__(self):
        weight_values = [self.dem, self.slope, self.lulc, self.ndvi, self.road, self.settlement, self.tmax, self.rh, self.aspect]
        print(sum(weight_values), round(sum(weight_values)))
        print(self.ppt, type(self.ppt), self.ppt == 1, (self.ppt != 1 or self.ppt != 0))
        if any(weight == 0 for weight in weight_values):
            raise ValueError('All weights must be non-zero.')
        elif round(sum(weight_values)) != 1:
            raise ValueError('Ensure that the sum of all weights except \'ppt\' is 1.')
        elif int(self.ppt) != 1 and int(self.ppt) != 0:
            raise ValueError('ppt values must be either 0 or 1')
        else:
            pass
        del weight_values


if __name__ == '__main__':
    print('This file is meant to be run from main.py')
