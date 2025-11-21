import argparse
import os
import xarray as xr
from datetime import datetime
import pandas as pd
from tools.make_figure_map_days import make_figure, make_figure_anomaly



def arguments():
    parser = argparse.ArgumentParser(prog='mapa_dias_OC_basemap.py')
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
        help='Region: BR or NEB or area1-summer',
    )

    return parser.parse_args()


def main():
    args = arguments()
    model = args.model
    region = args.region
    day = pd.to_datetime(args.date)

    dir = os.getcwd()
    dir_pesq = '/pesq/share/monan/curso_OMM_INPE_2025/Validation/HeatWave/HWI-tool/'

    if model is None:
        print('Especifique o modelo de previsão no terminal!\n')
        print('Exemplo: --model monan')
        exit()

    path_heatwave = dir + '/data/out_HWI/'
    data_prev = xr.open_dataset(f'{path_heatwave}/{model}.{day.strftime("%Y%m%d")}.onda_de_calor.nc')
    # Extract target coordinates from the target dataset
    target_coords = {
        'latitude': data_prev['latitude'],
        'longitude': data_prev['longitude']
    }

    times = data_prev.time.dt.strftime("2020-%m-%d").data

    # ----------------------------------------------------------------
    # ERA5 Climatology
    # ----------------------------------------------------------------
    #data_clim = xr.open_dataset(f'{dir}/data/era5_reanalysis/climatology.daily.t2m_max.ERA5.1981_2020.nc')
    data_clim = xr.open_dataset(f'{dir_pesq}/data/era5_reanalysis/climatology.daily.t2m_max.ERA5.1981_2020.nc')

    # Regrid the source dataset using target coordinates
    data_clim = data_clim.interp(coords=target_coords, method='linear')
    data_clim = data_clim.sel(time=slice(times[0], times[-1]))

    anomaly_tmax = data_prev.t2m.data - data_clim.t2m.data

    data_prev['anomalia'] = (('time', 'latitude', 'longitude'), anomaly_tmax)

    #file_out = f'previsao_3dias_onda_de_calor_{model}_{region}.png'
    file_out = f'./figs/previsao_3dias_onda_de_calor_{model}_{region}.png'
    #file_out_anomaly = f'previsao_anomalia_3dias_onda_de_calor_{model}_{region}.png'
    file_out_anomaly = f'./figs/previsao_anomalia_3dias_onda_de_calor_{model}_{region}.png'

    # Figuras onda de calor 6 dias (Tmax)
    make_figure(
        data=data_prev,
        row=1,
        col=3,
        filename=file_out,
        area=region,
        model=model,
    )

    # Figuras onda de calor 6 dias (anomalia de Tmax)
    make_figure_anomaly(
        data=data_prev,
        row=1,
        col=3,
        filename=file_out_anomaly,
        area=region,
        model=model
    )


main()
