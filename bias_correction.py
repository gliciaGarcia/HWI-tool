import argparse
import os
import warnings
from datetime import date, timedelta
from glob import glob

import numpy as np
import pandas as pd
import xarray as xr

from tools.tools_idhw_v2 import check_dir

warnings.filterwarnings('ignore')


def read_era5_reanalysis(dates, dir_out):
        """
        Read ERA5 reanalysis data.
        """
        files = [
            f'{dir_out}/{t.strftime("%Y")}/t2m_max_era5_{t.strftime("%Y%m%d")}_p050.nc'
            for t in dates
        ]
        list_datasets = []
        for filename in files:
            if not os.path.isfile(filename):
                print(f'ERROR in Accessing {filename.split("/")[-1]}')
            else:
                print(f'File {filename.split("/")[-1]} exists!')
                dataset = xr.open_dataset(filename)
                list_datasets.append(dataset)

        data_obs = xr.concat(list_datasets, dim='time')

        return data_obs


def bias_correction(
        h,
        day_fcst,
        dates=list,
        file_obs=str,
        dir_fcst=str,
):
    """Function: Bias correction.
    Args:
        :param h: Forecast hour index (0 for 18Z, 1 for 42Z, 2 for 66Z).
    :type h: int
        :param day_fcst: Forecast day.
    :type day_fcst: forecast time
        :param dates: Dates for bias calculation (previous 15 days).
    :type dates: list
        :param file_obs: Reference data (15 days of observation).
    :type dates: forecast time
        :param dir_fcst: Directory where the t2m forecast file is located.
    :type dir: str
    """

    list_vies = []
    for tt in dates:
        if tt + timedelta(days=h) < day_fcst:

            file = glob(f'{dir_fcst}/{tt.strftime("%Y%m%d")}00/*{(tt + timedelta(days=h)).strftime("%Y%m%d")}18.00.00*.nc')[0]

            data_prev = xr.open_dataset(file)['t2m'] - 273.16  # Convert from K to °C
            data_prev = data_prev.rename({'Time': 'time'})

            # Regrid observation data
            # Extract target coordinates from the target dataset
            target_coords = {
                'latitude': data_prev['latitude'],
                'longitude': data_prev['longitude']
            }

            # Regrid the source dataset using target coordinates
            regridded_obs = file_obs.interp(coords=target_coords, method='linear')


            data_prev = data_prev.sel(
                time=slice(str(file_obs.time[0].data).split('T')[0],
                        str(file_obs.time[-1].data).split('T')[0])
            )
            regridded_obs = regridded_obs.sel(
                time=slice(str(data_prev.time[0].data).split('T')[0],
                        str(data_prev.time[-1].data).split('T')[0])
            )

            vies = data_prev - regridded_obs.t2m.data
    
            list_vies.append(vies)

    final_vies = np.array(list_vies)
    # print(final_vies.shape)
    final_vies = np.mean(final_vies, axis=0)
    # print(final_vies.shape)

    return final_vies


def arguments():
    parser = argparse.ArgumentParser(prog='bias_correction.py')
    parser.add_argument(
        '--date',
        type=str,
        default=date.today(),
        help='Date: %Y%m%d',
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Forecast model',
    )
    return parser.parse_args()


def main():
    args = arguments()
    day = pd.to_datetime(args.date)
    model = args.model

    dir_local = os.getcwd()
    dir_obs = f'{dir_local}/data/era5_reanalysis'

    if day.strftime('%Y%m%d') == date.today().strftime('%Y%m%d'):
        time = day - timedelta(days=6)
    else:
        time = day - timedelta(days=1)

    # Apply bias correction using the previous 10 days of data
    times = pd.date_range(time - timedelta(days=9), time)

    print('\n\nStarting to read ERA5 data...\n')
    reference = read_era5_reanalysis(dates=times, dir_out=dir_obs)
    print('Completed!')

    # Bias Correction
    print(f'\n\nStarting bias correction for {model} forecast - Day {day.strftime("%Y%m%d")}...\n')

    dir_prev = f'{os.getcwd()}/data/monan_forecasts'

    hours_lookahead = [18, 42, 66]  # Forecast hour to be corrected

    list_ds = []
    for idx, h in enumerate(hours_lookahead):
        print(f'Forecast hour: {h}Z')
        bias = bias_correction(
            h=idx,
            day_fcst=day,
            dates=pd.date_range(str(reference.time[0].data).split('T')[0], str(reference.time[-1].data).split('T')[0], freq='D'),
            file_obs=reference,
            dir_fcst=dir_prev,
        )

        print(f'\nApplying bias correction to {model} forecast - Day {day.strftime("%Y%m%d")}00Z | Valid: {(day + timedelta(days=idx)).strftime("%Y%m%d")}18Z...\n')
        dir_out=dir_local + '/data/forecast_correction/'
        check_dir(dir_out)

        today = day - timedelta(days=0)
        file_today = glob(f'{dir_prev}/{today.strftime("%Y%m%d")}00/*{(today + timedelta(days=idx)).strftime("%Y%m%d")}18.00.00*.nc')[0]
        prev_init_today = xr.open_dataset(file_today)['t2m'] - 273.16
        prev_init_today = prev_init_today.rename({'Time': 'time'})

        # Removing bias from the forecast
        prev_corr = prev_init_today - bias
        list_ds.append(prev_corr)

    # Concatenate all forecast hours into a single dataset
    prev_corr_final = xr.concat(list_ds, dim='time')

    # Save corrected forecast to NetCDF
    prev_corr_final.to_netcdf(f'{dir_out}/{model}.t00z.t2m.p18Z.nc')
    print(f'\nSaving file in {dir_out}/{model}.t00z.t2m.p18Z.nc\n')

    print('Completed!\n')


main()
