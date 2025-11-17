#!/bin/bash
# Author: [Glícia R. G. Araújo]
# Date: 2024-10-01
# Description: This script will run the necessary scripts to perform the heat wave forecast.
# Usage: ./exec_heatwaves_forecast.sh <date> <region>
# Example: ./exec_heatwaves_forecast.sh YYYYMMDD BR

inicio=$(date +%s)

today=$(date +%Y%m%d)

date=$1  # YYYYMMDD
region=$2  # area1-summer or BR or NEB or CE

path_local='/media/glicia/glicia/curso_wmo/parte_2/HWI-tool'

################################# Heatwave Forecast ##########################################

echo
echo "Applying bias correction to model data"
python $path_local/bias_correction.py --model='monan' --date $date

echo
echo "Identifying extreme Tmax based on the Tmax climatology + Tmax std; a minimum of 3 consecutive days; area coverage"
python $path_local/id_heatwaves_fcst.py --model='monan' --region $region --date $date


echo
echo "Create heatwave forecast figures"
python $path_local/mapa_dias_OC_basemap.py --model='monan' --region $region --date $date

#python $path_local/plot_reference_heatwave.py --date-init $date_i --date-end $date_f --region $region

fim=$(date +%s)
duracao=$((fim - inicio))

minutos=$((duracao / 60))
segundos=$((duracao % 60))

echo "Time Duration:" $minutos":"$segundos"s"
echo
echo "END OF EXECUTION!"