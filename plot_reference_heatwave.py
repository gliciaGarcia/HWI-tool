import argparse
import os
import xarray as xr
from datetime import datetime, timedelta
import pandas as pd
from tools.make_figure_map_days import make_figure_reference
from tools.tools_idhw_v2 import split_dates_by_sequence


def arguments():
    parser = argparse.ArgumentParser(prog='plot_reference_heatwave.py')
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
        help='Região: BR ou NEB ou area1-summer',
    )

    return parser.parse_args()


def main():
    args = arguments()
    region = args.region
    day_first = args.date_init
    day_end = args.date_end

    dir = os.getcwd()

    path_heatwave = dir + '/dados/saida_IDHW/'
    data_ref_full = xr.open_dataset(f'{path_heatwave}/reference.heatwaves.{day_first}-{day_end}.nc')

    list_days = split_dates_by_sequence([pd.to_datetime(t) for t in data_ref_full.time.data])

    for days in list_days:
        t1 = days[0].strftime("%Y-%m-%d")
        t2 = days[-1].strftime("%Y-%m-%d")
        # data_clim = xr.open_dataset(f'{dir}/dados/dados_diarios_era5/climatology.daily.t2m_max.ERA5.1981_2020.nc')
        # data_clim = data_clim.sel(time=slice(t1, t2))

        data_ref = xr.open_dataset(f'{path_heatwave}/reference.heatwaves.{day_first}-{day_end}.nc')
        data_ref = data_ref.sel(time=slice(t1, t2))

        # anomaly_tmax = data_ref.t2m.data - data_clim.t2m.data
        # data_ref['anomalia'] = (('time', 'latitude', 'longitude'), anomaly_tmax)

        file_out = f'onda_de_calor_{t1}_{t2}_{region}.png'
        # file_out_anomaly = f'anomalia_onda_de_calor_{t1}_{t2}_{region}.png'

        if len(days) >= 10:
            row = 2
            col = 5
        if len(days) == 4:
            row = 2
            col = 2
        if len(days) == 5:
            row = 1
            col = 5
        print(len(days))

        # Figuras onda de calor
        make_figure_reference(
            data=data_ref,
            row=row,
            col=col,
            filename=file_out,
            area=region,
        )

    exit()



main()
