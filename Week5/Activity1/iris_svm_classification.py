"""
Week 5 Activity 1

Classify the Iris dataset with Support Vector Machine (SVM).

The script follows the four steps from the class example:
Step 1: Import sklearn datasets and SVM.
Step 2: Load the Iris dataset.
Step 3: Train the SVM classifier.
Step 4: Predict flower species and evaluate accuracy.
"""

# Step 1: Import sklearn datasets and SVM, plus support libraries for
# data preparation, evaluation, and visualisation.
from pathlib import Path
import os
import tempfile

MPL_CONFIG_DIR = Path(tempfile.gettempdir()) / "mse803_matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPL_CONFIG_DIR)

import matplotlib

matplotlib.use("Agg")
from sklearn import datasets
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
CLEANED_DATA_FILE = BASE_DIR / "cleaned_iris_dataset.csv"

FEATURE_COLUMNS = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
TARGET_COLUMN = "species"
CLASS_ORDER = ["setosa", "versicolor", "virginica"]
TEST_SIZE = 0.3
RANDOM_STATE = 15
SVM_KERNEL = "rbf"

CONFUSION_MATRIX_FILE = OUTPUT_DIR / "svm_confusion_matrix.png"
PETAL_SCATTER_FILE = OUTPUT_DIR / "iris_petal_scatter.png"


def ensure_directories():
    """Create the outputs directory before writing files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Step 2: Load the Iris dataset and prepare it for classification.
def load_and_prepare_data():
    """Load Iris from sklearn and perform basic data quality checks."""
    iris = datasets.load_iris()

    # X contains the four numeric flower measurements. y contains the species
    # class to be predicted.
    df = pd.DataFrame(iris.data, columns=FEATURE_COLUMNS)
    df[TARGET_COLUMN] = pd.Categorical.from_codes(iris.target, iris.target_names)

    # Convert measurements to numeric values before model training.
    for column in FEATURE_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    missing_summary = df.isna().sum().reset_index()
    missing_summary.columns = ["Column", "Missing_Values"]
    duplicate_count = int(df.duplicated().sum())

    # Drop invalid records only if essential values are missing.
    cleaned = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).copy()
    cleaned = cleaned.reset_index(drop=True)

    return cleaned, missing_summary, duplicate_count


# Step 3: Train the SVM classifier.
def train_and_evaluate_model(cleaned):
    """Train one SVM classifier and return its test-set performance."""
    x = cleaned[FEATURE_COLUMNS]
    y = cleaned[TARGET_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    # Split 150 records into 105 training records and 45 testing records.
    # X_train/y_train are used to train the model.
    # X_test/y_test are kept separate for evaluation.
    #
    # This follows the scikit-learn SVM example structure:
    # create an SVC classifier, fit it on X/y training data, then predict.
    # StandardScaler comes from sklearn.preprocessing. It standardises the
    # four measurement columns before training, which is useful for SVM.
    # The pipeline fits the scaler only on training data, then applies the
    # same transformation to the test data during prediction.
    model = make_pipeline(StandardScaler(), SVC(kernel=SVM_KERNEL))
    model.fit(x_train, y_train)

    # Step 4: Predict flower species for the test set.
    y_pred = model.predict(x_test)

    metrics = pd.DataFrame(
        [
            {
                "Model": "SVM Classifier (SVC)",
                "Kernel": SVM_KERNEL,
                "Training_Records": len(x_train),
                "Testing_Records": len(x_test),
                "Accuracy": accuracy_score(y_test, y_pred),
                "Weighted_Precision": precision_score(
                    y_test,
                    y_pred,
                    labels=CLASS_ORDER,
                    average="weighted",
                    zero_division=0,
                ),
                "Weighted_Recall": recall_score(
                    y_test,
                    y_pred,
                    labels=CLASS_ORDER,
                    average="weighted",
                    zero_division=0,
                ),
            }
        ]
    )

    return {
        "x_train": x_train,
        "x_test": x_test,
        "y_train": y_train,
        "y_test": y_test,
        "metrics": metrics,
        "model": model,
        "prediction": y_pred,
    }


# Step 4 continued: Evaluate prediction quality with a confusion matrix.
def create_confusion_matrix_plot(y_test, y_pred):
    """Show correct and incorrect classifications for the SVM classifier."""
    matrix = confusion_matrix(y_test, y_pred, labels=CLASS_ORDER)
    display = ConfusionMatrixDisplay(confusion_matrix=matrix, display_labels=CLASS_ORDER)
    fig, ax = plt.subplots(figsize=(7, 6))
    display.plot(ax=ax, cmap="Blues", colorbar=True, values_format="d")
    ax.set_title("SVM Classifier with RBF Kernel: Confusion Matrix")
    ax.set_xticklabels(CLASS_ORDER, rotation=25, ha="right")
    ax.set_yticklabels(CLASS_ORDER)
    fig.tight_layout()
    fig.savefig(CONFUSION_MATRIX_FILE, dpi=160)
    plt.close()


# Extra visualisation: show the dataset structure before classification.
# This supports the SVM task by showing that petal measurements separate
# the three species reasonably well.
def create_petal_scatter_plot(cleaned):
    """Visualise the Iris classes using petal length and petal width."""
    colors = {
        "setosa": "#1f77b4",
        "versicolor": "#2ca02c",
        "virginica": "#d62728",
    }

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for species, group in cleaned.groupby(TARGET_COLUMN, observed=False):
        ax.scatter(
            group["petal_length"],
            group["petal_width"],
            label=species,
            color=colors[species],
            alpha=0.8,
        )

    ax.set_title("Iris Petal Measurements by Species")
    ax.set_xlabel("Petal length (cm)")
    ax.set_ylabel("Petal width (cm)")
    ax.grid(alpha=0.25)
    ax.legend(title="Species")
    fig.tight_layout()
    fig.savefig(PETAL_SCATTER_FILE, dpi=160)
    plt.close()


# Save the cleaned data, model evaluation tables, and visualisations.
def save_outputs(cleaned, missing_summary, duplicate_count, results):
    """Save cleaned data, model outputs, and figures."""
    cleaned.to_csv(CLEANED_DATA_FILE, index=False)
    missing_summary.to_csv(OUTPUT_DIR / "missing_summary.csv", index=False)
    pd.DataFrame([{"Duplicate_Rows": duplicate_count}]).to_csv(
        OUTPUT_DIR / "duplicate_summary.csv",
        index=False,
    )
    cleaned[TARGET_COLUMN].value_counts().rename_axis("Species").reset_index(name="Count").to_csv(
        OUTPUT_DIR / "class_distribution.csv",
        index=False,
    )
    results["metrics"].to_csv(OUTPUT_DIR / "svm_model_accuracy.csv", index=False)

    report = classification_report(
        results["y_test"],
        results["prediction"],
        labels=CLASS_ORDER,
        output_dict=True,
        zero_division=0,
    )
    pd.DataFrame(report).T.to_csv(OUTPUT_DIR / "svm_classification_report.csv")
    pd.DataFrame(
        confusion_matrix(results["y_test"], results["prediction"], labels=CLASS_ORDER),
        index=CLASS_ORDER,
        columns=CLASS_ORDER,
    ).to_csv(OUTPUT_DIR / "svm_confusion_matrix.csv")

    create_petal_scatter_plot(cleaned)
    create_confusion_matrix_plot(results["y_test"], results["prediction"])

    print("Model: SVM Classifier (SVC, RBF kernel)")
    print(f"Analysis outputs saved to: {OUTPUT_DIR}")


def main():
    """Run the full Iris SVM classification workflow."""
    ensure_directories()
    cleaned, missing_summary, duplicate_count = load_and_prepare_data()
    results = train_and_evaluate_model(cleaned)
    save_outputs(cleaned, missing_summary, duplicate_count, results)


if __name__ == "__main__":
    main()
