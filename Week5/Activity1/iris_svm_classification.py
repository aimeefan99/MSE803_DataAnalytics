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
import csv
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
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
CLEANED_DATA_FILE = BASE_DIR / "cleaned_iris_dataset.csv"

TEST_SIZE = 0.3

# Change these two values to test how the SVM result changes.
SVM_KERNEL = "rbf"
RANDOM_STATE = 30

CONFUSION_MATRIX_FILE = OUTPUT_DIR / "svm_confusion_matrix.png"
PETAL_SCATTER_FILE = OUTPUT_DIR / "iris_petal_scatter.png"


def ensure_directories():
    """Create the outputs directory before writing files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Step 2: Load the Iris dataset and prepare it for classification.
def load_iris_data():
    """Load Iris from sklearn and define X features and y classes."""
    iris = datasets.load_iris()

    # Same structure as the teacher's sample code:
    # X contains four numeric flower measurements.
    # y contains the three species classes as numeric labels: 0, 1, and 2.
    x = iris.data
    y = iris.target

    return iris, x, y


# Step 3: Train the SVM classifier.
def train_and_evaluate_model(x, y):
    """Train one SVM classifier and return its test-set performance."""
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
    # Standardise the four feature columns before SVM training.
    # fit_transform is used on training data, while transform applies the same
    # scaling rule to the test data.
    scaler = StandardScaler()
    x_train = scaler.fit_transform(x_train)
    x_test = scaler.transform(x_test)

    # This follows the scikit-learn SVM example structure:
    # create an SVC classifier, fit it on X/y training data, then predict.
    model = SVC(kernel=SVM_KERNEL)
    model.fit(x_train, y_train)

    # Step 4: Predict flower species for the test set.
    y_pred = model.predict(x_test)

    metrics = {
        "Model": "SVM Classifier (SVC)",
        "Kernel": SVM_KERNEL,
        "Random_State": RANDOM_STATE,
        "Training_Records": len(x_train),
        "Testing_Records": len(x_test),
        "Accuracy": accuracy_score(y_test, y_pred),
        "Weighted_Precision": precision_score(
            y_test,
            y_pred,
            average="weighted",
            zero_division=0,
        ),
        "Weighted_Recall": recall_score(
            y_test,
            y_pred,
            average="weighted",
            zero_division=0,
        ),
    }

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
def create_confusion_matrix_plot(y_test, y_pred, class_names):
    """Show correct and incorrect classifications for the SVM classifier."""
    class_labels = range(len(class_names))
    matrix = confusion_matrix(y_test, y_pred, labels=class_labels)
    display = ConfusionMatrixDisplay(confusion_matrix=matrix, display_labels=class_names)
    fig, ax = plt.subplots(figsize=(7, 6))
    display.plot(ax=ax, cmap="Blues", colorbar=True, values_format="d")
    ax.set_title(f"SVM Classifier with {SVM_KERNEL} Kernel: Confusion Matrix")
    ax.set_xticklabels(class_names, rotation=25, ha="right")
    ax.set_yticklabels(class_names)
    fig.tight_layout()
    fig.savefig(CONFUSION_MATRIX_FILE, dpi=160)
    plt.close()


# Extra visualisation: show the dataset structure before classification.
# This supports the SVM task by showing that petal measurements separate
# the three species reasonably well.
def create_petal_scatter_plot(x, y, class_names):
    """Visualise the Iris classes using petal length and petal width."""
    colors = {
        0: "#1f77b4",
        1: "#2ca02c",
        2: "#d62728",
    }

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for class_id, class_name in enumerate(class_names):
        rows = y == class_id
        ax.scatter(
            x[rows, 2],
            x[rows, 3],
            label=class_name,
            color=colors[class_id],
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


def save_clean_dataset(iris, x, y):
    """Save a readable copy of the Iris data used in the analysis."""
    feature_names = [name.replace(" (cm)", "").replace(" ", "_") for name in iris.feature_names]
    with CLEANED_DATA_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(feature_names + ["species"])
        for measurements, class_id in zip(x, y):
            writer.writerow(list(measurements) + [iris.target_names[class_id]])


def save_metrics(results):
    """Save accuracy, precision, recall, and confusion matrix values."""
    with (OUTPUT_DIR / "svm_model_accuracy.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results["metrics"].keys())
        writer.writeheader()
        writer.writerow(results["metrics"])


def save_classification_report(results, class_names):
    """Save the detailed classification report from sklearn."""
    report = classification_report(
        results["y_test"],
        results["prediction"],
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )

    with (OUTPUT_DIR / "svm_classification_report.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        fieldnames = ["Class", "Precision", "Recall", "F1_Score", "Support"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row_name in list(class_names) + ["macro avg", "weighted avg"]:
            row = report[row_name]
            writer.writerow(
                {
                    "Class": row_name,
                    "Precision": row["precision"],
                    "Recall": row["recall"],
                    "F1_Score": row["f1-score"],
                    "Support": row["support"],
                }
            )


def save_confusion_matrix(results, class_names):
    """Save the confusion matrix values in CSV format."""
    matrix = confusion_matrix(
        results["y_test"],
        results["prediction"],
        labels=range(len(class_names)),
    )

    with (OUTPUT_DIR / "svm_confusion_matrix.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Actual/Predicted"] + list(class_names))
        for class_name, row in zip(class_names, matrix):
            writer.writerow([class_name] + list(row))


# Save the dataset, model evaluation tables, and visualisations.
def save_outputs(iris, x, y, results):
    """Save cleaned data, model outputs, and figures."""
    class_names = iris.target_names

    save_clean_dataset(iris, x, y)
    save_metrics(results)
    save_classification_report(results, class_names)
    save_confusion_matrix(results, class_names)
    create_petal_scatter_plot(x, y, class_names)
    create_confusion_matrix_plot(results["y_test"], results["prediction"], class_names)

    print(f"Model: SVM Classifier (SVC, {SVM_KERNEL} kernel)")
    print(f"Analysis outputs saved to: {OUTPUT_DIR}")


def main():
    """Run the full Iris SVM classification workflow."""
    ensure_directories()
    iris, x, y = load_iris_data()
    results = train_and_evaluate_model(x, y)
    save_outputs(iris, x, y, results)


if __name__ == "__main__":
    main()
