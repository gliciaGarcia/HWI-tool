# -*- coding: utf-8 -*-

__author__ = ["Glícia R. G. Araújo"]
__credits__ = ["Glícia Garcia"]
__license__ = "GPL"
__version__ = "1.0"
__email__ = "glicia.garcia@inpe.br"


import argparse
import os
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import xarray as xr
from tools.tools_idhw_v2 import (  # Subroutines of the necessary functions
    check_dir, split_list)

warnings.filterwarnings('ignore')


def previsao_onda_de_calor(
        day,
        model=str,
        area=str,
        dir_forecast=str,
        dir_climatology=str,
        dir_out=str,
):
    """This script identifies heat wave events in forecast data.

    Args:
        day (str): forecast day
        model (str): model name.
        area (str): region of interest.
        dir_forecast (str): forecast data directory.
        dir_climatology (str): climatology data directory.
        dir_out (str): output data directory.
    """
    if model is None:
        print('Especifique o modelo de previsão no terminal!\n')
        print('Exemplo: --model gfs')
        exit()

    # -----------------------------------------------------------------------------------------------------------------------------------------

    dir_local = os.getcwd()

    # -----------------------------------------------------------------------------------------------------------------------------------------
    # Reading data
    # -----------------------------------------------------------------------------------------------------------------------------------------

    today = day - timedelta(days=0)

    # Forecast valid date
    prev_day = today + timedelta(days=2)

    times = pd.date_range(start=today, end=prev_day, freq='D')
    times = times.strftime('2020-%m-%d')
    print(f'\nInicialização em {today.strftime("%d-%m-%Y")} \n')

    # ----------------------------------------------------------------
    # Forecast
    # ----------------------------------------------------------------
    nc_prev = xr.open_dataset(f'{dir_forecast}/{model}.t00z.t2m.p18Z.nc')

    # Extract target coordinates from the target dataset
    target_coords = {
        'latitude': nc_prev['latitude'],
        'longitude': nc_prev['longitude']
    }

    # ----------------------------------------------------------------
    # ERA5 Climatology
    # ----------------------------------------------------------------
    nc = xr.open_dataset(dir_climatology)
    nc = nc.sel(time=slice(times[0], times[-1]))

    # Regrid the source dataset using target coordinates
    nc = nc.interp(coords=target_coords, method='linear')

    # Region Mask
    try:
        read_mask = xr.open_dataset(f'{dir_local}/tools/mask_region_{area}.nc').rename({'lon': 'longitude', 'lat': 'latitude'})
    except:
        read_mask = xr.open_dataset(f'{dir_local}/tools/mask_region_{area}.nc')
    regrid_mask = read_mask.interp(coords=target_coords, method='linear')

    if len(regrid_mask.mask.data.shape) == 2:
        mask = regrid_mask.mask.data
    else:
        mask = regrid_mask.mask[0].data
    
    # Climatology mask
    nc = nc.where(mask, np.nan)

    # Forecast mask
    nc1 = nc_prev.where(mask, np.nan)
    del nc_prev

    # Fixing the required variables
    Tmax = np.array(nc1['t2m'])
    tmax_count = np.array(nc1['t2m'][0, :, :])

    # --------------------------------------------------------------------------------------------------------------------------------------------------
    # COUNTING THE NUMBER OF GRID POINTS IN THE REGION
    # --------------------------------------------------------------------------------------------------------------------------------------------------
    points_land = np.count_nonzero(~np.isnan(tmax_count))      # Total number of grid points over the continent.
    print("total points over the continent:", points_land, '\n')

    # --------------------------------------------------------------------------------------------------------------------------------------------------
    # First criterion: clim Tmax + std for each grid point - climatological reference from 1981 to 2020 of ERA5.
    # --------------------------------------------------------------------------------------------------------------------------------------------------
    P1 = (nc['t2m'] + nc['std']).data

    # --------------------------------------------------------------------------------------------------------------------------------------------------
    # APPLICATION OF THE CRITERION TMAX > clim Tmax + std WITH A MINIMUM OF 3 CONSECUTIVE DAYS.
    # --------------------------------------------------------------------------------------------------------------------------------------------------
    crit = np.where(Tmax > P1, Tmax, np.nan)
    nc1['crit90'] = (('time', 'latitude', 'longitude'), crit)


    # Applying the second condition (minimum of three days).
    list_index = []
    for idx, value_time in enumerate(nc1.time.data):
        value_time = pd.to_datetime(value_time)
        count_valid = np.count_nonzero(~np.isnan(nc1.sel(time=value_time).crit90.data))
        if (count_valid/points_land) > 0.25:  # Spatial extent (default: 0.25).
            list_index.append(idx)

    # Eliminating list sequences of indices with a size smaller than 3
    list_filter = split_list(list_index)  # Separating by sequence of values
    file_out = dir_out + f'{model}.{today.strftime("%Y%m%d")}.onda_de_calor.nc'

    # Saving the files with extreme temperatures
    check_dir(dir_out)

    list_dates = nc1.time.data

    # The idea is to place NaN on the days that did not pass the heatwave criterion 
    # (keeping all days in a single file)
    if len(list_filter) != 0:
        
        list_datasets = []
        for idx in list_filter:
            # Days with heatwave
            evento = nc1.isel(time=idx)
            evento = evento.drop('t2m').rename_vars({'crit90': 't2m'})
            PI = evento.mean(dim=['time', 'latitude', 'longitude']).t2m.data

            #--------------------------------------------------------------------------------------------------------------------------------------------------
            # CALCULATING THE AVERAGE BETWEEN THE DAYS OF THE EVENT (INTENSITY PARAMETER - PI)
            #--------------------------------------------------------------------------------------------------------------------------------------------------
            P75 = nc.isel(time=idx)['percentil75'].mean(dim=['time', 'latitude', 'longitude']).values
            
            if PI > P75:
                msg = "Heat wave event identified! \n"
                # Days that did not pass the heatwave criterion
                dates_without_oc = [list_dates[index] for index in range(len(list_dates)) if index not in idx]
                sel_days = nc1.sel(time=dates_without_oc)
                days_empty = sel_days.where(False, np.nan)

                dataset = xr.concat([evento, days_empty], dim='time')
                dataset = dataset.sortby('time')
            else:
                msg = "No heat wave event was identified! \n"
                dataset = nc1.where(False, np.nan)
            list_datasets.append(dataset)

        dataset_final = xr.merge(list_datasets)
        dataset_final.to_netcdf(file_out)
    else:
        if len(list_index) == 0:
            msg = "No extreme TMAX events were identified (No heat wave)! \n"
            print('Forecast: ' + str(today.strftime('%d/%m/%Y')) + f' Valid: {prev_day.strftime("%d/%m/%Y")}\n')
            # Mask the entire dataset with NaN values
            file_empty = nc1.where(False, np.nan)
            file_empty.to_netcdf(file_out)
        else:
            msg = "Extreme TMAX event identified (No heat wave)! \n"
            print('Forecast: ' + str(today.strftime('%d/%m/%Y')) + f' Valid: {prev_day.strftime("%d/%m/%Y")}\n')
            evento = nc1.isel(time=list_index)
            evento = evento.drop('t2m').rename_vars({'crit90': 't2m'})

            # Days that did not meet the heatwave criterion
            dates_without_oc = [list_dates[index] for index in range(len(list_dates)) if index not in list_index]
            sel_days = nc1.sel(time=dates_without_oc)
            days_empty = sel_days.where(False, np.nan)

            dataset = xr.concat([evento, days_empty], dim='time')
            dataset = dataset.sortby('time')
            dataset.to_netcdf(file_out)
    print(msg)
    print(f'\nSaving file in... {file_out}\n')


def arguments():
    parser = argparse.ArgumentParser(prog='id_heatwaves_fcst.py')
    parser.add_argument(
        '--date',
        type=str,
        default=datetime.today(),
        help='Date: %Y%m%d',
    )

    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Forecasting model',
    )

    parser.add_argument(
        '--region',
        type=str,
        default='BR',
        help='Region: CE or NEB or BR or area1-summer',
    )

    return parser.parse_args()


def main():

    args = arguments()
    model = args.model
    region = args.region
    day = pd.to_datetime(args.date)

    dir_local = os.getcwd()
    path_fcst = f'{dir_local}/data/forecast_correction'
    path_clim = f'{dir_local}/data/era5_reanalysis/climatology.daily.t2m_max.ERA5.1981_2020.nc'

    print(f'\n\nIdentifying heat waves in the forecast - {model.upper()}\n\n')
    previsao_onda_de_calor(
        day,
        model=model,
        area=region,
        dir_forecast=path_fcst,
        dir_climatology=path_clim,
        dir_out=f'{dir_local}/data/out_HWI/'
    )


main()
