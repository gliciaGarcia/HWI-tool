import geopandas as gpd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
from shapely.geometry import Point


def check_contains(i, j, lon, lat, polygon):
    point = Point(lon, lat)
    return (i, j, polygon.contains(point))

def mask_from_shape(polygon, longitude, latitude):
    mask = np.empty((len(longitude), len(latitude)), dtype=bool)
    
    args_list = [(i, j, lon, lat, polygon) for i, lon in enumerate(longitude)
                 for j, lat in enumerate(latitude)]
    
    # Use ThreadPoolExecutor to avoid pickling issues
    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda args: check_contains(*args), args_list)
    
    for i, j, contains in results:
        mask[i, j] = contains

    return mask.T

# Serial mode
def mask_from_shape_serial(polygon,longitude,latitude):

 
    mask = np.empty((len(longitude), len(latitude)), dtype=bool)
    for i,lon in enumerate(longitude):
        for j,lat in enumerate(latitude):
            point=Point(lon,lat)
            mask[i,j] = polygon.contains(point)
    
    return mask.T


if __name__ == '__main__':

    ## Usage example:
    filename = '../dados/dados_diarios_era5/2024/t2m_max_era5_20241016_p050.nc'
    shape_path = '../shape/area1_verao/area1_verao.shp'

    ds = xr.open_dataset(filename)

    gdf = gpd.read_file(shape_path)
    poly = gdf.iloc[0]['geometry']

    mask = mask_from_shape(poly, ds.longitude, ds.latitude)
    ds['mask'] = (('latitude', 'longitude'), mask.astype(int))
    ds = ds.drop('t2m')
    ds.to_netcdf('mask_region_area1-summer.nc')
    ds.mask.plot()
    plt.show()

