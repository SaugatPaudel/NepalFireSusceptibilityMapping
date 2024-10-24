from osgeo import gdal
import numpy as np
import pandas as pd
from pathlib import Path
from struct import unpack

gdal.UseExceptions()

gdal.SetConfigOption('GDAL_USE_CPL_MULTITHREAD', 'YES')
gdal.SetConfigOption('GDAL_NUM_THREADS', 'ALL_CPUS')


def _clear_memory(filepath: str | Path) -> None:
    if isinstance(filepath, Path):
        pass
    else:
        gdal.Unlink(filepath)


def classify_raster(*,
                    input_raster_path: Path,
                    output_raster_path: Path,
                    classification_range: tuple | dict
                    ) -> str | Path:

    print('Classifying raster ... ')
    raster_ds = gdal.Open(input_raster_path)
    band_ds = raster_ds.GetRasterBand(1)

    raster_x_size = raster_ds.RasterXSize
    raster_y_size = raster_ds.RasterYSize
    raster_geotransform = raster_ds.GetGeoTransform()
    raster_projection = raster_ds.GetProjection()

    nodata = band_ds.GetNoDataValue()
    if nodata is None:
        nodata = -128

    array_ds = band_ds.ReadAsArray()
    array_shape = array_ds.shape
    raster_ds = None
    band_ds = None

    classified_array = np.full(array_shape, nodata, dtype=np.int8)

    for low, high, value in classification_range:
        if low is None:
            classified_array[(array_ds < high) & (array_ds != nodata)] = value
        elif high is None:
            classified_array[(array_ds >= low) & (array_ds != nodata)] = value
        else:
            classified_array[(array_ds >= low) & (array_ds < high)] = value

    classified_array[array_ds == nodata] = -128

    array_ds = None

    raster_driver = gdal.GetDriverByName('GTiff')

    out_ds = raster_driver.Create(output_raster_path, raster_x_size, raster_y_size, 1, gdal.GDT_Int8)
    out_ds.SetGeoTransform(raster_geotransform)
    out_ds.SetProjection(raster_projection)

    out_band_ds = out_ds.GetRasterBand(1)
    out_band_ds.WriteArray(classified_array)
    out_band_ds.SetNoDataValue(-128)

    out_ds = None
    out_band_ds = None

    return output_raster_path


def _create_vrt(*, csv_path: Path, parameter: str) -> str:
    vrt_content = f'''
    <OGRVRTDataSource>
        <OGRVRTLayer name="{csv_path.stem}">
            <SrcDataSource>{csv_path}</SrcDataSource>
            <GeometryType>wkbPoint</GeometryType>
            <GeometryField encoding="PointFromColumns" x="lon" y="lat" z="{parameter}"/>
        </OGRVRTLayer>
    </OGRVRTDataSource>'''
    return vrt_content


def _parse_ewkb(hex_string: str) -> tuple[float, float]:
    # ogr le srid wala wkb directly support gardaina.
    # ewkb assumptions:
    #   Little endian.
    #   point data.
    #   srid for all and same srid.
    #   lat/lon after 9 bytes with 8 bytes each
    # aru format ma data aaye external library use garne.
    # ST_gromFromWkb ki yestai k pani chha. gdalgrid ma pass garna sakinchha kyare.

    offset = 18  # 9 bytes, 18 hex chars.

    lon_hex = hex_string[offset: offset + 16]
    lon_byte_array = bytes.fromhex(lon_hex)
    longitude = unpack('<d', lon_byte_array)[0]

    lat_hex = hex_string[offset + 16: offset + 32]
    lat_byte_array = bytes.fromhex(lat_hex)
    latitude = unpack('<d', lat_byte_array)[0]

    return latitude, longitude


def parse_raw_forecast_csv(*, raw_csv_filepath: Path, output_folder_path: Path) -> list[Path]:
    forecast_data_object = pd.read_csv(raw_csv_filepath)

    list_of_single_day_forecast_csv_filepaths = []

    forecast_data_object.rename(
        columns={
            'tmax_daily_tmax_region': 'tmax',
            'rainfall_daily_weighted_average': 'ppt',
            'rh_daily_avg_region': 'rh',
            'ws_daily_avg_region': 'ws',
            'date_range_start': 's_date',
            'date_range_end': 'e_date'
        },
        inplace=True
    )

    forecast_data_object.loc[:, 'ppt'] = forecast_data_object['ppt'].round(0).astype(int)
    forecast_data_object.loc[:, 'tmax'] = forecast_data_object['tmax'].round(0).astype(int)
    forecast_data_object.loc[:, 'rh'] = forecast_data_object['rh'].round(0).astype(int)

    forecast_data_object.loc[:, 'ppt'] = forecast_data_object['ppt'].clip(upper=127)

    forecast_data_object['s_date'] = pd.to_datetime(forecast_data_object['s_date'])
    forecast_data_object['e_date'] = pd.to_datetime(forecast_data_object['e_date'])

    forecast_data_object['lat'] = forecast_data_object['geom'].apply(_parse_ewkb).apply(lambda x: x[0])
    forecast_data_object['lon'] = forecast_data_object['geom'].apply(_parse_ewkb).apply(lambda y: y[1])

    forecast_data_object = forecast_data_object.sort_values(by=['administrative_id', 's_date'])

    unique_dates = forecast_data_object['s_date'].dt.date.unique()

    for i, date in enumerate(unique_dates):
        print(f'For forecast day {i + 1} with date: {date} ... ')

        day_data = forecast_data_object[forecast_data_object['s_date'].dt.date == date]

        final_day_data = day_data[['lat', 'lon', 'ppt', 'tmax', 'rh', 's_date', 'e_date']]

        single_day_forecast_csv_path = output_folder_path / f'{i + 1}_day_forecast.csv'

        final_day_data.to_csv(single_day_forecast_csv_path, index=False)

        if single_day_forecast_csv_path.exists():
            print(f'Csv file created: {single_day_forecast_csv_path.stem}\n')
            list_of_single_day_forecast_csv_filepaths.append(single_day_forecast_csv_path)
        else:
            print(f'Could not create file {single_day_forecast_csv_path} !')
            break
    return list_of_single_day_forecast_csv_filepaths


def _get_raster_info(*, input_raster_filepath: Path) -> dict:
    raster_ds = gdal.Open(input_raster_filepath)

    band_ds = raster_ds.GetRasterBand(1)
    nodata_value = band_ds.GetNoDataValue()
    band_ds = None

    raster_x_size_or_width = raster_ds.RasterXSize
    raster_y_size_or_height = raster_ds.RasterYSize
    geo_transform = raster_ds.GetGeoTransform()
    raster_ds = None

    min_lon_or_min_x = geo_transform[0]
    max_lon_or_max_x = geo_transform[0] + geo_transform[1] * raster_x_size_or_width
    max_lat_or_max_y = geo_transform[3]
    min_lat_or_min_y = geo_transform[3] + geo_transform[5] * raster_y_size_or_height

    geo_transform = None

    return {
        'x_size_or_width': raster_x_size_or_width,
        'y_size_or_height': raster_y_size_or_height,
        'min_lon_or_min_x': min_lon_or_min_x,
        'max_lon_or_max_x': max_lon_or_max_x,
        'max_lat_or_max_y': max_lat_or_max_y,
        'min_lat_or_min_y': min_lat_or_min_y,
        'nodata': nodata_value
    }


def create_gridded_raster_from_csv(*,
                                   input_csv_filepath: Path,
                                   output_raster_filepath: str | Path,
                                   information_raster_filepath: Path,
                                   create_raster_from_field: str
                                   ) -> str | Path:
    print('Creating gridded raster ... ')

    csv_vrt = _create_vrt(csv_path=input_csv_filepath, parameter=create_raster_from_field)
    vrt_ds = gdal.OpenEx(csv_vrt, gdal.OF_VECTOR, open_options=['VRT'])

    raster_info = _get_raster_info(input_raster_filepath=information_raster_filepath)

    grid_options = gdal.GridOptions(
        format='GTiff',
        outputType=gdal.GDT_Float32,
        outputBounds=[
            raster_info['min_lon_or_min_x'],
            raster_info['min_lat_or_min_y'],
            raster_info['max_lon_or_max_x'],
            raster_info['max_lat_or_max_y']
        ],
        outputSRS='EPSG:4326',
        noData=-9999,
        # TODO: Define suitable algorithm here. Defaults to inverse distance.
        # algorithm='nearest',
        zfield=create_raster_from_field
    )

    gridded_raster = gdal.Grid(
        destName=output_raster_filepath,
        srcDS=vrt_ds,
        options=grid_options
    )

    vrt_ds = None
    grid_options = None
    gridded_raster = None

    return output_raster_filepath


def reproject_raster(*, input_raster_filepath: Path, output_raster_filepath: str | Path) -> str | Path:

    print('Reprojecting raster ... ')

    warp_options = gdal.WarpOptions(
        format='Gtiff',
        srcSRS='EPSG:4326',
        dstSRS='EPSG:32645',
        outputType=gdal.GDT_Float32,
        srcNodata=_get_raster_info(input_raster_filepath=input_raster_filepath)['nodata'],
        dstNodata=-9999,
        multithread=True,
        resampleAlg=gdal.GRA_Bilinear,
        warpMemoryLimit=8192
    )

    reprojected_raster = gdal.Warp(
        destNameOrDestDS=output_raster_filepath,
        srcDSOrSrcDSTab=input_raster_filepath,
        options=warp_options
    )

    warp_options = None
    reprojected_raster = None

    return output_raster_filepath


def resample_raster(*, input_raster_filepath: Path, output_raster_filepath: str | Path) -> str | Path:

    print('Resampling raster ...')

    warp_options = gdal.WarpOptions(
        format='Gtiff',
        xRes=30,
        yRes=30,
        srcSRS='EPSG:32645',
        dstSRS='EPSG:32645',
        outputType=gdal.GDT_Float32,
        srcNodata=_get_raster_info(input_raster_filepath=input_raster_filepath)['nodata'],
        dstNodata=-9999,
        multithread=True,
        resampleAlg=gdal.GRA_CubicSpline,
        warpMemoryLimit=8192
    )

    resampled_raster = gdal.Warp(
        srcDSOrSrcDSTab=input_raster_filepath,
        destNameOrDestDS=output_raster_filepath,
        options=warp_options
    )

    warp_options = None
    resampled_raster = None

    return output_raster_filepath


def clip_raster(*,
                input_shapefile_filepath: Path,
                input_raster_filepath: Path,
                output_raster_filepath: str | Path
                ) -> str | Path:

    print('Clipping raster ...')

    warp_options = gdal.WarpOptions(
        format='Gtiff',
        xRes=30,
        yRes=30,
        srcSRS='EPSG:32645',
        dstSRS='EPSG:32645',
        outputType=gdal.GDT_Float32,
        dstNodata=-9999,
        multithread=True,
        cutlineLayer=input_shapefile_filepath.stem,
        cutlineDSName=input_shapefile_filepath,
        cropToCutline=True,
        cutlineSRS='EPSG:32645',
        warpMemoryLimit=8192
    )

    clipped_raster = gdal.Warp(
        srcDSOrSrcDSTab=input_raster_filepath,
        destNameOrDestDS=output_raster_filepath,
        options=warp_options
    )

    warp_options = None
    clipped_raster = None

    return output_raster_filepath


def constants_raster_pipeline(*,
                              input_raster_filepath: Path,
                              output_raster_filepath: Path,
                              input_shapefile_filepath: Path,
                              classification_range: dict
                              ) -> str | Path:

    step1 = clip_raster(
        input_raster_filepath=input_raster_filepath,
        input_shapefile_filepath=input_shapefile_filepath,
        output_raster_filepath='/vsimem/step1.tif'
    )

    step2 = classify_raster(
        input_raster_path=step1,
        output_raster_path=output_raster_filepath,
        classification_range=classification_range
    )

    _clear_memory(step1)
    _clear_memory(step2)

    return output_raster_filepath


def forecast_pipeline(*,
                      input_raster_filepath: str | Path,
                      classification_range: dict,
                      input_shapefile_filepath: Path,
                      output_raster_filepath: str | Path
                      ) -> str | Path:

    step1 = reproject_raster(
        input_raster_filepath=input_raster_filepath,
        output_raster_filepath='/vsimem/step1.tif'
    )

    step2 = resample_raster(
        input_raster_filepath=step1,
        output_raster_filepath='/vsimem/step2.tif'
    )

    _clear_memory(step1)

    step3 = clip_raster(
        input_shapefile_filepath=input_shapefile_filepath,
        input_raster_filepath=step2,
        output_raster_filepath='/vsimem/step3.tif'
    )

    _clear_memory(step2)

    step4 = classify_raster(
        input_raster_path=step3,
        output_raster_path=output_raster_filepath,
        classification_range=classification_range
    )

    _clear_memory(step3)
    _clear_memory(step4)

    return output_raster_filepath


if __name__ == '__main__':
    print('This file is meant to be run from main.py')
