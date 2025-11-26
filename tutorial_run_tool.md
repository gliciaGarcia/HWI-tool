# tutorial on running HWI-tool in Egeon

## 1) First step in EGEON
Log in to EGEON and set up a conda environment to run the tool's scripts.

In your terminal, write
```
ssh -X $USER@egeon-login.cptec.inpe.br
```
Attention: `$USER` is the username you received from the organization team.

## Check if the conda HWI-tool environment exists
In your terminal, write
```
conda env list
```
The following environments should appear in your terminal:
# conda environments:
#
base                     /opt/spack/opt/spack/linux-rhel8-zen2/gcc-11.2.0/anaconda3-2022.05-q74p53iarv7fk3uin3xzsgfmov7rqomj
HWI-tool              *  /pesq/share/monan/curso_OMM_INPE_2025/.conda/envs/HWI-tool
cursowmoenv2025          /pesq/share/monan/curso_OMM_INPE_2025/.conda/envs/cursowmoenv2025
cursowmoenv2025_alt      /pesq/share/monan/curso_OMM_INPE_2025/.conda/envs/cursowmoenv2025_alt
pdfview                  /pesq/share/monan/curso_OMM_INPE_2025/.conda/envs/pdfview
vtx_env                  /pesq/share/monan/curso_OMM_INPE_2025/.conda/envs/vtx_env

## If the conda environments appear
In your terminal, write
```
conda activate HWI-tool
```
---

## 2) Second step - Cloning the scripts repository
To clone the repository `HWI-tool`, which contains all the scripts for the heat wave identification tool in observation and forecasting.

### Go to your work directory:
```
cd /mnt/beegfs/$USER
```
### Clone the scripts repository:
In your terminal
```
git clone -b https://github.com/gliciaGarcia/HWI-tool.git
```

### To check if the HWI-tool folder exists
```
ls
```
click enter
The folder containing the HWI-tool name

---

### 3) Third step - Go to the scripts directory
```
cd HWI-tool
```
The main folder contains the following structure:
HWI-tool/

│

├── data/ # Input datasets (observations, forecasts, climatologies)

├── shape/ # Shapefiles used for geographic domains

└── tools/ # Python routines for heatwave detection and plotting

---

## **To identify the heat wave in ERA5 reanalysis**
In your terminal, write
```
python id_heatwaves_obs.py --date-init=20240401 --date-end=20240531 --region=BR
```
The tool will check for heatwave events in the ERA5 reanalysis for the period and region specified above.

## If a heat wave event is detected, please view it here:
```
python plot_reference_heatwave.py --date-init=20240401 --date-end=20240531 --region=BR
```
For visualization, we use the same arguments.

---

## **Heatwave Forecast Workflow**

The full forecast workflow can be executed using the shell script:
./exec_heatwaves_forecast.sh <date> <region>


### **Example**
./exec_heatwaves_forecast.sh 20220422 BR


### **Arguments**

- **`<date>`** – Forecast initialization date in **YYYYMMDD** format  
- **`<region>`** – Geographic domain (e.g., `BR`, `NEB`, `CE`, `area1-summer`)

---


