## HWI-tools
This project identifies heat waves in observation and forecasting.
The routines work in Python version 3.9.21 (It will soon be updated to the latest version.)

**Dependencies**
**Libs**

- numpy==1.26.4
- basemap==1.4.1
- pandas==2.2.3
- xarray==2023.6.0
- matplotlib==3.8.4
- shapely==2.0.6

**Folders**

- data
- shape
- tools

---

## **Project Structure**

HWI-tools/

│

├── data/ # Input datasets (observations, forecasts, climatologies)

├── shape/ # Shapefiles used for geographic domains

└── tools/ # Python routines for heatwave detection and plotting


---

## **Heatwave Forecast Workflow**

The full forecast workflow can be executed using the shell script:
./exec_heatwaves_forecast.sh <date> <region>


### **Example**
./exec_heatwaves_forecast.sh 20250115 BR


### **Arguments**

- **`<date>`** – Forecast initialization date in **YYYYMMDD** format  
- **`<region>`** – Geographic domain (e.g., `BR`, `NEB`, `CE`, `area1-summer`)

---

## **Step-by-Step Execution Description**

Below is a detailed explanation of what happens when the shell script runs.


### **1. Read input parameters**

The script reads the two user-provided arguments:

- The forecast date (`YYYYMMDD`)
- The target region for heatwave analysis

These arguments will be passed directly to each Python routine.

---

### **2. Define working directory**

The script sets the path where the Python tools are stored:
/media/glicia/glicia/curso_wmo/parte_2/HWI-tool

---

### **3. Apply bias correction**

Runs:
bias_correction.py --model='monan' --date <date>


This routine applies a bias correction method to the daily maximum temperature (Tmax) from the **MONAN** forecast model.

---

### **4. Identify heatwave events**

Runs:
id_heatwaves_fcst.py --model='monan' --region <region> --date <date>


This script:

- Computes the extreme Tmax threshold using climatology (mean + standard deviation)  
- Identifies sequences of **at least 3 consecutive days** exceeding the threshold  
- Applies spatial coverage criteria depending on the selected region

---

### **5. Generate heatwave maps**

Runs:
mapa_dias_OC_basemap.py --model='monan' --region <region> --date <date>


This routine generates forecast maps showing heatwave occurrence days using **Basemap**, with regional shapefiles overlaid.

---


## **Notes**

- All routines are currently configured for the **MONAN** model, but can be adapted for other datasets.  
- Python scripts are located in the `tools/` directory.  
- Make sure the required datasets and shapefiles are placed in the appropriate folders (`data/` and `shape/`).

---

## **Contact**

For questions, improvements, or contributions, feel free to open an issue or submit a pull request.



