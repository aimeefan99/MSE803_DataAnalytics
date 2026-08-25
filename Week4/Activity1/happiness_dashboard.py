"""
Week 4 Activity 1.2

This script performs the data work for the happiness dashboard:
1. Load and clean the provided World Happiness dataset.
2. Calculate dashboard summaries such as the top three happiest countries.
3. Detect potential outliers with the IQR method.
4. Generate Matplotlib and Plotly visualisations.
5. Save reusable CSV outputs for the written reports.

The written Markdown reports are maintained separately. This script does not
generate or overwrite report files.
"""

from pathlib import Path
import os
import tempfile

# Matplotlib may try to write font cache files. Setting MPLCONFIGDIR to a temp
# folder keeps the script portable in restricted or course-lab environments.
MPL_CONFIG_DIR = Path(tempfile.gettempdir()) / "mse803_matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPL_CONFIG_DIR)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "world_happiness_dataset.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
CLEANED_DATA_FILE = BASE_DIR / "cleaned_world_happiness_dataset.csv"

# Static image outputs used in the Markdown reports.
MATPLOTLIB_TOP3_FILE = OUTPUT_DIR / "matplotlib_top3_happiness.png"
MATPLOTLIB_LOWEST_FREEDOM_FILE = OUTPUT_DIR / "matplotlib_lowest_country_freedom.png"
MATPLOTLIB_TOP3_PROFILE_FILE = OUTPUT_DIR / "matplotlib_top3_indicator_profile.png"
MATPLOTLIB_CORRELATION_FILE = OUTPUT_DIR / "matplotlib_happiness_correlations.png"
MATPLOTLIB_FREEDOM_SCATTER_FILE = OUTPUT_DIR / "matplotlib_freedom_happiness_scatter.png"
MATPLOTLIB_OUTLIER_BOXPLOT_FILE = OUTPUT_DIR / "matplotlib_outlier_boxplots.png"

# Interactive HTML outputs used to demonstrate Plotly visualisation skills.
PLOTLY_TOP3_FILE = OUTPUT_DIR / "plotly_top3_happiness.html"
PLOTLY_LOWEST_FREEDOM_FILE = OUTPUT_DIR / "plotly_lowest_country_freedom.html"
PLOTLY_OUTLIER_BOXPLOT_FILE = OUTPUT_DIR / "plotly_outlier_boxplots.html"

# Columns used for cleaning, ranking, correlation, and outlier detection.
NUMERIC_COLUMNS = [
    "Happiness_Score",
    "GDP_per_Capita",
    "Social_Support",
    "Healthy_Life_Expectancy",
    "Freedom_to_Make_Choices",
    "Generosity",
    "Perceptions_of_Corruption",
]
SUPPORTING_COLUMNS = [
    "GDP_per_Capita",
    "Social_Support",
    "Healthy_Life_Expectancy",
    "Freedom_to_Make_Choices",
    "Generosity",
    "Perceptions_of_Corruption",
]
DISPLAY_LABELS = {
    "Happiness_Score": "Happiness",
    "GDP_per_Capita": "GDP",
    "Social_Support": "Social Support",
    "Healthy_Life_Expectancy": "Life Expectancy",
    "Freedom_to_Make_Choices": "Freedom",
    "Generosity": "Generosity",
    "Perceptions_of_Corruption": "Corruption",
}


def ensure_directories():
    """Create the outputs directory before writing charts or CSV files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_and_clean_data():
    """Load the source CSV and apply basic data quality preparation."""
    df = pd.read_csv(DATA_FILE)

    # Keep column and country names consistent before analysis.
    df.columns = df.columns.str.strip()
    df["Country"] = df["Country"].astype("string").str.strip()

    # Convert all metric columns to numeric values so sorting, aggregation, and
    # charting are based on numbers, not text.
    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    missing_summary = df.isna().sum().reset_index()
    missing_summary.columns = ["Column", "Missing Values"]
    duplicate_count = int(df.duplicated().sum())

    # Drop duplicate complete rows if any are found. Missing values are not
    # filled because the provided dataset is already complete after validation.
    cleaned = df.drop_duplicates().copy()
    cleaned = cleaned.dropna(subset=["Country", "Happiness_Score"])
    cleaned = cleaned.sort_values("Happiness_Score", ascending=False).reset_index(drop=True)

    return cleaned, missing_summary, duplicate_count


def get_dashboard_data(cleaned):
    """Calculate the main values required by the dashboard task."""
    top3 = cleaned.nlargest(3, "Happiness_Score").copy()
    lowest = cleaned.nsmallest(1, "Happiness_Score").iloc[0]
    return top3, lowest


def happiness_correlations(cleaned):
    # Correlation is used as descriptive association only. It does not prove
    # that a supporting indicator causes a higher or lower Happiness score.
    correlations = (
        cleaned[["Happiness_Score"] + SUPPORTING_COLUMNS]
        .corr()["Happiness_Score"]
        .drop("Happiness_Score")
        .sort_values(ascending=False)
        .reset_index()
    )
    correlations.columns = ["Indicator", "Correlation_with_Happiness"]
    return correlations


def happiness_correlation_matrix(cleaned):
    # A correlation matrix supports the heatmap view by comparing every numeric
    # indicator with every other numeric indicator, including Happiness score.
    return cleaned[NUMERIC_COLUMNS].corr()


def detect_outliers_iqr(cleaned):
    # The IQR rule follows the sample notebook: values below Q1 - 1.5 * IQR or
    # above Q3 + 1.5 * IQR are flagged as potential outliers.
    summary_rows = []
    record_rows = []

    for column in NUMERIC_COLUMNS:
        q1 = cleaned[column].quantile(0.25)
        q3 = cleaned[column].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outlier_mask = (cleaned[column] < lower_bound) | (cleaned[column] > upper_bound)
        outliers = cleaned.loc[outlier_mask, ["Country", column]]

        summary_rows.append(
            {
                "Indicator": column,
                "Q1": q1,
                "Q3": q3,
                "IQR": iqr,
                "Lower_Bound": lower_bound,
                "Upper_Bound": upper_bound,
                "Outlier_Count": int(outlier_mask.sum()),
                "Decision": "Review flagged records" if outlier_mask.any() else "Keep all records",
            }
        )

        for _, row in outliers.iterrows():
            record_rows.append(
                {
                    "Country": row["Country"],
                    "Indicator": column,
                    "Value": row[column],
                    "Lower_Bound": lower_bound,
                    "Upper_Bound": upper_bound,
                    "Decision": "Keep unless confirmed as data entry error",
                }
            )

    summary = pd.DataFrame(summary_rows)
    records = pd.DataFrame(
        record_rows,
        columns=["Country", "Indicator", "Value", "Lower_Bound", "Upper_Bound", "Decision"],
    )
    return summary, records


def build_lowest_comparison(cleaned, top3, lowest):
    """Prepare a small comparison table for the lowest-happiness country."""
    comparison = pd.concat([top3, pd.DataFrame([lowest])], ignore_index=True)
    comparison = comparison.drop_duplicates(subset=["Country"])

    average_row = {
        "Country": "Dataset Average",
        "Happiness_Score": cleaned["Happiness_Score"].mean(),
        "Freedom_to_Make_Choices": cleaned["Freedom_to_Make_Choices"].mean(),
    }
    comparison = pd.concat([comparison, pd.DataFrame([average_row])], ignore_index=True)

    max_happiness = cleaned["Happiness_Score"].max()
    comparison["Happiness_Normalised"] = comparison["Happiness_Score"] / max_happiness
    comparison["Freedom_Normalised"] = comparison["Freedom_to_Make_Choices"]
    return comparison


def create_matplotlib_top3_chart(top3):
    # A bar chart is appropriate because the task compares a numeric score
    # across categorical countries.
    plt.figure(figsize=(8, 5))
    bars = plt.bar(top3["Country"], top3["Happiness_Score"], color=["#1f77b4", "#2ca02c", "#ff7f0e"])
    plt.title("Top 3 Happiest Countries")
    plt.xlabel("Country")
    plt.ylabel("Happiness Score")
    plt.ylim(0, max(top3["Happiness_Score"]) + 1)
    plt.grid(axis="y", alpha=0.25)

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height + 0.08, f"{height:.2f}", ha="center")

    plt.tight_layout()
    plt.savefig(MATPLOTLIB_TOP3_FILE, dpi=160)
    plt.close()


def create_matplotlib_lowest_freedom_chart(comparison):
    # Compare the lowest-happiness country against the top three and the dataset
    # average. Happiness is normalised to 0-1 so it can be shown beside Freedom.
    x_positions = range(len(comparison))
    width = 0.36

    plt.figure(figsize=(10, 5.5))
    happiness_bars = plt.bar(
        [x - width / 2 for x in x_positions],
        comparison["Happiness_Normalised"],
        width,
        label="Happiness Score (normalised)",
        color="#1f77b4",
    )
    freedom_bars = plt.bar(
        [x + width / 2 for x in x_positions],
        comparison["Freedom_Normalised"],
        width,
        label="Freedom Score",
        color="#d62728",
    )
    plt.title("Lowest Happiness Country: Freedom and Happiness Context")
    plt.xlabel("Country / Benchmark")
    plt.ylabel("Score on 0-1 comparison scale")
    plt.xticks(list(x_positions), comparison["Country"], rotation=25, ha="right")
    plt.ylim(0, 1.15)
    plt.grid(axis="y", alpha=0.25)
    plt.legend()

    for bars in [happiness_bars, freedom_bars]:
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.03,
                f"{height:.2f}",
                ha="center",
                fontsize=8,
            )

    plt.tight_layout()
    plt.savefig(MATPLOTLIB_LOWEST_FREEDOM_FILE, dpi=160)
    plt.close()


def normalise_columns(df, columns):
    """Scale selected columns to 0-1 for profile comparison charts."""
    normalised = df[["Country"] + columns].copy()
    for column in columns:
        minimum = df[column].min()
        maximum = df[column].max()
        if maximum == minimum:
            normalised[column] = 0
        else:
            normalised[column] = (df[column] - minimum) / (maximum - minimum)
    return normalised


def create_matplotlib_top3_profile_chart(cleaned, top3):
    # Supporting indicators use different scales, so min-max normalisation makes
    # their profiles comparable on one chart.
    profile = normalise_columns(cleaned, SUPPORTING_COLUMNS)
    profile = profile[profile["Country"].isin(top3["Country"])]
    profile = profile.set_index("Country")[SUPPORTING_COLUMNS]

    ax = profile.T.plot(kind="bar", figsize=(11, 6), width=0.78)
    ax.set_title("Top 3 Countries: Normalised Indicator Profile")
    ax.set_xlabel("Supporting Indicator")
    ax.set_ylabel("Normalised Score")
    ax.set_ylim(0, 1.1)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(title="Country")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(MATPLOTLIB_TOP3_PROFILE_FILE, dpi=160)
    plt.close()


def create_matplotlib_correlation_heatmap(correlation_matrix):
    # A heatmap is more suitable than a bar chart when the goal is to review
    # relationships across many numeric variables at the same time.
    labels = list(correlation_matrix.columns)
    display_labels = [DISPLAY_LABELS[label] for label in labels]

    fig, ax = plt.subplots(figsize=(10, 8))
    heatmap = ax.imshow(correlation_matrix, cmap="RdYlGn", vmin=-1, vmax=1)

    ax.set_title("Correlation Heatmap: Happiness and Supporting Indicators")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(display_labels, rotation=35, ha="right")
    ax.set_yticklabels(display_labels)

    for row_index in range(len(labels)):
        for column_index in range(len(labels)):
            value = correlation_matrix.iloc[row_index, column_index]
            text_color = "white" if abs(value) >= 0.55 else "black"
            ax.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                color=text_color,
                fontsize=8,
            )

    colorbar = fig.colorbar(heatmap, ax=ax)
    colorbar.set_label("Correlation coefficient")

    fig.tight_layout()
    fig.savefig(MATPLOTLIB_CORRELATION_FILE, dpi=160)
    plt.close()


def create_matplotlib_freedom_scatter(cleaned, lowest):
    # A scatter plot is used because both variables are numeric. The lowest
    # happiness country is highlighted so it can be discussed in context.
    plt.figure(figsize=(8, 5.5))
    plt.scatter(
        cleaned["Freedom_to_Make_Choices"],
        cleaned["Happiness_Score"],
        color="#1f77b4",
        alpha=0.75,
        s=70,
    )

    plt.scatter(
        lowest["Freedom_to_Make_Choices"],
        lowest["Happiness_Score"],
        color="#d62728",
        s=130,
        edgecolor="black",
        label=f"Lowest happiness: {lowest['Country']}",
    )
    plt.text(
        lowest["Freedom_to_Make_Choices"] + 0.015,
        lowest["Happiness_Score"],
        lowest["Country"],
        va="center",
        fontsize=9,
    )

    plt.title("Freedom to Make Choices vs Happiness Score")
    plt.xlabel("Freedom to Make Choices")
    plt.ylabel("Happiness Score")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(MATPLOTLIB_FREEDOM_SCATTER_FILE, dpi=160)
    plt.close()


def create_matplotlib_outlier_boxplots(cleaned, outlier_summary):
    # Each subplot uses the original column scale and shows the actual IQR
    # lower/upper bounds. Points outside the red dashed lines are outliers.
    fig, axes = plt.subplots(3, 3, figsize=(14, 10))
    axes = axes.flatten()

    for index, column in enumerate(NUMERIC_COLUMNS):
        ax = axes[index]
        values = cleaned[column].dropna()
        bounds = outlier_summary.loc[outlier_summary["Indicator"] == column].iloc[0]
        q1 = bounds["Q1"]
        q3 = bounds["Q3"]
        lower_bound = bounds["Lower_Bound"]
        upper_bound = bounds["Upper_Bound"]
        outlier_count = int(bounds["Outlier_Count"])
        median = values.median()

        ax.boxplot(
            values,
            showmeans=True,
            patch_artist=True,
            boxprops={"facecolor": "#dbeafe", "color": "#1f2937"},
            medianprops={"color": "#f97316", "linewidth": 1.5},
            whiskerprops={"color": "#1f2937"},
            capprops={"color": "#1f2937"},
            meanprops={"marker": "^", "markerfacecolor": "#16a34a", "markeredgecolor": "#16a34a"},
        )

        offsets = pd.Series(range(len(values))).map(lambda value: (value % 5 - 2) * 0.035)
        ax.scatter(
            1 + offsets,
            values,
            color="#2563eb",
            alpha=0.65,
            s=28,
            zorder=3,
        )
        ax.axhline(lower_bound, color="#dc2626", linestyle="--", linewidth=1, label="IQR bounds")
        ax.axhline(upper_bound, color="#dc2626", linestyle="--", linewidth=1)

        y_min = min(values.min(), lower_bound)
        y_max = max(values.max(), upper_bound)
        padding = (y_max - y_min) * 0.08 if y_max > y_min else 1
        ax.set_ylim(y_min - padding, y_max + padding)
        tick_values = sorted({round(value, 2) for value in [lower_bound, q1, median, q3, upper_bound]})
        ax.set_yticks(tick_values)
        ax.set_yticklabels([f"{value:.2f}" for value in tick_values], fontsize=8)
        ax.text(
            1.18,
            upper_bound,
            f"Upper {upper_bound:.2f}",
            color="#dc2626",
            fontsize=8,
            va="bottom",
        )
        ax.text(
            1.18,
            lower_bound,
            f"Lower {lower_bound:.2f}",
            color="#dc2626",
            fontsize=8,
            va="top",
        )
        ax.set_title(f"{DISPLAY_LABELS[column]} (outliers: {outlier_count})", fontsize=10)
        ax.set_xticks([])
        ax.set_ylabel("Original value")
        ax.grid(axis="y", alpha=0.25)

    for ax in axes[len(NUMERIC_COLUMNS):]:
        ax.axis("off")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=1)
    fig.suptitle("Outlier Check with IQR Bounds", fontsize=14)
    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.savefig(MATPLOTLIB_OUTLIER_BOXPLOT_FILE, dpi=160)
    plt.close()


def create_plotly_top3_chart(top3):
    # Plotly versions provide interactive HTML views for exploration.
    fig = px.bar(
        top3,
        x="Country",
        y="Happiness_Score",
        color="Country",
        text=top3["Happiness_Score"].round(2),
        title="Interactive View: Top 3 Happiest Countries",
        labels={"Happiness_Score": "Happiness Score"},
    )
    fig.update_layout(showlegend=False, yaxis_range=[0, top3["Happiness_Score"].max() + 1])
    fig.write_html(PLOTLY_TOP3_FILE, include_plotlyjs="cdn")


def create_plotly_lowest_freedom_chart(comparison):
    # Convert the comparison table into long format for grouped bars.
    long_df = comparison.melt(
        id_vars=["Country"],
        value_vars=["Happiness_Normalised", "Freedom_Normalised"],
        var_name="Metric",
        value_name="Score",
    )
    long_df["Metric"] = long_df["Metric"].replace(
        {
            "Happiness_Normalised": "Happiness Score (normalised)",
            "Freedom_Normalised": "Freedom Score",
        }
    )

    fig = px.bar(
        long_df,
        x="Country",
        y="Score",
        color="Metric",
        barmode="group",
        text=long_df["Score"].round(2),
        title="Interactive View: Lowest Happiness Country in Context",
        labels={"Score": "Score on 0-1 comparison scale"},
    )
    fig.update_layout(yaxis_range=[0, 1.15])
    fig.write_html(PLOTLY_LOWEST_FREEDOM_FILE, include_plotlyjs="cdn")


def create_plotly_outlier_boxplots(cleaned, outlier_summary):
    # The interactive version mirrors the Matplotlib outlier chart, with hover
    # labels so the country behind each point can be identified.
    fig = make_subplots(
        rows=3,
        cols=3,
        subplot_titles=[DISPLAY_LABELS[column] for column in NUMERIC_COLUMNS],
    )

    for index, column in enumerate(NUMERIC_COLUMNS):
        row = index // 3 + 1
        col = index % 3 + 1
        values = cleaned[column]
        bounds = outlier_summary.loc[outlier_summary["Indicator"] == column].iloc[0]

        fig.add_trace(
            go.Box(
                y=values,
                name=DISPLAY_LABELS[column],
                boxmean=True,
                boxpoints="all",
                jitter=0.35,
                pointpos=0,
                text=cleaned["Country"],
                hovertemplate=(
                    "Country: %{text}<br>"
                    "Original value: %{y:.2f}<extra></extra>"
                ),
                marker={"color": "#2563eb", "opacity": 0.7},
                line={"color": "#1f2937"},
                showlegend=False,
            ),
            row=row,
            col=col,
        )
        fig.add_hline(
            y=bounds["Lower_Bound"],
            line_dash="dash",
            line_color="#dc2626",
            annotation_text=f"Lower {bounds['Lower_Bound']:.2f}",
            annotation_position="bottom right",
            row=row,
            col=col,
        )
        fig.add_hline(
            y=bounds["Upper_Bound"],
            line_dash="dash",
            line_color="#dc2626",
            annotation_text=f"Upper {bounds['Upper_Bound']:.2f}",
            annotation_position="top right",
            row=row,
            col=col,
        )
        tick_values = sorted(
            {
                round(value, 2)
                for value in [
                    bounds["Lower_Bound"],
                    bounds["Q1"],
                    values.median(),
                    bounds["Q3"],
                    bounds["Upper_Bound"],
                ]
            }
        )
        fig.update_yaxes(
            title_text="Original value",
            tickmode="array",
            tickvals=tick_values,
            ticktext=[f"{value:.2f}" for value in tick_values],
            row=row,
            col=col,
        )

    fig.update_layout(
        title="Interactive View: Outlier Check with IQR Bounds",
        height=900,
    )
    fig.write_html(PLOTLY_OUTLIER_BOXPLOT_FILE, include_plotlyjs="cdn")


def create_visualisations(cleaned, top3, lowest, correlation_matrix, outlier_summary):
    """Generate all static and interactive visualisations."""
    lowest_comparison = build_lowest_comparison(cleaned, top3, lowest)
    create_matplotlib_top3_chart(top3)
    create_matplotlib_lowest_freedom_chart(lowest_comparison)
    create_matplotlib_top3_profile_chart(cleaned, top3)
    create_matplotlib_correlation_heatmap(correlation_matrix)
    create_matplotlib_freedom_scatter(cleaned, lowest)
    create_matplotlib_outlier_boxplots(cleaned, outlier_summary)
    create_plotly_top3_chart(top3)
    create_plotly_lowest_freedom_chart(lowest_comparison)
    create_plotly_outlier_boxplots(cleaned, outlier_summary)


def save_outputs(
    cleaned,
    top3,
    lowest,
    correlations,
    correlation_matrix,
    outlier_summary,
):
    """Save cleaned data, analysis tables, and generated visualisations."""
    cleaned.to_csv(CLEANED_DATA_FILE, index=False)
    correlations.to_csv(OUTPUT_DIR / "happiness_correlations.csv", index=False)
    outlier_summary.to_csv(OUTPUT_DIR / "outlier_summary.csv", index=False)
    create_visualisations(cleaned, top3, lowest, correlation_matrix, outlier_summary)
    print(f"Analysis outputs saved to: {OUTPUT_DIR}")


def main():
    """Run the complete analysis workflow."""
    ensure_directories()
    cleaned, _, _ = load_and_clean_data()
    top3, lowest = get_dashboard_data(cleaned)
    correlations = happiness_correlations(cleaned)
    correlation_matrix = happiness_correlation_matrix(cleaned)
    outlier_summary, _ = detect_outliers_iqr(cleaned)
    save_outputs(
        cleaned,
        top3,
        lowest,
        correlations,
        correlation_matrix,
        outlier_summary,
    )


if __name__ == "__main__":
    main()
