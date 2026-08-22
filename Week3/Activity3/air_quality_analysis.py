from pathlib import Path
import os
from string import Template
import tempfile

MPL_CONFIG_DIR = Path(tempfile.gettempdir()) / "mse803_matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPL_CONFIG_DIR)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "rawdata"
OUTPUT_DIR = BASE_DIR / "outputs"

REPORT_TEMPLATE_FILE = BASE_DIR / "report_template.md"
REPORT_FILE = BASE_DIR / "analysis_report.md"

COMBINED_CLEANED_FILE = OUTPUT_DIR / "beijing_air_quality_cleaned_sample.csv"
MISSING_SUMMARY_FILE = OUTPUT_DIR / "missing_values_summary.csv"
DESCRIPTIVE_STATS_FILE = OUTPUT_DIR / "descriptive_statistics.csv"
CORRELATION_FILE = OUTPUT_DIR / "correlation_matrix.csv"
STATION_SUMMARY_FILE = OUTPUT_DIR / "station_pm25_summary.csv"
MONTHLY_SUMMARY_FILE = OUTPUT_DIR / "monthly_pm25_summary.csv"

MONTHLY_TREND_PLOT = OUTPUT_DIR / "monthly_pm25_trend.png"
STATION_PM25_PLOT = OUTPUT_DIR / "station_pm25_mean.png"
CORRELATION_HEATMAP_PLOT = OUTPUT_DIR / "correlation_heatmap.png"
PM25_PM10_SCATTER_PLOT = OUTPUT_DIR / "pm25_pm10_scatter.png"

NUMERIC_COLUMNS = [
    "PM2.5",
    "PM10",
    "SO2",
    "NO2",
    "CO",
    "O3",
    "TEMP",
    "PRES",
    "DEWP",
    "RAIN",
    "WSPM",
]


def ensure_directories():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def find_air_quality_files():
    csv_files = sorted(RAW_DIR.rglob("PRSA_Data_*.csv"))
    if not csv_files:
        raise SystemExit(
            "No PRSA_Data_*.csv files were found. Download and extract the UCI "
            f"Beijing air-quality dataset, place the extracted CSV files in {RAW_DIR}, "
            "and run the script again."
        )
    return csv_files


def load_raw_dataset():
    # The raw UCI zip is downloaded and extracted manually before running this
    # script. This script reads the extracted station-level CSV files directly.
    csv_files = find_air_quality_files()
    frames = []
    for file_path in csv_files:
        frames.append(pd.read_csv(file_path))
    return pd.concat(frames, ignore_index=True)


def prepare_dataset(df):
    required_columns = {"year", "month", "day", "hour", "station"}
    missing_required = required_columns - set(df.columns)
    if missing_required:
        raise SystemExit(
            "The loaded dataset does not contain the expected Beijing air-quality "
            f"columns: {', '.join(sorted(missing_required))}"
        )

    df["datetime"] = pd.to_datetime(
        df[["year", "month", "day", "hour"]],
        errors="coerce",
    )

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["station"] = df["station"].astype("string").str.strip()
    df["wd"] = df["wd"].astype("string").str.strip()
    return df


def clean_dataset(df):
    cleaned = df.sort_values(["station", "datetime"]).copy()

    # Interpolate numeric gaps within each monitoring station. Remaining gaps
    # are filled with station medians, then overall medians as a final fallback.
    cleaned[NUMERIC_COLUMNS] = cleaned.groupby("station")[NUMERIC_COLUMNS].transform(
        lambda group: group.interpolate(limit_direction="both")
    )
    station_medians = cleaned.groupby("station")[NUMERIC_COLUMNS].transform("median")
    cleaned[NUMERIC_COLUMNS] = cleaned[NUMERIC_COLUMNS].fillna(station_medians)
    cleaned[NUMERIC_COLUMNS] = cleaned[NUMERIC_COLUMNS].fillna(
        cleaned[NUMERIC_COLUMNS].median()
    )

    # Wind direction is categorical, so use each station's most frequent value.
    station_wd_mode = cleaned.groupby("station")["wd"].transform(
        lambda group: group.mode().iloc[0] if not group.mode().empty else pd.NA
    )
    cleaned["wd"] = cleaned["wd"].fillna(station_wd_mode).fillna("Unknown")

    return cleaned


def missing_summary(raw_df, cleaned_df):
    # Summarise data quality by comparing missing values before and after
    # cleaning. This supports the data-cleaning part of the project.
    summary = pd.DataFrame(
        {
            "Missing Before Cleaning": raw_df.isna().sum(),
            "Missing After Cleaning": cleaned_df.isna().sum(),
        }
    )
    summary["Missing Reduction"] = (
        summary["Missing Before Cleaning"] - summary["Missing After Cleaning"]
    )
    return summary.reset_index().rename(columns={"index": "Column"})


def descriptive_statistics(cleaned_df):
    # Calculate univariate descriptive statistics: central tendency, spread,
    # and range for each numeric air-quality and weather variable.
    stats = cleaned_df[NUMERIC_COLUMNS].agg(["count", "mean", "median", "var", "std", "min", "max"])
    return stats.T.reset_index().rename(columns={"index": "Variable"})


def correlation_matrix(cleaned_df):
    # Calculate bivariate relationships between numeric variables.
    # Correlation describes association only, not causation.
    return cleaned_df[NUMERIC_COLUMNS].corr()


def station_summary(cleaned_df):
    # Compare PM2.5 levels across monitoring stations to show spatial variation
    # in air quality across Beijing.
    summary = (
        cleaned_df.groupby("station")
        .agg(
            PM25_Mean=("PM2.5", "mean"),
            PM25_Median=("PM2.5", "median"),
            PM25_Std=("PM2.5", "std"),
            PM10_Mean=("PM10", "mean"),
            NO2_Mean=("NO2", "mean"),
            Record_Count=("PM2.5", "count"),
        )
        .sort_values("PM25_Mean", ascending=False)
        .reset_index()
    )
    return summary


def monthly_summary(cleaned_df):
    # Aggregate hourly records into monthly averages so long-term patterns and
    # seasonal changes can be analysed.
    monthly = cleaned_df.copy()
    monthly["Month"] = monthly["datetime"].dt.to_period("M").astype(str)
    return (
        monthly.groupby("Month")
        .agg(PM25_Mean=("PM2.5", "mean"), PM10_Mean=("PM10", "mean"), O3_Mean=("O3", "mean"))
        .reset_index()
    )


def confidence_interval(series):
    # Estimate a 95% confidence interval for the population mean using the
    # sample mean and sample standard deviation.
    values = series.dropna().to_numpy(dtype=float)
    mean = values.mean()
    std = values.std(ddof=1)
    margin = 1.96 * std / np.sqrt(len(values))
    return mean, mean - margin, mean + margin


def plot_monthly_pm25(monthly_df):
    # Visualise the time trend of monthly PM2.5 averages.
    plt.figure(figsize=(12, 6))
    plt.plot(monthly_df["Month"], monthly_df["PM25_Mean"], color="#1f77b4", linewidth=2)
    plt.title("Monthly Average PM2.5 Across Beijing Monitoring Sites")
    plt.xlabel("Month")
    plt.ylabel("Average PM2.5")
    plt.xticks(monthly_df["Month"][::6], rotation=45, ha="right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(MONTHLY_TREND_PLOT, dpi=160)
    plt.close()


def plot_station_pm25(station_df):
    # Visualise station-level differences in average PM2.5.
    plt.figure(figsize=(10, 6))
    plt.bar(station_df["station"], station_df["PM25_Mean"], color="#2ca02c")
    plt.title("Average PM2.5 by Monitoring Station")
    plt.xlabel("Station")
    plt.ylabel("Average PM2.5")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(STATION_PM25_PLOT, dpi=160)
    plt.close()


def plot_correlation_heatmap(corr_df):
    # Visualise the correlation matrix to make strong positive and negative
    # associations easier to identify.
    plt.figure(figsize=(9, 7))
    image = plt.imshow(corr_df, cmap="coolwarm", vmin=-1, vmax=1)
    plt.colorbar(image, fraction=0.046, pad=0.04)
    plt.xticks(range(len(corr_df.columns)), corr_df.columns, rotation=45, ha="right")
    plt.yticks(range(len(corr_df.index)), corr_df.index)
    plt.title("Correlation Matrix for Air Quality and Weather Variables")

    for row_index, row_name in enumerate(corr_df.index):
        for column_index, column_name in enumerate(corr_df.columns):
            value = corr_df.loc[row_name, column_name]
            plt.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=7,
            )

    plt.tight_layout()
    plt.savefig(CORRELATION_HEATMAP_PLOT, dpi=160)
    plt.close()


def plot_pm25_pm10_scatter(cleaned_df):
    # Plot a sample of observations to show the relationship between PM10 and
    # PM2.5 without overloading the figure with all 420,768 records.
    sample = cleaned_df.sample(n=min(5000, len(cleaned_df)), random_state=42)
    plt.figure(figsize=(8, 6))
    plt.scatter(sample["PM10"], sample["PM2.5"], alpha=0.2, s=8, color="#9467bd")
    plt.title("PM2.5 vs PM10")
    plt.xlabel("PM10")
    plt.ylabel("PM2.5")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(PM25_PM10_SCATTER_PLOT, dpi=160)
    plt.close()


def create_charts(cleaned_df, station_df, monthly_df, corr_df):
    plot_monthly_pm25(monthly_df)
    plot_station_pm25(station_df)
    plot_correlation_heatmap(corr_df)
    plot_pm25_pm10_scatter(cleaned_df)


def format_number(value):
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{value:,.2f}"
    return str(value)


def markdown_table(df, numeric_columns=None, max_rows=None):
    numeric_columns = set(numeric_columns or [])
    table = df.head(max_rows).copy() if max_rows else df.copy()

    for column in table.columns:
        if column in numeric_columns:
            table[column] = table[column].map(format_number)
        else:
            table[column] = table[column].map(lambda value: "" if pd.isna(value) else str(value))

    lines = [
        "| " + " | ".join(table.columns) + " |",
        "| " + " | ".join(["---"] * len(table.columns)) + " |",
    ]
    for _, row in table.iterrows():
        lines.append("| " + " | ".join(row.astype(str)) + " |")
    return "\n".join(lines)


def build_report(raw_df, cleaned_df, missing_df, stats_df, corr_df, station_df, monthly_df):
    # Fill the markdown template with computed tables and key findings.
    pm25_mean, pm25_ci_low, pm25_ci_high = confidence_interval(cleaned_df["PM2.5"])
    strongest_pm25_corr = (
        corr_df["PM2.5"]
        .drop(labels=["PM2.5"])
        .abs()
        .sort_values(ascending=False)
        .index[0]
    )
    strongest_pm25_corr_value = corr_df.loc["PM2.5", strongest_pm25_corr]
    highest_station = station_df.iloc[0]
    lowest_station = station_df.iloc[-1]

    template = Template(REPORT_TEMPLATE_FILE.read_text(encoding="utf-8"))
    return template.substitute(
        row_count=f"{len(raw_df):,}",
        cleaned_row_count=f"{len(cleaned_df):,}",
        station_count=cleaned_df["station"].nunique(),
        start_date=cleaned_df["datetime"].min().strftime("%Y-%m-%d"),
        end_date=cleaned_df["datetime"].max().strftime("%Y-%m-%d"),
        missing_summary_table=markdown_table(
            missing_df,
            ["Missing Before Cleaning", "Missing After Cleaning", "Missing Reduction"],
        ),
        descriptive_stats_table=markdown_table(
            stats_df,
            ["count", "mean", "median", "var", "std", "min", "max"],
        ),
        station_summary_table=markdown_table(
            station_df,
            ["PM25_Mean", "PM25_Median", "PM25_Std", "PM10_Mean", "NO2_Mean", "Record_Count"],
        ),
        monthly_summary_table=markdown_table(
            monthly_df.tail(12),
            ["PM25_Mean", "PM10_Mean", "O3_Mean"],
        ),
        correlation_table=markdown_table(
            corr_df.reset_index().rename(columns={"index": "Variable"}),
            NUMERIC_COLUMNS,
        ),
        pm25_mean=f"{pm25_mean:,.2f}",
        pm25_ci_low=f"{pm25_ci_low:,.2f}",
        pm25_ci_high=f"{pm25_ci_high:,.2f}",
        strongest_pm25_corr=strongest_pm25_corr,
        strongest_pm25_corr_value=f"{strongest_pm25_corr_value:.2f}",
        highest_station=highest_station["station"],
        highest_station_pm25=f"{highest_station['PM25_Mean']:,.2f}",
        lowest_station=lowest_station["station"],
        lowest_station_pm25=f"{lowest_station['PM25_Mean']:,.2f}",
    )


def save_outputs(raw_df, cleaned_df, missing_df, stats_df, corr_df, station_df, monthly_df):
    # Save the summary outputs used in the report. The cleaned sample is limited
    # to keep the repository size reasonable while preserving a reproducible view.
    cleaned_df.head(5000).to_csv(COMBINED_CLEANED_FILE, index=False)
    missing_df.to_csv(MISSING_SUMMARY_FILE, index=False)
    stats_df.to_csv(DESCRIPTIVE_STATS_FILE, index=False)
    corr_df.to_csv(CORRELATION_FILE)
    station_df.to_csv(STATION_SUMMARY_FILE, index=False)
    monthly_df.to_csv(MONTHLY_SUMMARY_FILE, index=False)

    create_charts(cleaned_df, station_df, monthly_df, corr_df)

    report = build_report(raw_df, cleaned_df, missing_df, stats_df, corr_df, station_df, monthly_df)
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(report)


def main():
    ensure_directories()

    raw_df = prepare_dataset(load_raw_dataset())
    cleaned_df = clean_dataset(raw_df)

    missing_df = missing_summary(raw_df, cleaned_df)
    stats_df = descriptive_statistics(cleaned_df)
    corr_df = correlation_matrix(cleaned_df)
    station_df = station_summary(cleaned_df)
    monthly_df = monthly_summary(cleaned_df)

    save_outputs(raw_df, cleaned_df, missing_df, stats_df, corr_df, station_df, monthly_df)


if __name__ == "__main__":
    main()
