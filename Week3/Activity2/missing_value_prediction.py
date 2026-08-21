from pathlib import Path
import os
import tempfile
from string import Template

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mse803_matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures


# This script continues Week 3 Activity 1.
# It reads the cleaned dataset from Activity 1, predicts selected missing
# values with both linear regression and polynomial regression, then writes
# a report and a completed dataset for Activity 2.
BASE_DIR = Path(__file__).resolve().parent
ACTIVITY1_DIR = BASE_DIR.parent / "Activity1"

INPUT_FILE = ACTIVITY1_DIR / "cleaned_dataset.csv"
RESULTS_FILE = BASE_DIR / "prediction_results.md"
REPORT_TEMPLATE_FILE = BASE_DIR / "report_template.md"
PREDICTIONS_FILE = BASE_DIR / "missing_value_predictions.csv"
COMPLETED_DATASET_FILE = BASE_DIR / "completed_dataset.csv"
DAVID_PLOT_FILE = BASE_DIR / "david_net_worth_regression.png"
GRACE_PLOT_FILE = BASE_DIR / "grace_country_regression.png"

# David's Net worth is numeric, so only numeric input fields are used.
# Age and Salary are available for David and most complete training rows.
NET_WORTH_FEATURES = ["Age", "Salary"]

# Grace's Country is categorical. To meet the activity requirement, Country is
# encoded into numbers first, then regression models are used on numeric fields.
COUNTRY_FEATURES = ["Age", "Net worth", "Salary"]


def linear_model():
    # Baseline model: assumes a straight-line relationship between inputs and target.
    return LinearRegression()


def polynomial_model():
    # Non-linear model: PolynomialFeatures creates degree-2 terms such as
    # Age^2, Salary^2, and Age * Salary. LinearRegression then fits those
    # expanded features. This follows the supplied sample code pattern.
    return Pipeline(
        [
            ("polynomial_features", PolynomialFeatures(degree=2, include_bias=False)),
            ("linear_regression", LinearRegression()),
        ]
    )


def load_cleaned_dataset():
    # Use Activity 1's cleaned file so Activity 2 builds on the previous work
    # instead of repeating all original cleaning steps.
    df = pd.read_csv(INPUT_FILE)

    # Convert analytical fields to numeric again after reading from CSV.
    # Invalid or blank values become NaN and are excluded from model training.
    for column in ["Age", "Net worth", "Salary"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # Keep ID and Original Row as nullable integers because Eve has no ID.
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce").astype("Int64")
    df["Original Row"] = pd.to_numeric(df["Original Row"], errors="coerce").astype("Int64")

    # Activity 1 used "Unknown" as the placeholder for missing text values.
    df["Name"] = df["Name"].fillna("Unknown")
    df["Country"] = df["Country"].fillna("Unknown")
    return df


def regression_metrics(model, x_values, y_values):
    # The dataset is very small, so leave-one-out cross-validation is used.
    # Each row is tested once while all remaining rows are used for training.
    predictions = cross_val_predict(model, x_values, y_values, cv=LeaveOneOut())
    return {
        "MAE": mean_absolute_error(y_values, predictions),
        "RMSE": np.sqrt(mean_squared_error(y_values, predictions)),
        "R2": r2_score(y_values, predictions),
    }


def predict_david_net_worth(df):
    # Train only on rows that have all input features and the target value.
    # David is excluded automatically because his Net worth is missing.
    training_df = df[df[NET_WORTH_FEATURES + ["Net worth"]].notna().all(axis=1)]
    x_train = training_df[NET_WORTH_FEATURES].to_numpy(dtype=float)
    y_train = training_df["Net worth"].to_numpy(dtype=float)
    x_david = df.loc[df["Name"] == "David", NET_WORTH_FEATURES].to_numpy(dtype=float)

    # Run both required approaches for comparison:
    # 1. Linear regression
    # 2. Non-linear polynomial regression
    rows = []
    for model_name, model in [
        ("Linear Regression", linear_model()),
        ("Polynomial Regression degree 2", polynomial_model()),
    ]:
        # Evaluate with cross-validation first, then fit on all available rows
        # to make the final prediction for David.
        metrics = regression_metrics(model, x_train, y_train)
        model.fit(x_train, y_train)
        prediction = float(model.predict(x_david)[0])
        rows.append(
            {
                "Target": "David - Net worth",
                "Model": model_name,
                "Predicted Value": prediction,
                "MAE": metrics["MAE"],
                "RMSE": metrics["RMSE"],
                "R2": metrics["R2"],
            }
        )

    return pd.DataFrame(rows), training_df


def encode_country_labels(series):
    # Regression models require numeric targets.
    # Example for this dataset: AUS -> 0 and NZ -> 1.
    labels = sorted(series.unique())
    label_to_number = {label: index for index, label in enumerate(labels)}
    number_to_label = {index: label for label, index in label_to_number.items()}
    return label_to_number, number_to_label


def nearest_country_label(numeric_prediction, number_to_label):
    # A regression prediction for Country can be a decimal, such as -0.09.
    # Round it to the nearest valid encoded label and clip it into the valid
    # label range before converting back to AUS or NZ.
    lower_bound = min(number_to_label)
    upper_bound = max(number_to_label)
    rounded_value = int(np.clip(np.rint(numeric_prediction), lower_bound, upper_bound))
    return number_to_label[rounded_value]


def country_metrics(model, x_values, y_values, number_to_label):
    # Evaluate the encoded numeric predictions and also convert them back to
    # country labels so an accuracy score can be reported.
    numeric_predictions = cross_val_predict(model, x_values, y_values, cv=LeaveOneOut())
    class_predictions = [
        nearest_country_label(prediction, number_to_label)
        for prediction in numeric_predictions
    ]
    actual_classes = [number_to_label[int(value)] for value in y_values]

    return {
        "MAE": mean_absolute_error(y_values, numeric_predictions),
        "RMSE": np.sqrt(mean_squared_error(y_values, numeric_predictions)),
        "Accuracy": accuracy_score(actual_classes, class_predictions),
    }


def predict_grace_country(df):
    # Training records must have a known country and complete numeric features.
    # Grace is excluded because her Country is Unknown.
    # Heidi is excluded because she is missing too many numeric input fields.
    training_df = df[
        (df["Country"] != "Unknown")
        & df[COUNTRY_FEATURES].notna().all(axis=1)
    ].copy()
    label_to_number, number_to_label = encode_country_labels(training_df["Country"])

    training_df["Country Encoded"] = training_df["Country"].map(label_to_number)
    x_train = training_df[COUNTRY_FEATURES].to_numpy(dtype=float)
    y_train = training_df["Country Encoded"].to_numpy(dtype=float)
    x_grace = df.loc[df["Name"] == "Grace", COUNTRY_FEATURES].to_numpy(dtype=float)

    # Compare linear and polynomial regression on the encoded Country target.
    rows = []
    for model_name, model in [
        ("Linear Regression", linear_model()),
        ("Polynomial Regression degree 2", polynomial_model()),
    ]:
        # The final numeric prediction is converted back to the nearest country
        # label so the completed dataset remains categorical.
        metrics = country_metrics(model, x_train, y_train, number_to_label)
        model.fit(x_train, y_train)
        numeric_prediction = float(model.predict(x_grace)[0])
        country_prediction = nearest_country_label(numeric_prediction, number_to_label)
        rows.append(
            {
                "Target": "Grace - Country",
                "Model": model_name,
                "Numeric Prediction": numeric_prediction,
                "Predicted Value": country_prediction,
                "MAE": metrics["MAE"],
                "RMSE": metrics["RMSE"],
                "Accuracy": metrics["Accuracy"],
            }
        )

    return pd.DataFrame(rows), training_df, label_to_number


def best_numeric_prediction(predictions_df):
    # For David's numeric Net worth, choose the model with the lowest validation
    # error. RMSE is used first because it penalizes large errors strongly.
    return predictions_df.sort_values(["RMSE", "MAE"]).iloc[0]


def best_country_prediction(predictions_df):
    # For Grace's encoded Country, choose the model with the highest validation
    # accuracy. If accuracy is tied, use RMSE as the secondary comparison.
    return predictions_df.sort_values(
        ["Accuracy", "RMSE"], ascending=[False, True]
    ).iloc[0]


def format_number(value):
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{value:,.2f}"
    return str(value)


def format_text(value):
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)) and value.is_integer():
        return str(int(value))
    return str(value)


def markdown_table(df, numeric_columns=None):
    # Build simple markdown tables for the generated report without adding
    # another formatting dependency.
    numeric_columns = set(numeric_columns or [])
    formatted = df.copy()
    for column in formatted.columns:
        if column in numeric_columns:
            formatted[column] = formatted[column].map(format_number)
        else:
            formatted[column] = formatted[column].map(format_text)

    headers = list(formatted.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in formatted.iterrows():
        lines.append("| " + " | ".join(row.astype(str)) + " |")
    return "\n".join(lines)


def build_completed_dataset(df, net_worth_choice, country_choice):
    # Apply only the selected predictions required by Activity 2.
    # Heidi is intentionally left unchanged because her row lacks enough inputs.
    completed_df = df.copy()
    completed_df.loc[completed_df["Name"] == "David", "Net worth"] = round(
        float(net_worth_choice["Predicted Value"]), 2
    )
    completed_df.loc[completed_df["Name"] == "Grace", "Country"] = country_choice[
        "Predicted Value"
    ]
    return completed_df


def model_list():
    return [
        ("Linear Regression", linear_model()),
        ("Polynomial Regression degree 2", polynomial_model()),
    ]


def plot_david_net_worth(df, training_df, predictions_df):
    # David's model uses two features: Age and Salary.
    # A 2D chart can only show one x-axis, so this plot uses Age on the x-axis
    # and keeps Salary fixed at David's salary. This visualises a model slice
    # through the trained regression surface.
    x_train = training_df[NET_WORTH_FEATURES].to_numpy(dtype=float)
    y_train = training_df["Net worth"].to_numpy(dtype=float)
    david_row = df.loc[df["Name"] == "David"].iloc[0]
    david_age = float(david_row["Age"])
    david_salary = float(david_row["Salary"])

    age_min = min(training_df["Age"].min(), david_age) - 1
    age_max = max(training_df["Age"].max(), david_age) + 1
    age_plot = np.linspace(age_min, age_max, 100)
    x_plot = np.column_stack([age_plot, np.full_like(age_plot, david_salary)])

    plt.figure(figsize=(10, 6))
    plt.scatter(
        training_df["Age"],
        training_df["Net worth"],
        color="#1f77b4",
        label="Training records",
    )

    for model_name, model in model_list():
        model.fit(x_train, y_train)
        y_plot = model.predict(x_plot)
        line_style = "-" if model_name == "Linear Regression" else "--"
        color = "#d62728" if model_name == "Linear Regression" else "#2ca02c"
        plt.plot(age_plot, y_plot, line_style, color=color, linewidth=2, label=model_name)

        prediction = predictions_df.loc[
            predictions_df["Model"] == model_name, "Predicted Value"
        ].iloc[0]
        marker = "X" if model_name == "Linear Regression" else "D"
        plt.scatter(
            david_age,
            prediction,
            marker=marker,
            s=120,
            color=color,
            edgecolor="black",
            linewidth=0.8,
            label=f"David prediction: {model_name}",
        )

    plt.title("David Net Worth Prediction: Linear vs Polynomial Regression")
    plt.xlabel("Age")
    plt.ylabel("Net worth")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.figtext(
        0.5,
        0.01,
        f"Model slice shown with Salary fixed at David's salary: {david_salary:,.0f}",
        ha="center",
        fontsize=9,
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(DAVID_PLOT_FILE, dpi=160)
    plt.close()


def plot_grace_country(df, training_df, predictions_df, country_labels):
    # Grace's model uses Age, Net worth, and Salary.
    # The chart uses Age on the x-axis and keeps Net worth and Salary fixed at
    # Grace's values. The y-axis is the encoded Country value: AUS=0, NZ=1.
    label_to_number = country_labels
    number_to_label = {number: label for label, number in label_to_number.items()}
    x_train = training_df[COUNTRY_FEATURES].to_numpy(dtype=float)
    y_train = training_df["Country Encoded"].to_numpy(dtype=float)
    grace_row = df.loc[df["Name"] == "Grace"].iloc[0]
    grace_age = float(grace_row["Age"])
    grace_net_worth = float(grace_row["Net worth"])
    grace_salary = float(grace_row["Salary"])

    age_min = min(training_df["Age"].min(), grace_age) - 1
    age_max = max(training_df["Age"].max(), grace_age) + 1
    age_plot = np.linspace(age_min, age_max, 100)
    x_plot = np.column_stack(
        [
            age_plot,
            np.full_like(age_plot, grace_net_worth),
            np.full_like(age_plot, grace_salary),
        ]
    )

    plt.figure(figsize=(10, 6))
    plt.scatter(
        training_df["Age"],
        training_df["Country Encoded"],
        color="#1f77b4",
        label="Training records",
    )

    for encoded_value, label in number_to_label.items():
        plt.axhline(encoded_value, color="gray", linewidth=1, alpha=0.25)
        plt.text(age_min, encoded_value + 0.03, label, fontsize=9, color="gray")

    for model_name, model in model_list():
        model.fit(x_train, y_train)
        y_plot = model.predict(x_plot)
        line_style = "-" if model_name == "Linear Regression" else "--"
        color = "#d62728" if model_name == "Linear Regression" else "#2ca02c"
        plt.plot(age_plot, y_plot, line_style, color=color, linewidth=2, label=model_name)

        numeric_prediction = predictions_df.loc[
            predictions_df["Model"] == model_name, "Numeric Prediction"
        ].iloc[0]
        marker = "X" if model_name == "Linear Regression" else "D"
        plt.scatter(
            grace_age,
            numeric_prediction,
            marker=marker,
            s=120,
            color=color,
            edgecolor="black",
            linewidth=0.8,
            label=f"Grace prediction: {model_name}",
        )

    plt.title("Grace Country Prediction: Linear vs Polynomial Regression")
    plt.xlabel("Age")
    plt.ylabel("Country encoded value")
    plt.ylim(-1.25, 1.25)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.figtext(
        0.5,
        0.01,
        (
            "Model slice shown with Net worth fixed at "
            f"{grace_net_worth:,.0f} and Salary fixed at {grace_salary:,.0f}"
        ),
        ha="center",
        fontsize=9,
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(GRACE_PLOT_FILE, dpi=160)
    plt.close()


def create_plots(
    df,
    net_worth_predictions,
    net_worth_training,
    country_predictions,
    country_training,
    country_labels,
):
    # Generate visual comparisons of the two models for the final report.
    # These plots are supporting evidence for the model comparison tables.
    plot_david_net_worth(df, net_worth_training, net_worth_predictions)
    plot_grace_country(df, country_training, country_predictions, country_labels)


def build_report(
    df,
    net_worth_predictions,
    net_worth_training,
    country_predictions,
    country_training,
    country_labels,
    completed_df,
):
    # Read the markdown template from a separate file so the code stays focused
    # on calculations and the report text can be edited independently.
    net_worth_choice = best_numeric_prediction(net_worth_predictions)
    country_choice = best_country_prediction(country_predictions)

    net_worth_training_table = net_worth_training[
        ["Name"] + NET_WORTH_FEATURES + ["Net worth"]
    ]
    country_training_table = country_training[
        ["Name"] + COUNTRY_FEATURES + ["Country", "Country Encoded"]
    ]

    country_label_text = ", ".join(
        f"{label}={number}" for label, number in country_labels.items()
    )

    completed_preview = completed_df[
        ["ID", "Name", "Age", "Net worth", "Country", "Salary", "Join Date"]
    ]

    template = Template(REPORT_TEMPLATE_FILE.read_text(encoding="utf-8"))
    return template.substitute(
        net_worth_training_table=markdown_table(
            net_worth_training_table, ["Age", "Salary", "Net worth"]
        ),
        net_worth_predictions_table=markdown_table(
            net_worth_predictions, ["Predicted Value", "MAE", "RMSE", "R2"]
        ),
        david_prediction=format_number(net_worth_choice["Predicted Value"]),
        david_model=net_worth_choice["Model"],
        country_label_text=country_label_text,
        country_training_table=markdown_table(
            country_training_table,
            ["Age", "Net worth", "Salary", "Country Encoded"],
        ),
        country_predictions_table=markdown_table(
            country_predictions, ["Numeric Prediction", "MAE", "RMSE", "Accuracy"]
        ),
        grace_prediction=country_choice["Predicted Value"],
        grace_model=country_choice["Model"],
        completed_dataset_table=markdown_table(
            completed_preview, ["Age", "Net worth", "Salary"]
        ),
    )


def main():
    # 1. Load Activity 1's cleaned dataset.
    df = load_cleaned_dataset()

    # 2. Predict David's numeric missing value and Grace's categorical missing value.
    net_worth_predictions, net_worth_training = predict_david_net_worth(df)
    country_predictions, country_training, country_labels = predict_grace_country(df)

    # 3. Select the preferred prediction for each target.
    net_worth_choice = best_numeric_prediction(net_worth_predictions)
    country_choice = best_country_prediction(country_predictions)
    completed_df = build_completed_dataset(df, net_worth_choice, country_choice)

    # 4. Save visual comparison charts.
    create_plots(
        df,
        net_worth_predictions,
        net_worth_training,
        country_predictions,
        country_training,
        country_labels,
    )

    # 5. Save machine-readable outputs.
    predictions_df = pd.concat(
        [net_worth_predictions, country_predictions], ignore_index=True, sort=False
    )
    predictions_df.to_csv(PREDICTIONS_FILE, index=False)
    completed_df.to_csv(COMPLETED_DATASET_FILE, index=False)

    # 6. Save and print the human-readable report.
    report = build_report(
        df,
        net_worth_predictions,
        net_worth_training,
        country_predictions,
        country_training,
        country_labels,
        completed_df,
    )
    RESULTS_FILE.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
