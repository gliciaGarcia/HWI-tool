import warnings
import os
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.offsetbox import (  # The OffsetBox is a simple container artist.
    AnnotationBbox, OffsetImage)
from matplotlib.patches import Path, PathPatch
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point

mpl.use("agg")

dir_local = os.getcwd()

warnings.filterwarnings('ignore')


# Parallel mode
def check_contains(args):
    i, j, lon, lat, polygon = args
    point = Point(lon, lat)
    return (i, j, polygon.contains(point))


def cut2shapefile(plot_obj, shape_obj):
    """
    plot_obj: axis where plot is being made. ex: ax
    shape_obj: basemap shapefile.
    ex: m.nordeste_do_brasil when shape is read with m.readshapefile(path/to/nordeste_do_brasil, nordeste_do_brasil)
    """

    x0, x1 = plot_obj.get_xlim()
    y0, y1 = plot_obj.get_ylim()

    edges = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    edge_codes = [Path.MOVETO] + (len(edges) - 1) * [Path.LINETO]

    verts = shape_obj[0] + [shape_obj[0][0]]
    codes = [Path.MOVETO] + (len(verts) - 1) * [Path.LINETO]

    path = Path(verts+edges, codes+edge_codes)

    patch = PathPatch(path, facecolor='white', lw=0)
    plot_obj.add_patch(patch)


def make_figure(
        data,
        row=int,
        col=int,
        filename=str,
        area='BR',
        model=str,
        ):
    """function that generates the forecast figure.

    Args:
        data (dataset): forecast dataset.
        row (int): Number of rows of the subplot grid.
        col (int): Number of columns of the subplot grid..
        filename (str): output filename.
        area (str): region of interest. Defaults to 'BR'.
        model (str): name model.
    """

    if area == 'BR':
        lon_min, lon_max, lat_min, lat_max = (-75, -30, -35, 10)
    if area == 'area1-summer':
        lon_min, lon_max, lat_min, lat_max = (-88, -30, -52, 16)

    shapefile = dir_local + '/shape/BR_UF_2021/BR_UF_2021.shp'

    shp = gpd.read_file(shapefile)
    shp = shp[shp.NM_UF == 'Ceará']
    shp = shp.explode().iloc[0].geometry

    x, y = shp.exterior.coords.xy
    t = [[(a, s) for a, s in zip(x, y)]]

    if area == 'CE':
        fig, axarr = plt.subplots(row, col, figsize=(12, 9))
    else:
        fig, axarr = plt.subplots(row, col, figsize=(14, 8))

    lat, lon = (data.latitude.data, data.longitude.data)

    lon2d, lat2d = np.meshgrid(lon, lat)

    temp = np.array(data['t2m'][:])  # Lendo todo o tempo da variável t2m para usar o min e o max no levels

    levs = [30, 32, 34, 36, 38, 39, 40]

    jet_white = (
        '#ffe0b3',
        '#ffb84d',
        '#FF7F00',
        '#FF0000',
        '#c10000',
        '#880000'
        )

    levs = np.array(levs)

    my_cmap = ListedColormap(jet_white)
    my_cmap.set_over('#540002')
    my_cmap.set_under('#f8fa7a')

    for index, ax in enumerate(axarr.ravel()):

        if area == 'CE':
            mymap = Basemap(
                projection='cyl', llcrnrlat=-8,
                urcrnrlat=-2, llcrnrlon=-42,
                urcrnrlon=-37, ax=ax
                )
            mymap.drawmeridians(np.arange(0, 360, 1), labels=[0, 0, 0, 1], linewidth=0.01, fontsize=10)
            mymap.drawparallels(np.arange(-90, 90, 1), labels=[1, 0, 0, 0], linewidth=0.01, fontsize=10)
            mymap.readshapefile(
                f'{dir_local}/shape/i3geomap_limite_municipal/i3geomap_limite_municipal',
                'i3geomap_limite_municipal',
                color='black',
                linewidth=0.2,
                zorder=3000
                )
        else:
            mymap = Basemap(
                projection='cyl', llcrnrlat=lat_min,
                urcrnrlat=lat_max, llcrnrlon=lon_min,
                urcrnrlon=lon_max, ax=ax
                )
            mymap.drawparallels(np.arange(-60, 20, 5), labels=[1, 0, 0, 0], fontsize=12, linewidth=0.01)
            mymap.drawmeridians(np.arange(-90, 0, 10), labels=[0, 0, 0, 1], fontsize=12, linewidth=0.01)
            mymap.drawcoastlines(linewidth=0.2)

        x, y = mymap(lon2d, lat2d)

        mymap.readshapefile(f'{dir_local}/shape/BR_UF_2021/BR_UF_2021', 'BR_UF_2021', color='black', linewidth=0.9)

        tp = mymap.pcolormesh(x, y, temp[index], ax=ax, cmap=my_cmap,
                              norm=mpl.colors.BoundaryNorm(levs, ncolors=my_cmap.N, clip=False)
                              )
        if area == 'CE':
            cut2shapefile(ax, t)

        ax.set_title(str(np.array(data["time"][index].dt.strftime("%d-%m-%Y"))), fontsize=14)

    # Desenhando a barra da escala de cores
    # the dimensions add_axes[left, bottom, width, height] of the new Axes
    cbar_ax = fig.add_axes([0.91, 0.16, 0.02, 0.6])
    cbar = fig.colorbar(tp, cax=cbar_ax, orientation="vertical", extend='both')
    cbar.set_label('°C', fontsize=14)
    cbar.ax.set_xticklabels(labels=cbar.ax.get_xticklabels(), weight='bold', fontsize=12)

    plt.suptitle('Previsão de Onda de Calor', fontsize=20, fontweight='bold')
    plt.tight_layout()
    plt.subplots_adjust(top=0.91, bottom=0.048, left=0.035, right=0.864, hspace=0.2, wspace=0.15)
    datei = f'{pd.to_datetime(data["time"][0].data).strftime("%d/%m/%Y")}'
    datef = f'{pd.to_datetime(data["time"][-1].data).strftime("%d/%m/%Y")}'
    plt.text(
        0.4, 2.40,
        f'GFS 25km rodada de {datei} 0000 UTC\nVálido até {datef} 1800 UTC',
        transform=ax.transAxes,
        verticalalignment='top',
        fontsize=10,
        fontweight='bold'
        )  # y -> 2.4; 0.4

    plt.savefig(filename, dpi=200)



def make_figure_anomaly(
        data,
        row=int,
        col=int,
        filename=str,
        area='BR',
        model=str
        ):
    """function that generates the forecast figure.

    Args:
        data (dataset): anomaly forecast dataset.
        row (int): Number of rows of the subplot grid.
        col (int): Number of columns of the subplot grid..
        filename (str): output filename.
        area (str): region of interest. Defaults to 'BR'.
        model (str): name model.
    """

    if area == 'BR':
        lon_min, lon_max, lat_min, lat_max = (-75, -30, -35, 10)
    if area == 'area1-summer':
        lon_min, lon_max, lat_min, lat_max = (-88, -30, -52, 16)

    shapefile = dir_local + '/shape/BR_UF_2021/BR_UF_2021.shp'

    shp = gpd.read_file(shapefile)
    shp = shp[shp.NM_UF == 'Ceará']
    shp = shp.explode().iloc[0].geometry

    x, y = shp.exterior.coords.xy
    t = [[(a, s) for a, s in zip(x, y)]]

    if area == 'CE':
        fig, axarr = plt.subplots(row, col, figsize=(12, 9))
    else:
        fig, axarr = plt.subplots(row, col, figsize=(14, 8))

    lat, lon = (data.latitude.data, data.longitude.data)

    lon2d, lat2d = np.meshgrid(lon, lat)

    temp = np.array(data['anomalia'][:])  # Lendo todo o tempo da variável t2m para usar o min e o max no levels

    levs = [1, 2, 3, 4, 5]
    jet_white = (
        '#f8fa7a',
        '#ffb84d',
        '#FF7F00',
        '#FF0000',
        '#c10000'
        )

    levs = np.array(levs)

    my_cmap = ListedColormap(jet_white)
    my_cmap.set_over('#540002')

    for index, ax in enumerate(axarr.ravel()):

        if area == 'CE':
            mymap = Basemap(
                projection='cyl', llcrnrlat=-8,
                urcrnrlat=-2, llcrnrlon=-42,
                urcrnrlon=-37, ax=ax
                )
            mymap.drawmeridians(np.arange(0, 360, 1), labels=[0, 0, 0, 1], linewidth=0.01, fontsize=10)
            mymap.drawparallels(np.arange(-90, 90, 1), labels=[1, 0, 0, 0], linewidth=0.01, fontsize=10)
            mymap.readshapefile(
                f'{dir_local}/shape/i3geomap_limite_municipal/i3geomap_limite_municipal',
                'i3geomap_limite_municipal',
                color='black',
                linewidth=0.2,
                zorder=3000
                )
        else:
            mymap = Basemap(
                projection='cyl', llcrnrlat=lat_min,
                urcrnrlat=lat_max, llcrnrlon=lon_min,
                urcrnrlon=lon_max, ax=ax
                )
            mymap.drawparallels(np.arange(-60, 20, 5), labels=[1, 0, 0, 0], fontsize=12, linewidth=0.01)
            mymap.drawmeridians(np.arange(-90, 0, 10), labels=[0, 0, 0, 1], fontsize=12, linewidth=0.01)
            mymap.drawcoastlines(linewidth=0.2)

        x, y = mymap(lon2d, lat2d)

        mymap.readshapefile(f'{dir_local}/shape/BR_UF_2021/BR_UF_2021', 'BR_UF_2021', color='black', linewidth=0.9)

        tp = mymap.pcolormesh(
            x, y, temp[index], ax=ax, cmap=my_cmap,
            norm=mpl.colors.BoundaryNorm(levs, ncolors=my_cmap.N, clip=False)
            )
        if area == 'CE':
            cut2shapefile(ax, t)

        ax.set_title(str(np.array(data["time"][index].dt.strftime("%d-%m-%Y"))), fontsize=14)

    # Desenhando a barra da escala de cores
    # the dimensions add_axes[left, bottom, width, height] of the new Axes
    cbar_ax = fig.add_axes([0.91, 0.16, 0.02, 0.6])
    cbar = fig.colorbar(tp, cax=cbar_ax, orientation="vertical", extend='max')
    cbar.set_label('°C', fontsize=14)
    cbar.ax.set_xticklabels(labels=cbar.ax.get_xticklabels(), weight='bold', fontsize=12)

    plt.suptitle('Previsão: Anomalia de Temperatura Máxima', fontsize=20, fontweight='bold')
    plt.tight_layout()
    plt.subplots_adjust(top=0.91, bottom=0.048, left=0.035, right=0.864, hspace=0.2, wspace=0.15)
    datei = f'{pd.to_datetime(data["time"][0].data).strftime("%d/%m/%Y")}'
    datef = f'{pd.to_datetime(data["time"][-1].data).strftime("%d/%m/%Y")}'
    plt.text(
        0.6, 2.40,
        f'GFS 25km rodada de {datei} 0000 UTC\nVálido até {datef} 1800 UTC',
        transform=ax.transAxes,
        verticalalignment='top',
        fontsize=10,
        fontweight='bold'
        )  # y -> 2.4; 0.4

    plt.savefig(filename, dpi=200)


def make_figure_reference(
        data,
        row=int,
        col=int,
        filename=str,
        area='BR',
        ):
    """function that generates the reference heatwave figure.

    Args:
        data (dataset): anomaly forecast dataset.
        row (int): Number of rows of the subplot grid.
        col (int): Number of columns of the subplot grid.
        filename (str): output filename.
        area (str): region of interest. Defaults to 'BR'.
    """

    if area == 'BR':
        lon_min, lon_max, lat_min, lat_max = (-75, -30, -35, 10)
    if area == 'area1-summer':
        lon_min, lon_max, lat_min, lat_max = (-88, -30, -52, 16)

    shapefile = dir_local + '/shape/BR_UF_2021/BR_UF_2021.shp'

    shp = gpd.read_file(shapefile)
    shp = shp[shp.NM_UF == 'Ceará']
    shp = shp.explode().iloc[0].geometry

    x, y = shp.exterior.coords.xy
    t = [[(a, s) for a, s in zip(x, y)]]

    if area == 'CE':
        fig, axarr = plt.subplots(row, col, figsize=(12, 9))
    else:
        fig, axarr = plt.subplots(row, col, figsize=(20, 10))

    lat, lon = (data.latitude.data, data.longitude.data)

    lon2d, lat2d = np.meshgrid(lon, lat)

    temp = np.array(data['t2m'][:])  # Lendo todo o tempo da variável t2m para usar o min e o max no levels

    levs = [30, 32, 34, 36, 38, 39, 40]

    jet_white = (
        '#ffe0b3',
        '#ffb84d',
        '#FF7F00',
        '#FF0000',
        '#c10000',
        '#880000'
        )

    levs = np.array(levs)

    my_cmap = ListedColormap(jet_white)
    my_cmap.set_over('#540002')
    my_cmap.set_under('#f8fa7a')

    for index, ax in enumerate(axarr.ravel()):

        if area == 'CE':
            mymap = Basemap(
                projection='cyl', llcrnrlat=-8,
                urcrnrlat=-2, llcrnrlon=-42,
                urcrnrlon=-37, ax=ax
                )
            mymap.drawmeridians(np.arange(0, 360, 1), labels=[0, 0, 0, 1], linewidth=0.01, fontsize=10)
            mymap.drawparallels(np.arange(-90, 90, 1), labels=[1, 0, 0, 0], linewidth=0.01, fontsize=10)
            mymap.readshapefile(
                f'{dir_local}/shape/i3geomap_limite_municipal/i3geomap_limite_municipal',
                'i3geomap_limite_municipal',
                color='black',
                linewidth=0.2,
                zorder=3000
                )
        else:
            mymap = Basemap(
                projection='cyl', llcrnrlat=lat_min,
                urcrnrlat=lat_max, llcrnrlon=lon_min,
                urcrnrlon=lon_max, ax=ax
                )
            mymap.drawparallels(np.arange(-60, 20, 5), labels=[1, 0, 0, 0], fontsize=12, linewidth=0.01)
            mymap.drawmeridians(np.arange(-90, 0, 10), labels=[0, 0, 0, 1], fontsize=12, linewidth=0.01)
            mymap.drawcoastlines(linewidth=0.2)

        x, y = mymap(lon2d, lat2d)

        mymap.readshapefile(f'{dir_local}/shape/BR_UF_2021/BR_UF_2021', 'BR_UF_2021', color='black', linewidth=0.9)

        tp = mymap.pcolormesh(x, y, temp[index], ax=ax, cmap=my_cmap,
                              norm=mpl.colors.BoundaryNorm(levs, ncolors=my_cmap.N, clip=False)
                              )
        if area == 'CE':
            cut2shapefile(ax, t)

        ax.set_title(str(np.array(data["time"][index].dt.strftime("%d-%m-%Y"))), fontsize=14)

    # Desenhando a barra da escala de cores
    # the dimensions add_axes[left, bottom, width, height] of the new Axes
    cbar_ax = fig.add_axes([0.91, 0.16, 0.02, 0.6])
    cbar = fig.colorbar(tp, cax=cbar_ax, orientation="vertical", extend='both')
    cbar.set_label('°C', fontsize=14)
    cbar.ax.set_xticklabels(labels=cbar.ax.get_xticklabels(), weight='bold', fontsize=12)

    plt.suptitle('Onda de Calor', fontsize=20, fontweight='bold')
    plt.tight_layout()
    plt.subplots_adjust(top=0.91, bottom=0.048, left=0.035, right=0.864, hspace=0.2, wspace=0.15)
    datei = f'{pd.to_datetime(data["time"][0].data).strftime("%d/%m/%Y")}'
    datef = f'{pd.to_datetime(data["time"][-1].data).strftime("%d/%m/%Y")}'

    plt.savefig(filename, dpi=200)
