import os
from datetime import timedelta
from multiprocessing import Pool

import numpy as np
import pandas as pd
from shapely.geometry import Point


def check_dir(dir):
    """ Create temporary directory where GEFS05 crude data
        is saved.
    :param dir: the directory where crede data must be saved.
    :type dir: str
    """
    if not os.path.exists(dir):
        os.makedirs(dir)


def delete_old_files(files=list, reference_time=str):
    """Função: Exclui arquivos a partir de uma determinada data.
    :param files: Lista de arquivos de uma pasta.
    :type dates: list
    :param reference_time: Data de referência para exclusão dos arquivos, ou seja,
    os arquivos com datas menores do que a data de referência serão exluídos.
    :type dir: str (format %Y%m%d)
    """
    # Remove arquivos antigos
    list_remove = []
    files_to_remove = sorted(files)
    for f in files_to_remove:
        name_data = f.split('/')[-2]
        if name_data == 'samet':
            date_file = pd.to_datetime(f.split('_')[-1].split('.')[0], format='%Y%m%d')
        else:
            date_file = pd.to_datetime(f.split('.')[-3], format='%Y%m%d')

        if date_file < pd.to_datetime(reference_time):
            if name_data == 'gfs':
                list_remove.append(f)
            else:
                os.remove(f)
    return list_remove


# Parallel mode
def check_contains(args):
    i, j, lon, lat, polygon = args
    point = Point(lon, lat)
    return (i, j, polygon.contains(point))


def mask_from_shape(polygon, longitude, latitude):

    mask = np.empty((len(longitude), len(latitude)), dtype=bool)

    # Create a list of arguments for the check_contains function
    args_list = [(i, j, lon, lat, polygon) for i, lon in enumerate(longitude)
                 for j, lat in enumerate(latitude)]

    # Use a pool of workers to check the contains condition in parallel
    with Pool() as pool:
        results = pool.map(check_contains, args_list)

    # Assign the results to the mask array
    for i, j, contains in results:
        mask[i, j] = contains

    return mask.T


def split_dates_by_sequence(dates):
    # Sort the dates in ascending order
    sorted_dates = sorted(dates)

    # Initialize variables
    result = []
    current_sequence = [sorted_dates[0]]

    # Iterate through the sorted dates
    for i in range(1, len(sorted_dates)):
        current_date = sorted_dates[i]
        previous_date = sorted_dates[i - 1]

        # Check if the current date is in the same sequence as the previous date
        if current_date == previous_date + timedelta(days=1):
            current_sequence.append(current_date)
        else:
            result.append(current_sequence)
            current_sequence = [current_date]

    # Add the last sequence to the result
    result.append(current_sequence)

    return result


# Função para eliminar os índices do time com abrangência menor que 25% do total de pontos válidos
def split_list(mylist):
    # Calculando as diferenças
    d = np.diff(mylist)
    # Quando as diferenças não são 1, salve esta informação
    # Precisamos a +1 para compensar o elemento perdido
    breaks = list(np.arange(len(mylist) - 1)[d != 1] + 1)
    slices = zip([0] + breaks, breaks + [len(mylist)])
    # fatia as listas
    int_list = [mylist[a:b] for a, b in slices]
    filter = [int_list[idx] for idx in range(0, len(int_list))
              if len(int_list[idx]) > 2]  # tirar as listas menores que 3

    return list(filter)
