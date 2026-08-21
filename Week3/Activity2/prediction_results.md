# Week 3 - Activity 2: Data Cleaning Prediction for Missing Value

## Objective

This activity continues the data cleaning work from Week 3 Activity 1. The goal is to retrieve or predict missing values where there is enough supporting data.

The selected missing values are:
- David's missing `Net worth`
- Grace's missing `Country`

Heidi is not predicted because she has several missing fields, so there are not enough reliable input features for regression-based prediction.

## Method

Two models were compared:
- Linear regression
- Non-linear regression using polynomial features with degree 2

Because the dataset has only a small number of records, leave-one-out cross-validation was used to compare prediction quality. Lower MAE and RMSE are better. For the country prediction, higher accuracy is better after rounding the encoded regression result back to the nearest country label.

The two charts below visualise the model comparison. Each chart shows a 2D slice of the trained model because the models use multiple input features.

## David's Missing Net Worth

Input features used: `Age` and `Salary`.

Training records:

| Name | Age | Salary | Net worth |
| --- | --- | --- | --- |
| Alice | 25.00 | 55,000.00 | 30,000.00 |
| Bob | 30.00 | 60,000.00 | 35,000.00 |
| Charlie | 35.00 | 72,000.00 | 40,000.00 |
| Unknown | 40.00 | 65,000.00 | 55,000.00 |
| Grace | 22.00 | 64,000.00 | 28,000.00 |
| Ivan | 27.00 | 58,000.00 | 60,000.00 |
| Eve | 29.00 | 59,000.00 | 22,000.00 |

Prediction results:

| Target | Model | Predicted Value | MAE | RMSE | R2 |
| --- | --- | --- | --- | --- | --- |
| David - Net worth | Linear Regression | 47,099.30 | 11,851.96 | 15,118.97 | -0.33 |
| David - Net worth | Polynomial Regression degree 2 | 177,663.59 | 185,944.26 | 277,463.26 | -446.70 |

Selected value for David's `Net worth`: **47,099.30** from **Linear Regression**.

The linear regression model is preferred for David because it has much lower MAE and RMSE. The polynomial regression model produces an unrealistically high prediction, which indicates overfitting on this very small dataset.

![David net worth regression comparison](david_net_worth_regression.png)

## Grace's Missing Country

`Country` is categorical, so it was encoded as a number for this activity: AUS=0, NZ=1. This is a practical workaround because the activity asks for regression models. In a larger real-world task, a classification model would be more appropriate for country prediction.

Input features used: `Age`, `Net worth`, and `Salary`.

Training records:

| Name | Age | Net worth | Salary | Country | Country Encoded |
| --- | --- | --- | --- | --- | --- |
| Alice | 25.00 | 30,000.00 | 55,000.00 | NZ | 1 |
| Bob | 30.00 | 35,000.00 | 60,000.00 | NZ | 1 |
| Charlie | 35.00 | 40,000.00 | 72,000.00 | AUS | 0 |
| Unknown | 40.00 | 55,000.00 | 65,000.00 | NZ | 1 |
| Ivan | 27.00 | 60,000.00 | 58,000.00 | NZ | 1 |
| Eve | 29.00 | 22,000.00 | 59,000.00 | AUS | 0 |

Prediction results:

| Target | Model | Numeric Prediction | Predicted Value | MAE | RMSE | Accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| Grace - Country | Linear Regression | -0.09 | AUS | 0.80 | 0.97 | 0.83 |
| Grace - Country | Polynomial Regression degree 2 | -1.06 | AUS | 1.21 | 1.66 | 0.67 |

Selected value for Grace's `Country`: **AUS**. The model with the better validation result is **Linear Regression**.

Both models predict `AUS` for Grace, so the final imputed country is the same. Linear regression has better validation accuracy and lower RMSE on this small dataset, so it is more stable according to the measured results. Polynomial regression is still useful as the required non-linear comparison method because an encoded country category may have a non-linear relationship with `Age`, `Net worth`, and `Salary`. However, the validation metrics show that the polynomial model does not improve Grace's prediction in this dataset.

![Grace country regression comparison](grace_country_regression.png)

## Completed Dataset

The selected predictions were applied to David and Grace only. Heidi remains incomplete because her record does not have enough known values for a reliable prediction.

| ID | Name | Age | Net worth | Country | Salary | Join Date |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Alice | 25.00 | 30,000.00 | NZ | 55,000.00 | 15/01/2020 |
| 2 | Bob | 30.00 | 35,000.00 | NZ | 60,000.00 | 20/02/2020 |
| 4 | Charlie | 35.00 | 40,000.00 | AUS | 72,000.00 |  |
| 5 | David | 38.00 | 47,099.30 | NZ | 68,000.00 | 01/11/2019 |
| 7 | Unknown | 40.00 | 55,000.00 | NZ | 65,000.00 | 30/05/2018 |
| 8 | Grace | 22.00 | 28,000.00 | AUS | 64,000.00 | 25/07/2021 |
| 9 | Heidi |  |  | AUS |  | 25/07/2021 |
| 10 | Ivan | 27.00 | 60,000.00 | NZ | 58,000.00 | 15/03/2019 |
|  | Eve | 29.00 | 22,000.00 | AUS | 59,000.00 | 13/01/2019 |

## Conclusion

For David's numeric `Net worth`, linear regression provides the better prediction because it has much lower validation error. For Grace's encoded `Country`, both models produce the same final country value, `AUS`, but linear regression performs better on the validation metrics. Overall, polynomial regression is demonstrated as the required non-linear method, but it does not provide better predictions for this small dataset.
