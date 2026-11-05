# CrimeSight – Predicting Crime Trends Using Machine Learning

## 📌 Project Overview

CrimeSight is a machine learning-based crime data analytics application designed to analyze historical crime records and provide data-driven insights into crime patterns across different geographical locations and years.

The application uses machine learning algorithms to classify crime categories based on historical data, location, year, and population. It provides an interactive dashboard with visualizations, statistical summaries, and analytical results to help users explore historical crime trends and understand patterns in public safety data.

## 🎯 Objectives

- Analyze historical crime datasets to identify patterns and trends.
- Apply machine learning algorithms for crime category classification.
- Explore crime distributions across different locations and years.
- Visualize crime statistics through interactive charts and dashboards.
- Provide data-driven insights to support research and public safety analysis.

## ✨ Key Features

- **Interactive Dashboard:** Displays crime statistics, category distributions, and location-based insights.
- **Crime Classification:** Uses Random Forest and Extra Trees algorithms to classify crime categories.
- **Crime Rate Estimation:** Uses Random Forest Regression when sufficient crime-rate data is available.
- **Historical Data Analysis:** Explores crime records based on location and year.
- **Data Visualization:** Presents crime trends, category distributions, and geographical comparisons.
- **Prediction Results:** Displays predicted categories and model confidence scores.
- **CSV Download:** Allows users to download filtered crime records.
- **JSON API:** Provides endpoints for accessing summary statistics and crime records.

## 🛠️ Technologies Used

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend | Flask |
| Machine Learning | Scikit-learn |
| Data Processing | Pandas, NumPy |
| Data Visualization | HTML, CSS, JavaScript |
| Dataset Formats | CSV, Excel |
| Algorithms | Random Forest, Extra Trees, Random Forest Regression |

## ⚙️ Machine Learning Methodology

1. **Data Collection:** Load historical crime datasets from CSV or Excel files.
2. **Data Preprocessing:** Clean missing values, normalize column names, and prepare input features.
3. **Feature Selection:** Use year, location, and population as model input features.
4. **Model Training:** Train Random Forest and Extra Trees classification models.
5. **Model Evaluation:** Evaluate classification performance using accuracy and weighted F1-score.
6. **Prediction:** Generate crime category estimates for the selected location and year.
7. **Visualization:** Display analytical results through the dashboard.

## 🚀 Expected Outcome

CrimeSight provides an interactive platform for exploring historical crime information and understanding data patterns. It demonstrates how machine learning and data visualization can be combined to support academic research and public safety analytics.

## 🔮 Future Enhancements

- Integrate larger and more diverse crime datasets.
- Explore advanced machine learning and deep learning techniques.
- Add interactive geographical crime visualizations.
- Improve model evaluation using independent test datasets.
- Introduce additional data filtering and reporting capabilities.

## ⚠️ Responsible Use

This is an academic data analytics prototype. Its classification results describe categories present in historical records; they do not predict whether a crime will occur. Model outputs should not be used for individual risk assessment, surveillance, policing, or other high-impact decisions.

## 👩‍💻 Project Domain

Machine Learning | Data Science | Crime Data Analytics | Public Safety
