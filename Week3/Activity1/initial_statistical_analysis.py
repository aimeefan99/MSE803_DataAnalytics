from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "Sample_dataset.csv"
CLEANED_FILE = BASE_DIR / "cleaned_dataset.csv"
RESULTS_FILE = BASE_DIR / "analysis_results.md"

NUMERIC_COLUMNS = ["Age", "Net worth", "Salary"]
TEXT_NUMBER_FIXES = {
    "thirty-eight": "38",
    "sixty five thousand": "65000",
}


def clean_numeric_column(series):
    cleaned = (
        series.astype("string")
        .str.strip()
        .str.lower()
        .replace(TEXT_NUMBER_FIXES)
        .str.replace(",", "", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def first_valid(series):
    valid_values = series.dropna()
    return valid_values.iloc[0] if not valid_values.empty else pd.NA


def clean_join_date_column(series):
    cleaned = series.astype("string").str.strip()
    parsed_dates = pd.Series(pd.NA, index=series.index, dtype="string")

    slash_dates = cleaned.str.contains("/", na=False)
    dash_dates = cleaned.str.contains("-", na=False)

    parsed_slash_dates = pd.to_datetime(
        cleaned.loc[slash_dates], format="%d/%m/%Y", errors="coerce"
    )
    parsed_dates.loc[slash_dates] = parsed_slash_dates.dt.strftime("%d/%m/%Y")

    corrected_dash_dates = cleaned.loc[dash_dates].replace({"2019-13-01": "2019-01-13"})
    parsed_dash_dates = pd.to_datetime(
        corrected_dash_dates, format="%Y-%m-%d", errors="coerce"
    )
    parsed_dates.loc[dash_dates] = parsed_dash_dates.dt.strftime("%d/%m/%Y")

    return parsed_dates


def clean_data(df):
    cleaned = df.copy()
    cleaned["Original Row"] = range(1, len(cleaned) + 1)

    missing_id_count = cleaned["ID"].isna().sum()
    cleaned["ID"] = pd.to_numeric(cleaned["ID"], errors="coerce")
    cleaned["Record Key"] = cleaned["ID"].astype("Int64").astype("string")
    missing_id_mask = cleaned["ID"].isna()
    cleaned.loc[missing_id_mask, "Record Key"] = (
        "MissingID_Row_" + cleaned.loc[missing_id_mask, "Original Row"].astype(str)
    )
    cleaned["ID"] = cleaned["ID"].astype("Int64")

    cleaned["Name"] = cleaned["Name"].astype("string").str.strip().replace("", pd.NA)
    cleaned["Country"] = (
        cleaned["Country"]
        .astype("string")
        .str.strip()
        .str.upper()
        .replace({"AU": "AUS", "": pd.NA})
    )

    for column in NUMERIC_COLUMNS:
        cleaned[column] = clean_numeric_column(cleaned[column])

    cleaned["Join Date"] = clean_join_date_column(cleaned["Join Date"])

    duplicate_id_rows = cleaned[cleaned["ID"].notna()].duplicated("ID", keep=False).sum()
    cleaned = (
        cleaned.sort_values(["ID", "Original Row"], na_position="last")
        .groupby("Record Key", as_index=False)
        .agg(
            {
                "ID": first_valid,
                "Name": first_valid,
                "Age": first_valid,
                "Net worth": first_valid,
                "Country": first_valid,
                "Salary": first_valid,
                "Join Date": first_valid,
                "Original Row": "min",
            }
        )
        .drop(columns=["Record Key"])
        .sort_values(["ID", "Original Row"], na_position="last")
        .reset_index(drop=True)
    )

    cleaned["Name"] = cleaned["Name"].fillna("Unknown")
    cleaned["Country"] = cleaned["Country"].fillna("Unknown")
    return cleaned, int(missing_id_count), int(duplicate_id_rows)


def required_metrics(df):
    rows = []
    for column in NUMERIC_COLUMNS:
        values = df[column].to_numpy(dtype=float)
        rows.append(
            {
                "Variable": column,
                "Mean": np.nanmean(values),
                "Sample Variance": np.nanvar(values, ddof=1),
                "Sample Standard Deviation": np.nanstd(values, ddof=1),
            }
        )
    return pd.DataFrame(rows).set_index("Variable")


def pairwise_covariance(df):
    rows = []
    for left, right in [("Age", "Net worth"), ("Age", "Salary"), ("Net worth", "Salary")]:
        pair_data = df[[left, right]].dropna()
        covariance = np.cov(pair_data[left], pair_data[right], ddof=1)[0, 1]
        rows.append(
            {
                "Variable Pair": f"{left} vs {right}",
                "Pair Count": len(pair_data),
                "Sample Covariance": covariance,
            }
        )
    return pd.DataFrame(rows).set_index("Variables")


def format_report_table(df):
    table = df.reset_index()
    formatted = table.copy()

    for column in formatted.columns:
        formatted[column] = formatted[column].map(
            lambda value: f"{value:,.2f}" if isinstance(value, float) else str(value)
        )

    headers = list(formatted.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in formatted.iterrows():
        lines.append("| " + " | ".join(row.astype(str)) + " |")
    return "\n".join(lines)


def build_report(raw_df, cleaned_df, missing_id_count, duplicate_id_rows):
    metrics_table = required_metrics(cleaned_df)
    covariance_table = pairwise_covariance(cleaned_df)

    return f"""# Week 3 - Activity 1: Initial Statistical Analysis

## Dataset

Source file: {DATA_FILE.name}
Original records: {len(raw_df)}
Cleaned records used for analysis: {len(cleaned_df)}

## Data Cleaning Summary

Raw missing values by column:
```text
{raw_df.isna().sum().to_string()}
```

Rows removed because ID is missing: 0
Rows retained with missing ID: {missing_id_count}
Duplicate ID rows involved in merge: {duplicate_id_rows}

Cleaning decisions:
- Kept rows with missing ID when their analytical fields were still useful.
- Merged duplicate records with the same ID when values were complementary.
- Converted Age, Net worth, and Salary to numeric values.
- Removed thousands separators from numeric values, for example 30,000.
- Converted simple text numbers, for example thirty-eight and sixty five thousand.
- Kept missing numeric values as NaN and ignored them in statistical calculations.
- Standardised country values by converting AU to AUS and empty country values to Unknown.
- Parsed valid join dates and corrected Eve's date from 2019-13-01 to 13/01/2019.

## Cleaned Dataset

```text
{cleaned_df.to_string(index=False)}
```

## Required Statistical Metrics

{format_report_table(metrics_table)}

## Sample Covariance Between Variables

{format_report_table(covariance_table)}

## Metric Explanations

**Mean**

The arithmetic average. It describes the central value of a variable, but it can be affected by very high or very low values.

**Sample Variance**

The average squared distance from the mean. A larger variance means the values are more spread out.

**Sample Standard Deviation**

The square root of sample variance. It is easier to interpret than variance because it uses the same unit as the original variable.

**Sample Covariance**

Measures whether two variables tend to move together. A positive covariance means both variables tend to increase together. A negative covariance means one tends to increase when the other decreases. A value near zero suggests little linear co-movement.

## Population vs Sample

This dataset is treated as a sample, not a full population. The mean is the same for population and sample calculations.

## Library Usage

Pandas was used to load, clean, and structure the dataset. NumPy was used for the statistical calculations required by the activity: mean, variance, standard deviation, and covariance.
"""


def main():
    raw_df = pd.read_csv(DATA_FILE)
    cleaned_df, missing_id_count, duplicate_id_rows = clean_data(raw_df)

    cleaned_df.to_csv(CLEANED_FILE, index=False)
    report = build_report(raw_df, cleaned_df, missing_id_count, duplicate_id_rows)
    RESULTS_FILE.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
