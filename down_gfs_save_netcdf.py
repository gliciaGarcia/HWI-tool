import argparse
import os
import subprocess
import warnings
from datetime import date, timedelta

import pandas as pd
import xarray as xr
from tools.tools_idhw_v2 import check_dir

warnings.filterwarnings('ignore')


def arguments():
    parser = argparse.ArgumentParser(prog='correcao_vies.py')
    parser.add_argument(
        '--date',
        type=str,
        default=date.today(),
        help='Date: %Y%m%d',
    )
    return parser.parse_args()


class GFSDownloader:
    def __init__(self, path_data, path_out, path_minio):
        self.path_data = path_data
        self.path_out = path_out
        self.path_minio = path_minio

    def download_gfs(self, date, hour_init, HR0, HR1, HDR, variable, var_name, filename):
        """Download GFS data.
        :param date: Initial forecast date.
        :param hour_init: Forecast initialization hour.
        :param HR0: Initial forecast hour.
        :param HR1: Final forecast hour.
        :param HDR: Forecast interval in hours (1, 3, 6, 24, ...).
        :param variable: Abbreviation of the variable.
        :param var_name: Full name of the variable.
        :param filename: Name of the netCDF file to be saved.
        """
        hour_init = f"{hour_init:02d}"
        time = pd.to_datetime(date)

        check_dir(self.path_data)
        check_dir(self.path_out)

        # Perl command to download the GRIB files
        perl_command = "/usr/bin/perl"
        perl_script = f"{os.getcwd()}/tools/get_gfs.pl"

        command = [
            perl_command,
            perl_script,
            "data",
            f"{time.strftime('%Y%m%d')}{hour_init}",
            f"{HR0}",
            f"{HR1}",
            f"{HDR}",
            var_name,
            f"{variable}",
            self.path_data
        ]

        print('\nstart date:', time, '\n')
        file_out = self.path_out + filename

        if not os.path.isfile(file_out):
            subprocess.run(command)

            datasets = []
            for hour in range(HR0, HR1, HDR):
                file = self.path_data + f'gfs.t00z.pgrb2.0p25.f{"{:03d}".format(hour)}'

                Hour = hour - HR0
                date_day = time + timedelta(hours=Hour)

                time18z = pd.to_datetime(date_day) + timedelta(hours=HR0)

                ds = xr.open_dataset(
                    file,
                    engine='cfgrib',
                    backend_kwargs=dict(filter_by_keys={'typeOfLevel': 'heightAboveGround', 'level': 2})
                )
                ds.coords['longitude'] = (ds.coords['longitude'] + 180) % 360 - 180
                ds = ds.sortby(ds.longitude)
                ds = ds.sel(latitude=slice(16, -52), longitude=slice(-88, -20))
                ds = ds['t2m']
                ds = ds.to_dataset().drop(['step', 'heightAboveGround', 'valid_time'])
                ds['time'] = [time18z]
                datasets.append(ds)

            data = xr.concat(datasets, dim='time')
            data.to_netcdf(file_out)
        else:
            print(f'File {file_out} already exists.')


    def start_download(self):
        print('\n\nStarting GFS forecast data download...\n')
        for t in times:
            file_model = f'gfs.t00z.{t.strftime("%Y%m%d")}.p18Z.nc'
            self.download_gfs(
                date=t,
                hour_init=0,
                HR0=18,
                HR1=162,
                HDR=24,
                variable='2 m above ground',
                var_name="TMP",
                filename=f'gfs.t00z.{t.strftime("%Y%m%d")}.p18Z.nc',
            )
        print('\nGFS download completed!\n')


if __name__ == "__main__":
    args = arguments()
    day = pd.to_datetime(args.date)
    times = pd.date_range(start=(day - timedelta(days=14)), end=day, freq='D')

    path_data = f'{os.getcwd()}/dados_previsao/tmp/'
    path_out = f'{os.getcwd()}/dados_previsao/'

    downloader = GFSDownloader(path_data, path_out, times)
    downloader.start_download()
