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


def onda_de_calor(
        day_init,
        day_final,
        area=str,
        dir_reference=str,
        dir_climatology=str,
        dir_out=str,
):
    """This script identifies heat wave events in reference data.

    Args:
        day_init (str): start date to find the event.
        day_final (str): final date to find the event
        area (str): region of interest.
        dir_reference (str): reference data directory.
        dir_climatology (str): climatology data directory.
        dir_out (str): output data directory.
    """

    # -----------------------------------------------------------------------------------------------------------------------------------------

    dir_local = os.getcwd()

    # -----------------------------------------------------------------------------------------------------------------------------------------
    # Reading data
    # -----------------------------------------------------------------------------------------------------------------------------------------

    times = pd.date_range(start=day_init, end=day_final, freq='D')
    times_clim = times.strftime('2020-%m-%d')

    print(f'\nStart date: {day_init} \nFinal date: {day_final}\n')

    # ERA5 Climatology
    nc = xr.open_dataset(dir_climatology)
    nc = nc.sel(time=slice(times_clim[0], times_clim[-1]))

    # Regrid data forecast
    # Extract target coordinates from the target dataset
    target_coords = {
        'latitude': nc['latitude'],
        'longitude': nc['longitude']
    }

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

    # Reference
    nc_ref = xr.concat([
        xr.open_dataset(f'{dir_reference}/{time.year}/t2m_max_era5_{time.strftime("%Y%m%d")}_p050.nc')
        for time in times
        ],
        dim='time'
    )


    # Regrid the source dataset using target coordinates
    nc_ref = nc_ref.interp(coords=target_coords, method='linear')
    nc1 = nc_ref.where(mask, np.nan)
    del nc_ref

    # Fixing the required variables
    Tmax = np.array(nc1['t2m'])
    tmax_count = np.array(nc1['t2m'][0, :, :])

    # --------------------------------------------------------------------------------------------------------------------------------------------------
    # COUNTING THE NUMBER OF GRID POINTS IN THE REGION
    # --------------------------------------------------------------------------------------------------------------------------------------------------
    points_land = np.count_nonzero(~np.isnan(tmax_count))      # Total number of grid points over the continent.
    print("total de pontos sobre o continente:", points_land, '\n')

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
    file_out = dir_out + f'reference.heatwaves.{day_init.strftime("%Y%m%d")}-{day_final.strftime("%Y%m%d")}.nc'

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
                msg = "\nEvento de onda de calor identificado!"
                print(msg)
                dataset = evento
                dataset = dataset.sortby('time')
                days = evento.time.dt.strftime("%Y-%m-%d")
                print(f'Evento com {len(days)} dias de duração: {days[0].data} - {days[-1].data}')
            else:
                msg = "Não foi identificado evento de onda de calor! \n"
                print(msg)
            list_datasets.append(dataset)

        if len(list_datasets) != 0:
            dataset_final = xr.merge(list_datasets)
            dataset_final.to_netcdf(file_out)
            print(f'\n\nSaving file in {file_out}')


def arguments():
    parser = argparse.ArgumentParser(prog='id_heatwaves.py')
    parser.add_argument(
        '--date-init',
        type=str,
        default=(datetime.today() - timedelta(days=50)).strftime("%Y%m%d"),
        help='Date: %Y%m%d',
    )

    parser.add_argument(
        '--date-end',
        type=str,
        default=(datetime.today() - timedelta(days=6)).strftime("%Y%m%d"),
        help='Date: %Y%m%d',
    )


    parser.add_argument(
        '--region',
        type=str,
        default='BR',
        help='Região: CE ou NEB ou BR ou area1-summer',
    )

    return parser.parse_args()


def main():

    args = arguments()
    region = args.region
    day_first = pd.to_datetime(args.date_init)
    day_end = pd.to_datetime(args.date_end)

    dir_pesq = '/pesq/share/monan/curso_OMM_INPE_2025/Validation/HeatWave/HWI-tool/'

    dir_local = os.getcwd()
    #path_ref = f'{dir_local}/dados/dados_diarios_era5'
    path_ref = f'{dir_pesq}/data/era5_reanalysis'

    #path_clim = f'{dir_local}/dados/dados_diarios_era5/climatology.daily.t2m_max.ERA5.1981_2020.nc'
    path_clim = f'{dir_pesq}/data/era5_reanalysis/climatology.daily.t2m_max.ERA5.1981_2020.nc'
    

    print(f'\n\nIdentificação de onda de calor na referência\n\n')
    onda_de_calor(
        day_first,
        day_end,
        area=region,
        dir_reference=path_ref,
        dir_climatology=path_clim,
        dir_out=f'{dir_local}/data/out_HWI/'
    )


main()
