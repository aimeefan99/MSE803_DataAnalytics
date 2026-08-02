# Week1 - Activity 2: IRIS Dataset Exploration and Analysis

Repository link: https://github.com/aimeefan99/MSE803_DataAnalytics

## Understanding

The Iris dataset is a classic classification dataset from the UCI Machine Learning Repository. Each record describes one iris flower using four numeric measurements, and the target class is the iris species.

This activity explores the basic structure of the dataset:

- how many feature columns are available
- how many target classes are available
- whether duplicate records exist

## Files

- `analyze_iris.py`: Python script that uses `ucimlrepo.fetch_ucirepo(id=53)` to load the dataset from UCI
- `analysis_results.txt`: generated output from the analysis script
- `requirements.txt`: Python package required for fetching the dataset

## Steps Followed

1. Installed the UCI dataset package with `pip3 install -U ucimlrepo`.
2. Fetched the Iris dataset using `fetch_ucirepo(id=53)`.
3. Stored `iris.data.features` as `X` and `iris.data.targets` as `y`.
4. Counted the number of feature columns in `X`.
5. Counted the distinct target classes in `y`.
6. Counted how many records belong to each class.
7. Joined `X` and `y`, then checked duplicate records by comparing every complete row.
8. Saved the analysis output to `analysis_results.txt`.

## Findings

- Total records: 150
- Number of features: 4
- Feature columns: `sepal length`, `sepal width`, `petal length`, `petal width`
- Number of classes: 3
- Classes: `Iris-setosa`, `Iris-versicolor`, `Iris-virginica`
- Records per class:
  - `Iris-setosa`: 50
  - `Iris-versicolor`: 50
  - `Iris-virginica`: 50
- Duplicate records: yes
- Duplicate record count: 3 additional duplicate records beyond their first occurrence
- Duplicate groups: 2

Note: `data.duplicated().sum()` counts only the extra duplicated records after the first occurrence. The duplicate table lists all rows involved in duplication, including the original rows.

The duplicate groups are:

- Rows 10, 35, and 38: `4.9, 3.1, 1.5, 0.1, Iris-setosa`
- Rows 102 and 143: `5.8, 2.7, 5.1, 1.9, Iris-virginica`

## How to Run

From the repository root:

```bash
python3 -m pip install -U ucimlrepo
python3 Week1/Activity2/analyze_iris.py
```

The script prints the findings and writes the same result to `Week1/Activity2/analysis_results.txt`.
