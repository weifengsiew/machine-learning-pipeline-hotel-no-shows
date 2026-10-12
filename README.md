# Hotel no-show prediction pipeline

<p align="center">
  <img src="notebooks/images/final_results_header.png" alt="Hotel no-show prediction report visual" width="900">
</p>

<p align="center">
  <sub>Header image source: <a href="https://www.prostay.com/blog/hotel-no-show/">Prostay, Hotel No Show: Prevention and Management Strategies</a>.</sub>
</p>

## 1. Project Objective

In this project, we leverage machine learning to accurately predict the probability that a hotel guest will show up for their booked stay ('0'), or if a no-show will occur ('1'). These probability estimates can support hotel operations management decisions, including staffing, inventory planning, booking reminders, deposit policies, and overbooking limits. By identifying bookings with a higher risk of no-show, the hotel can make more informed decisions that support business objectives such as reducing operational inefficiencies, improving resource allocation and protecting revenue.

**Input:** Hotel booking information, including:

- booking and stay calendar fields
- branch, country, room, and booking platform
- first-time guest status
- adult and child counts
- booking price and currency

**Output:** The probability that a booking will be a no-show.

**Main metric:** Area under the receiver operating characteristic curve
(AUROC).

AUROC is used to compare candidate pipelines because the model produces
no-show probabilities and must distinguish no-shows from shows across
classification thresholds. Calibration is also evaluated because the
probabilities support operational decisions.

## Data

We use the `noshow.db` SQLite dataset, which contains 119,391 hotel booking
rows and 15 raw columns. The raw database is downloaded by `scripts/stage1.sh`
from the configured source URL and stored at `data/raw/noshow.db`. The raw data
is not committed to the repository.

## Solution: machine learning pipeline

<img src="notebooks/images/kedro%20pipeline.png" alt="Kedro pipeline visualisation" width="700">

[Open the Kedro pipeline visualisation](https://weifengsiew.github.io/machine-learning-pipeline-hotel-no-shows/?types=nodes&expandAllPipelines=false&pid=__default__)

## Python frameworks

This project is supported by the following Python frameworks and libraries:

<p align="center">
  <img alt="Kedro" src="https://img.shields.io/badge/Kedro-Orchestration-243B53?style=for-the-badge">
  <img alt="pandas" src="https://img.shields.io/badge/pandas-Data%20Processing-150458?style=for-the-badge&logo=pandas&logoColor=white">
  <img alt="Great Expectations" src="https://img.shields.io/badge/Great%20Expectations-Validation-FF6319?style=for-the-badge">
  <img alt="NumPy" src="https://img.shields.io/badge/NumPy-Feature%20Engineering-013243?style=for-the-badge&logo=numpy&logoColor=white">
  <img alt="scikit-learn" src="https://img.shields.io/badge/scikit--learn-Modeling-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white">
  <img alt="LightGBM" src="https://img.shields.io/badge/LightGBM-Modeling-02569B?style=for-the-badge">
  <img alt="XGBoost" src="https://img.shields.io/badge/XGBoost-Modeling-FF6600?style=for-the-badge">
  <img alt="MLflow" src="https://img.shields.io/badge/MLflow-Experiment%20Tracking-0194E2?style=for-the-badge&logo=mlflow&logoColor=white">
  <img alt="joblib" src="https://img.shields.io/badge/joblib-Persistence-4B8BBE?style=for-the-badge">
  <img alt="Jupyter" src="https://img.shields.io/badge/Jupyter-EDA%20and%20Reporting-F37626?style=for-the-badge&logo=jupyter&logoColor=white">
  <img alt="Matplotlib" src="https://img.shields.io/badge/Matplotlib-Visualisation-11557C?style=for-the-badge">
  <img alt="Seaborn" src="https://img.shields.io/badge/Seaborn-Visualisation-4B8BBE?style=for-the-badge">
</p>

| Pipeline stage | Python framework or library |
| --- | --- |
| Pipeline orchestration | Kedro |
| Pipeline visualisation | Kedro-Viz |
| Data ingestion and cleaning | pandas |
| Data validation | Great Expectations, pandas |
| Exploratory analysis and reporting | pandas, Matplotlib, Jupyter |
| Feature engineering | pandas, NumPy |
| Train/test split and preprocessing | scikit-learn |
| Model training and tuning | scikit-learn, LightGBM, XGBoost |
| Probability calibration | scikit-learn |
| Experiment tracking | MLflow |
| Model persistence | joblib |

## Exploratory data analysis (EDA)

For the full exploratory analysis, see [`eda.ipynb`](eda.ipynb).

### EDA findings and decisions

#### Data cleaning

| Finding | Decision |
|---|---|
| `no_show` has one missing value among 119,391 rows. | Remove the missing target row with `drop_missing_target_rows` before modelling. |
| `arrival_day`, `checkout_day`, and `num_children` are stored as floating-point values even though their observed non-missing values are integer-valued. | Cast the expected integer fields to nullable `Int64` types with `convert_numeric_column_types`. |
| `num_adults` contains 11,402 word-form values such as `one` and `two`. | Convert the word forms to numeric strings with `num_adults_words_to_numbers` before integer conversion. |
| The singleton missing values affect only one row per field, while `room` and `price` have substantially more missing values. | Drop rows with low missingness using `drop_rows_with_low_missingness`; retain the missing `room` and `price` values for handling in downstream preprocessing. |
| Month labels include inconsistent casing in `arrival_month`, such as `April` and `ApRiL`. | Standardise month labels with `standardize_month_columns`. |
| `checkout_day` contains negative values, including a minimum of `-31`. | Set invalid day-of-month values to missing with `set_invalid_day_of_month_to_missing` before calendar and stay-length features are constructed. |
| Every non-missing `price` value matches the specified `SGD$ amount` or `USD$ amount` pattern. | Parse the currency and numeric amount with `parse_price_currency_and_amount` in feature engineering. |

The raw table contains no exact duplicate rows or duplicate `booking_id`
values. The pipeline nevertheless runs `drop_duplicate_rows` as a defensive
cleaning step; because no duplicates are present, the rows remain unchanged,
and the validation suite also checks row and booking-identifier uniqueness.

#### Feature engineering

| Finding | Decision |
|---|---|
| Every non-missing price value contains either an SGD or USD currency label and a numeric amount. | Parse the currency and amount, then convert USD amounts to SGD. |
| Arrival and checkout month/day fields can be combined into reference-year dates. | Create `stay_length_nights` from 2024 reference-year dates, with invalid or unavailable calendar inputs represented as missing. |
| Booking and arrival months define a cyclic booking lead-time measure. | Create `booking_to_arrival_month_gap`. |
| Adult and child counts define the booking party size. | Create `total_guests`. |
| Total guests, stay length, and SGD price define price-intensity measures. | Create `price_per_guest`, `price_per_night`, and `price_per_guest_per_night`. |
| The chi-square and Mann–Whitney analyses identify candidate relationships with `no_show`. | Retain the engineered features as candidate model inputs and assess them through the modelling workflow. |

## Machine learning pipeline

### Pipeline stages

The pipeline runs through these stages:

1. `data_ingestion`
2. `data_cleaning`
3. `data_validation`
4. `feature_engineering`
5. `train_test_split`
6. `ml_experiment`
7. `pipeline_selection_and_calibration`
8. `holdout_evaluation`
9. `experiment_logging` and `pipeline_persistence`

### Data cleaning

| Pipeline node | Cleaning action | Evidence from EDA | Result |
|---|---|---|---|
| `drop_duplicate_rows` | Remove exact duplicate rows. | The EDA finds no exact duplicate rows or duplicate `booking_id` values. | No rows are removed; uniqueness is also checked during validation. |
| `drop_missing_target_rows` | Remove rows without `no_show`. | One target value is missing. | The modelling target is available for every retained row. |
| `drop_rows_with_low_missingness` | Remove rows with missing values in fields with a missingness rate below `5%`. | Several fields have only one missing value. | Singleton missing values are removed; higher-missingness fields remain for downstream preprocessing. |
| `num_adults_words_to_numbers` | Convert `one` and `two` to numeric strings. | 11,402 word-form adult-count values are observed. | Adult counts can be converted to nullable integer types. |
| `convert_numeric_column_types` | Cast `booking_id`, `no_show`, day fields, and guest-count fields to nullable `Int64`. | Day, child-count, and target values are integer-valued despite raw floating-point storage; adult counts are converted to numeric strings first. | The pipeline’s identifier, target, and integer features have nullable integer types. |
| `standardize_month_columns` | Standardise month labels to title case. | `arrival_month` contains inconsistent casing. | Month labels can be compared with the expected month set. |
| `set_invalid_day_of_month_to_missing` | Replace invalid day values with missing values. | Negative `checkout_day` values are not valid day-of-month values. | Calendar features are constructed only from valid or missing day values. |

### Data validation

The shared validation suite checks column structure, uniqueness, missingness,
types, numeric ranges, month categories, and the price format before and after
cleaning.

The saved raw validation report contains 36 successful expectations out of 69.
The saved cleaned validation report contains 66 successful expectations out of
69. The remaining cleaned-data failures are non-null expectations for
`checkout_day`, `room`, and `price`, which remain missing after the EDA-driven
cleaning actions. Downstream preprocessing fills missing categorical values
with `missing` and retains missing numeric values rather than imputing them.

### Feature engineering

| Feature group | Features | Purpose |
|---|---|---|
| Currency and price | `price_currency`, `price_amount`, `price_amount_sgd` | Parse the raw price and express it in a common currency. |
| Stay timing | `stay_length_nights`, `booking_to_arrival_month_gap` | Represent stay duration and the time between booking and arrival months. |
| Guest count | `total_guests` | Represent the total party size. |
| Price intensity | `price_per_guest`, `price_per_night`, `price_per_guest_per_night` | Represent booking price relative to party size and stay duration. |
| Forecast target | `no_show` | Store the binary prediction target separately from model inputs. |

### Preprocessing and model training

The `no_show` target is separated from the feature columns before modelling,
and the data is divided into an 80%
training set and a 20% holdout test set using a stratified train-test split.
Missing
categorical values are filled with the label `missing` and categorical
features are one-hot encoded. Numeric features are converted to floating-point
values; the preprocessor does not impute missing numeric values.

Candidate Random Forest, LightGBM, and XGBoost pipelines are compared using
five-fold stratified cross-validation and AUROC. The selected pipeline is
calibrated with isotonic regression using five-fold cross-validation on the
training data.

The selected model is LightGBM with the following tuned parameters:

| Parameter | Value |
|---|---:|
| `learning_rate` | `0.05` |
| `min_child_samples` | `20` |
| `n_estimators` | `300` |
| `num_leaves` | `127` |
| `class_weight` | `balanced` |

The pipeline saves experiment results, validation reports, the calibrated
model, and test-set metrics under `results/`.

### Key artifacts

| Artifact | Description |
|---|---|
| `results/ml_experiments/test_set_metrics.json` | Holdout classification and probability metrics |
| `results/ml_experiments/persisted_pipeline_summary.json` | Selected model, parameters, and test metrics |
| `results/ml_experiments/final_no_show_model/best_model.joblib` | Persisted calibrated model |
| `results/validation/noshow_validation_results.json` | Raw-data validation results |
| `results/validation/noshow_cleaned_validation_results.json` | Cleaned-data validation results |
| `notebooks/final_results.ipynb` | Final results report and evaluation plots |

## 4. Results Summary

### Final Pipeline

Multiple candidate pipelines were compared during the ML experiment stage. The best candidate pipeline was selected based on the highest mean cross-validated AUROC, then calibrated on the train set (80%) using isotonic regression.

| Components of final pipeline | Details |
| --- | --- |
| Preprocessor | `preprocessor_v1` |
| Model | `LGBMClassifier` |
| Hyperparameters | `learning_rate=0.05`, `min_child_samples=20`, `n_estimators=300`, `num_leaves=127`, `class_weight="balanced"` |
| Calibration | Isotonic regression |

See [`notebooks/final_results.ipynb`](notebooks/final_results.ipynb) for multiple candidate pipelines compared.

Note: a scikit-learn pipeline is composed of a preprocessor, which feeds engineered and preprocessed features to a machine learning model with specific hyperparameters to make a prediction.

### Final Results

The calibrated pipeline was evaluated on the test set (20%).

First, we plot the ROC curve to visualise the tradeoff between True Positive Rate and False Positive Rate across various classification thresholds. True Positive Rate measures the proportion of actual no-shows that were predicted as no-shows. A higher True Positive Rate means that more no-show instances will be identified in advance and receive intervention. False Positive Rate measures the proportion of actual shows that were incorrectly predicted as no-shows. A higher False Positive Rate means that more guests who would have shown up may receive unnecessary interventions.For example, at the classification threshold where 60% of all no-show instances are identified (True Positive Rate = 0.60), around 15% of show instances are incorrectly predicted as no-shows (False Positive Rate = 0.15). Overall, the pipeline achieves an AUROC of 0.81, indicating that no-show instances are assigned higher no-show probabilities than show instances around 81% of the time, allowing robust discrimination between the two.

<p align="center">
  <img src="notebooks/images/roc_curve.png" alt="ROC curve" width="450"/>

Moreover, we plot the precision-recall curve to visualise the tradeoff between Precision and Recall across various classification thresholds. Precision measures the proportion of predicted no-shows which are actually no-shows. Higher precision means that a larger proportion of interventions will be targeted at actual no-shows. For example, at the classification threshold where 60% of all no-shows are identified (Recall = 0.60), around 71% of the predicted no-shows are actually no-shows (Precision = 0.71).

<p align="center">
  <img src="notebooks/images/precision_recall_curve.png" alt="Precision-recall curve" width="450"/>
</p>

Lastly, we plot the calibration curve to assess whether the predicted no-show probabilities align with the actual observed no-show rates. This is important because well-calibrated probabilities enable reliable estimation of operational quantities such as expected no-shows, expected show-ups, under-occupancy risk, over-occupancy risk, and the potential value of targeted interventions such as reminders. These estimates can then inform hotel operations management decisions, including staffing, inventory management, booking reminders, deposit policies, and overbooking limits, supporting business objectives such as reducing operational inefficiencies, improving resource allocation and protecting revenue.

<p align="center">
  <img src="notebooks/images/calibration_curve.png" alt="Calibration curve" width="450"/>
</p>

See [`notebooks/final_results.ipynb`](notebooks/final_results.ipynb) for the full results.

## How to run

### Clone the repository

```bash
git clone https://github.com/weifengsiew/Machine-Learning-Pipeline-Hotel-No-Shows.git
cd Machine-Learning-Pipeline-Hotel-No-Shows
```

### Environment setup

Use Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Run the workflow

Run all stages:

```bash
./run.sh
```

Run individual stages:

```bash
./scripts/stage1.sh
./scripts/stage2.sh
./scripts/stage3.sh
./scripts/stage4.sh
```

| Script | Runs |
|---|---|
| `scripts/stage1.sh` | Download `noshow.db` |
| `scripts/stage2.sh` | Data ingestion, cleaning, and validation |
| `scripts/stage3.sh` | Feature engineering |
| `scripts/stage4.sh` | Train/test split, model search, calibration, evaluation, logging, and persistence |
| `scripts/all_stages.sh` | Run stages 1–4 in order |

Open [`notebooks/final_results.ipynb`](notebooks/final_results.ipynb) for the
final report.

## To configure a new ML experiment

To add a new candidate pipeline:

1. Add a preprocessor builder in
   [`preprocessor_registry.py`](src/hotel_no_show_prediction/sklearn_pipeline_components/preprocessor_registry.py).
2. Add a model in
   [`model_registry.py`](src/hotel_no_show_prediction/sklearn_pipeline_components/model_registry.py).
3. Add the model's hyperparameter search grid in
   [`conf/base/parameters/model_hyperparams/`](conf/base/parameters/model_hyperparams/).
4. Add the candidate name, preprocessor type, and model key in
   [`ml_experiment.yml`](conf/base/parameters/ml_experiment.yml).

## Repository structure

```text
.
|-- conf/
|   `-- base/
|       |-- catalog/                 # Kedro dataset and artifact definitions
|       `-- parameters/              # Validation, experiment, and model parameters
|-- data/
|   |-- raw/                         # Downloaded noshow.db
|   |-- intermediate/                # Cleaned dataset
|   `-- processed/                   # Feature-engineered dataset
|-- notebooks/
|   |-- eda.ipynb                    # Exploratory data analysis
|   |-- final_results.ipynb          # Final results report
|   `-- images/                      # Report and pipeline images
|-- results/
|   |-- ml_experiments/              # Metrics, model summary, and persisted model
|   |-- mlruns/                      # MLflow tracking data
|   `-- validation/                  # Great Expectations results
|-- scripts/
|   |-- all_stages.sh
|   |-- stage1.sh                    # Download raw data
|   |-- stage2.sh                    # Ingestion, cleaning, and validation
|   |-- stage3.sh                    # Feature engineering
|   `-- stage4.sh                    # Modelling and evaluation
|-- src/
|   `-- hotel_no_show_prediction/
|       |-- pipelines/               # Kedro pipeline nodes and definitions
|       `-- sklearn_pipeline_components/ # Preprocessor and model registries
|-- eda.ipynb
|-- pyproject.toml
|-- requirements.txt
`-- run.sh                           # Full workflow
```
