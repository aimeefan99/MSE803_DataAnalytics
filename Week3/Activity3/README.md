# Week 3 - Activity 3: Beijing Multi-Site Air Quality Statistical Analysis

This activity develops a statistical data analysis project using the Beijing Multi-Site Air Quality dataset from the UCI Machine Learning Repository.

## Files

- `Week_2_Statistical Analytics.pptx`: lecture notes supplied for the activity
- `air_quality_analysis.py`: reproducible analysis script
- `report_template.md`: markdown template used to generate the report
- `analysis_report.md`: generated statistical analysis report
- `requirements.txt`: Python packages required to run the script
- `outputs/`: generated CSV summaries and charts
- `data/raw/`: optional fallback location for the downloaded UCI zip file or extracted raw CSV files

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

The script loads the dataset from UCI using:

```python
fetch_ucirepo(id=501)
```

If the UCI package reports that this dataset is not available for import, the script will automatically try the official UCI zip file URL:

```text
https://archive.ics.uci.edu/static/public/501/beijing+multi+site+air+quality+data.zip
```

If automatic downloading is blocked, manually download the zip file and place it in:

```text
Week3/Activity3/data/raw/
```

Run the script again after placing the file there.

## Analysis Included

- Missing value summary before and after cleaning
- Descriptive statistics for pollutant and weather variables
- Station-level PM2.5 comparison
- Monthly PM2.5 trend
- Correlation matrix
- PM2.5 vs PM10 scatter plot
- 95% confidence interval for mean PM2.5

The final written analysis is generated in `analysis_report.md`.
