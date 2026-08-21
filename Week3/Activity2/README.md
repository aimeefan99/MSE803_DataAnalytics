# Week 3 - Activity 2: Data Cleaning Prediction for Missing Value

This activity continues the Week 3 Activity 1 data cleaning work by predicting missing values where enough supporting data is available.

## Files

- `missing_value_prediction.py`: prediction script
- `report_template.md`: markdown template used to generate the report
- `nonlinear regression -sample code.py`: supplied polynomial regression sample code
- `prediction_results.md`: generated report comparing linear and polynomial regression
- `missing_value_predictions.csv`: generated prediction and validation metrics
- `completed_dataset.csv`: generated dataset with selected predictions applied
- `david_net_worth_regression.png`: generated linear vs polynomial comparison chart
- `grace_country_regression.png`: generated linear vs polynomial comparison chart
- `requirements.txt`: Python packages required to run the script

## Missing Values Predicted

- David's missing `Net worth`
- Grace's missing `Country`

Heidi is not predicted because too many fields are missing from her record, so there are not enough reliable input features for regression.

## How to Run

Activate the course conda environment first:

```bash
conda activate 803env
```

From the repository root:

```bash
python -m pip install -r Week3/Activity2/requirements.txt
python Week3/Activity2/missing_value_prediction.py
```

Or from inside `Week3/Activity2`:

```bash
python -m pip install -r requirements.txt
python missing_value_prediction.py
```

The script reads `Week3/Activity1/cleaned_dataset.csv` and writes the Activity 2 outputs into `Week3/Activity2`.
