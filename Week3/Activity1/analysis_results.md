# Week 3 - Activity 1: Initial Statistical Analysis

## Dataset

Source file: Sample_dataset.csv
Original records: 10
Cleaned records used for analysis: 9

## Data Cleaning Summary

Raw missing values by column:

```text
ID           1
Name         1
Age          2
Net worth    3
Country      1
Salary       2
Join Date    1
```

Rows removed because ID is missing: 0
Rows retained with missing ID: 1
Duplicate ID rows involved in merge: 2

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
 ID    Name  Age  Net worth Country  Salary  Join Date  Original Row
  1   Alice 25.0    30000.0      NZ 55000.0 15/01/2020             1
  2     Bob 30.0    35000.0      NZ 60000.0 20/02/2020             2
  4 Charlie 35.0    40000.0     AUS 72000.0       <NA>             4
  5   David 38.0        NaN      NZ 68000.0 01/11/2019             5
  7 Unknown 40.0    55000.0      NZ 65000.0 30/05/2018             7
  8   Grace 22.0    28000.0 Unknown 64000.0 25/07/2021             8
  9   Heidi  NaN        NaN     AUS     NaN 25/07/2021             9
 10    Ivan 27.0    60000.0      NZ 58000.0 15/03/2019            10
<NA>     Eve 29.0    22000.0     AUS 59000.0 13/01/2019             6
```

## Required Statistical Metrics

| Variable | Mean | Sample Variance | Sample Standard Deviation |
| --- | --- | --- | --- |
| Age | 30.75 | 40.50 | 6.36 |
| Net worth | 38,571.43 | 200,619,047.62 | 14,164.01 |
| Salary | 62,625.00 | 31,982,142.86 | 5,655.28 |

## Sample Covariance Between Variables

| Variable Pair | Pair Count | Sample Covariance |
| --- | --- | --- |
| Age vs Net worth | 7 | 41,857.14 |
| Age vs Salary | 8 | 22,607.14 |
| Net worth vs Salary | 7 | 12,261,904.76 |

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
