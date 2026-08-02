from pathlib import Path

from ucimlrepo import fetch_ucirepo


iris = fetch_ucirepo(id=53)

X = iris.data.features
y = iris.data.targets
data = X.join(y)

classes = y.iloc[:, 0].unique()
class_counts = y.iloc[:, 0].value_counts()
duplicate_count = data.duplicated().sum()
duplicate_rows = data[data.duplicated(keep=False)]

report = f"""IRIS Dataset Exploration and Analysis
=====================================
Total records: {len(data)}
Number of features: {X.shape[1]}
Feature columns: {", ".join(X.columns)}
Number of classes: {len(classes)}
Classes: {", ".join(classes)}
Records per class:
{class_counts.to_string()}
Duplicate records found: {"Yes" if duplicate_count > 0 else "No"}
Duplicate record count: {duplicate_count}
"""

if duplicate_count > 0:
    report += "\nDuplicate rows:\n"
    report += duplicate_rows.to_string()
    report += "\n"

Path(__file__).with_name("analysis_results.txt").write_text(report, encoding="utf-8")
print(report)
