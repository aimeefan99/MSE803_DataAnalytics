# Week 3 - Activity 3: Beijing Multi-Site Air Quality Statistical Analysis

This activity develops a statistical data analysis project using the Beijing Multi-Site Air Quality dataset from the UCI Machine Learning Repository.

## Files

- `Week_2_Statistical Analytics.pptx`: lecture notes supplied for the activity
- `air_quality_analysis.py`: reproducible analysis script
- `report_template.md`: markdown template used to generate the report
- `analysis_report.md`: generated statistical analysis report
- `requirements.txt`: Python packages required to run the script
- `outputs/`: generated CSV summaries and charts
- `rawdata/`: location for the manually downloaded and extracted raw CSV files

## How to Run

Activate the course conda environment first:

```bash
conda activate 803env
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the analysis from inside `Week3/Activity3`:

```bash
python air_quality_analysis.py
```

Before running the script, manually download the dataset from:

```text
https://archive.ics.uci.edu/static/public/501/beijing+multi+site+air+quality+data.zip
```

Extract the zip file until the station-level CSV files are available, then place those extracted files under:

```text
Week3/Activity3/rawdata/
```

The script reads `PRSA_Data_*.csv` files from `rawdata/` and then generates the report and outputs.

## Analysis Included

- Missing value summary before and after cleaning
- Descriptive statistics for pollutant and weather variables
- Station-level PM2.5 comparison
- Monthly PM2.5 trend
- Correlation matrix
- PM2.5 vs PM10 scatter plot
- 95% confidence interval for mean PM2.5

The final written analysis is generated in `analysis_report.md`.
