# Week 3 - Activity 3: Beijing Multi-Site Air Quality Statistical Analysis

## Dataset

This project analyses the Beijing Multi-Site Air Quality dataset from the UCI Machine Learning Repository.

Source: https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data

Dataset summary:
- Raw records loaded: $row_count
- Cleaned records analysed: $cleaned_row_count
- Monitoring stations: $station_count
- Date range: $start_date to $end_date

## Data Cleaning

The original dataset uses separate `year`, `month`, `day`, and `hour` columns. These were combined into one `datetime` column for time-series analysis.

Missing numeric values were cleaned with station-level time interpolation first. Remaining numeric gaps were filled with station medians and then overall medians if needed. Wind direction was cleaned with the most frequent value for each station.

Missing values before and after cleaning:

$missing_summary_table

## Descriptive Statistics

The table below summarises the major pollutant and weather variables. It includes count, mean, median, sample variance, sample standard deviation, minimum, and maximum.

$descriptive_stats_table

## Station-Level PM2.5 Comparison

The highest average PM2.5 station is **$highest_station** with an average PM2.5 of **$highest_station_pm25**.

The lowest average PM2.5 station is **$lowest_station** with an average PM2.5 of **$lowest_station_pm25**.

$station_summary_table

![Average PM2.5 by station](outputs/station_pm25_mean.png)

## Monthly Trend

The chart below shows the monthly average PM2.5 trend across all Beijing monitoring stations.

![Monthly PM2.5 trend](outputs/monthly_pm25_trend.png)

The most recent 12 monthly averages in the dataset are:

$monthly_summary_table

## Correlation Analysis

The strongest absolute correlation with PM2.5 is **$strongest_pm25_corr**, with a correlation coefficient of **$strongest_pm25_corr_value**.

Correlation matrix:

$correlation_table

![Correlation heatmap](outputs/correlation_heatmap.png)

The PM2.5 and PM10 scatter plot is included because these two pollutants are expected to move together.

![PM2.5 vs PM10 scatter](outputs/pm25_pm10_scatter.png)

## Statistical Interpretation

This analysis uses descriptive statistics to summarise the distribution of each variable and bivariate statistics to describe relationships between variables. The correlation matrix shows association, not causation. For example, a high correlation between PM2.5 and PM10 means they tend to move together, but it does not prove that one pollutant directly causes the other.

The estimated 95% confidence interval for the overall mean PM2.5 is **$pm25_ci_low to $pm25_ci_high**, with a sample mean of **$pm25_mean**.

## Conclusion

The dataset shows clear variation in air quality across stations and over time. PM2.5 differs by monitoring site, changes across months, and is associated with other pollutant variables. However, because this is observational data, the results should be interpreted as statistical relationships rather than direct causal effects.
