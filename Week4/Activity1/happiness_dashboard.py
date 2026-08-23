from pathlib import Path
from string import Template
import os
import tempfile

MPL_CONFIG_DIR = Path(tempfile.gettempdir()) / "mse803_matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPL_CONFIG_DIR)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "world_happiness_dataset.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
REPORT_TEMPLATE_FILE = BASE_DIR / "report_template.md"
REPORT_FILE = BASE_DIR / "dashboard_report.md"
CLEANED_DATA_FILE = BASE_DIR / "cleaned_world_happiness_dataset.csv"

MATPLOTLIB_TOP3_FILE = OUTPUT_DIR / "matplotlib_top3_happiness.png"
MATPLOTLIB_LOWEST_FREEDOM_FILE = OUTPUT_DIR / "matplotlib_lowest_country_freedom.png"
MATPLOTLIB_TOP3_PROFILE_FILE = OUTPUT_DIR / "matplotlib_top3_indicator_profile.png"
MATPLOTLIB_CORRELATION_FILE = OUTPUT_DIR / "matplotlib_happiness_correlations.png"
MATPLOTLIB_FREEDOM_SCATTER_FILE = OUTPUT_DIR / "matplotlib_freedom_happiness_scatter.png"
PLOTLY_TOP3_FILE = OUTPUT_DIR / "plotly_top3_happiness.html"
PLOTLY_LOWEST_FREEDOM_FILE = OUTPUT_DIR / "plotly_lowest_country_freedom.html"
PLOTLY_RELATIONSHIP_FILE = OUTPUT_DIR / "plotly_happiness_freedom_relationship.html"
PLOTLY_CORRELATION_FILE = OUTPUT_DIR / "plotly_happiness_correlations.html"

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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_and_clean_data():
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
    top3 = cleaned.nlargest(3, "Happiness_Score").copy()
    lowest = cleaned.nsmallest(1, "Happiness_Score").iloc[0]
    freedom_average = cleaned["Freedom_to_Make_Choices"].mean()
    return top3, lowest, freedom_average


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


def build_lowest_comparison(cleaned, top3, lowest):
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


def create_plotly_top3_chart(top3):
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


def create_plotly_relationship_chart(cleaned):
    fig = px.scatter(
        cleaned,
        x="Freedom_to_Make_Choices",
        y="Happiness_Score",
        size="GDP_per_Capita",
        color="Social_Support",
        hover_name="Country",
        hover_data={
            "GDP_per_Capita": ":.2f",
            "Social_Support": ":.2f",
            "Healthy_Life_Expectancy": ":.1f",
            "Generosity": ":.2f",
            "Perceptions_of_Corruption": ":.2f",
        },
        title="Interactive View: Happiness Score and Supporting Indicators",
        labels={
            "Freedom_to_Make_Choices": "Freedom to Make Choices",
            "Happiness_Score": "Happiness Score",
            "GDP_per_Capita": "GDP per Capita",
            "Social_Support": "Social Support",
        },
    )
    fig.update_layout(coloraxis_colorbar_title="Social Support")
    fig.write_html(PLOTLY_RELATIONSHIP_FILE, include_plotlyjs="cdn")


def create_plotly_correlation_heatmap(correlation_matrix):
    labels = list(correlation_matrix.columns)
    display_labels = [DISPLAY_LABELS[label] for label in labels]
    values = correlation_matrix.round(2).values

    fig = go.Figure(
        data=go.Heatmap(
            z=values,
            x=display_labels,
            y=display_labels,
            colorscale="RdYlGn",
            zmin=-1,
            zmax=1,
            text=values,
            customdata=[
                [[row_label, column_label] for column_label in labels]
                for row_label in labels
            ],
            texttemplate="%{text:.2f}",
            colorbar={"title": "Correlation"},
            hovertemplate=(
                "%{customdata[0]} vs %{customdata[1]}"
                "<br>Correlation: %{z:.2f}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title="Interactive View: Correlation Heatmap",
        xaxis_title="Numeric Indicator",
        yaxis_title="Numeric Indicator",
        xaxis={"tickangle": -45},
    )
    fig.write_html(PLOTLY_CORRELATION_FILE, include_plotlyjs="cdn")


def create_visualisations(cleaned, top3, lowest, correlation_matrix):
    lowest_comparison = build_lowest_comparison(cleaned, top3, lowest)
    create_matplotlib_top3_chart(top3)
    create_matplotlib_lowest_freedom_chart(lowest_comparison)
    create_matplotlib_top3_profile_chart(cleaned, top3)
    create_matplotlib_correlation_heatmap(correlation_matrix)
    create_matplotlib_freedom_scatter(cleaned, lowest)
    create_plotly_top3_chart(top3)
    create_plotly_lowest_freedom_chart(lowest_comparison)
    create_plotly_relationship_chart(cleaned)
    create_plotly_correlation_heatmap(correlation_matrix)


def markdown_table(df, numeric_columns=None):
    numeric_columns = set(numeric_columns or [])
    table = df.copy()

    for column in table.columns:
        if column in numeric_columns:
            table[column] = table[column].map(lambda value: f"{value:.2f}")
        else:
            table[column] = table[column].astype(str)

    lines = [
        "| " + " | ".join(table.columns) + " |",
        "| " + " | ".join(["---"] * len(table.columns)) + " |",
    ]
    for _, row in table.iterrows():
        lines.append("| " + " | ".join(row.astype(str)) + " |")
    return "\n".join(lines)


def build_report(cleaned, missing_summary, duplicate_count, top3, lowest, freedom_average, correlations):
    top3_table = top3[["Country", "Happiness_Score", "Freedom_to_Make_Choices"]]
    lowest_table = pd.DataFrame([lowest])[
        ["Country", "Happiness_Score", "Freedom_to_Make_Choices"]
    ]
    lowest_comparison = build_lowest_comparison(cleaned, top3, lowest)
    lowest_comparison_table = lowest_comparison[
        [
            "Country",
            "Happiness_Score",
            "Freedom_to_Make_Choices",
            "Happiness_Normalised",
            "Freedom_Normalised",
        ]
    ]
    supporting_summary = cleaned[SUPPORTING_COLUMNS].agg(["mean", "min", "max"]).T
    supporting_summary = supporting_summary.reset_index().rename(columns={"index": "Indicator"})
    strongest_positive = correlations.iloc[0]
    strongest_negative = correlations.iloc[-1]
    missing_total = int(missing_summary["Missing Values"].sum())
    if missing_total == 0:
        missing_value_result = (
            "No missing values were found in the provided dataset, so no "
            "missing-value imputation was required."
        )
    else:
        missing_value_result = (
            f"{missing_total} missing values were found during data preparation. "
            "Rows missing `Country` or `Happiness_Score` were removed before visualisation."
        )

    template = Template(REPORT_TEMPLATE_FILE.read_text(encoding="utf-8"))
    return template.substitute(
        record_count=len(cleaned),
        column_count=len(cleaned.columns),
        duplicate_count=duplicate_count,
        missing_value_result=missing_value_result,
        top3_table=markdown_table(top3_table, ["Happiness_Score", "Freedom_to_Make_Choices"]),
        lowest_table=markdown_table(lowest_table, ["Happiness_Score", "Freedom_to_Make_Choices"]),
        lowest_comparison_table=markdown_table(
            lowest_comparison_table,
            [
                "Happiness_Score",
                "Freedom_to_Make_Choices",
                "Happiness_Normalised",
                "Freedom_Normalised",
            ],
        ),
        supporting_summary_table=markdown_table(supporting_summary, ["mean", "min", "max"]),
        correlation_table=markdown_table(correlations, ["Correlation_with_Happiness"]),
        strongest_positive_indicator=strongest_positive["Indicator"],
        strongest_positive_correlation=f"{strongest_positive['Correlation_with_Happiness']:.2f}",
        strongest_negative_indicator=strongest_negative["Indicator"],
        strongest_negative_correlation=f"{strongest_negative['Correlation_with_Happiness']:.2f}",
        lowest_country=lowest["Country"],
        lowest_happiness=f"{lowest['Happiness_Score']:.2f}",
        lowest_freedom=f"{lowest['Freedom_to_Make_Choices']:.2f}",
        freedom_average=f"{freedom_average:.2f}",
        top_country=top3.iloc[0]["Country"],
        top_score=f"{top3.iloc[0]['Happiness_Score']:.2f}",
    )


def save_outputs(cleaned, missing_summary, duplicate_count, top3, lowest, freedom_average, correlations, correlation_matrix):
    cleaned.to_csv(CLEANED_DATA_FILE, index=False)
    correlations.to_csv(OUTPUT_DIR / "happiness_correlations.csv", index=False)
    correlation_matrix.to_csv(OUTPUT_DIR / "happiness_correlation_matrix.csv")
    create_visualisations(cleaned, top3, lowest, correlation_matrix)

    report = build_report(cleaned, missing_summary, duplicate_count, top3, lowest, freedom_average, correlations)
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(report)


def main():
    ensure_directories()
    cleaned, missing_summary, duplicate_count = load_and_clean_data()
    top3, lowest, freedom_average = get_dashboard_data(cleaned)
    correlations = happiness_correlations(cleaned)
    correlation_matrix = happiness_correlation_matrix(cleaned)
    save_outputs(cleaned, missing_summary, duplicate_count, top3, lowest, freedom_average, correlations, correlation_matrix)


if __name__ == "__main__":
    main()
