"""Data cleaning nodes."""

from __future__ import annotations

import calendar

import pandas as pd

TARGET_COLUMN = "no_show"
MISSING_DROP_THRESHOLD = 0.05
MONTH_MAPPINGS = {month.lower(): month for month in calendar.month_name if month}
DAYS_IN_MONTH_BY_NAME = {
    month: calendar.monthrange(2024, month_number)[1]
    for month_number, month in enumerate(calendar.month_name)
    if month
}
ADULT_COUNT_MAPPINGS = {"one": "1", "two": "2"}
NUMERIC_COLUMN_TYPES = {
    "booking_id": "Int64",
    "no_show": "Int64",
    "arrival_day": "Int64",
    "checkout_day": "Int64",
    "num_adults": "Int64",
    "num_children": "Int64",
}


def drop_duplicate_rows(noshow: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate no-show data rows.

    Args:
        noshow (pd.DataFrame): No-show data.

    Returns:
        pd.DataFrame: No-show data with exact duplicate rows removed.
    """
    return noshow.drop_duplicates().copy()


def drop_missing_target_rows(noshow: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with missing target values.

    Args:
        noshow (pd.DataFrame): No-show data.

    Returns:
        pd.DataFrame: No-show data with missing target rows removed.
    """
    return noshow.dropna(subset=[TARGET_COLUMN]).copy()


def drop_rows_with_low_missingness(noshow: pd.DataFrame) -> pd.DataFrame:
    """Remove rows when only a small fraction of values is missing in that column.

    Args:
        noshow (pd.DataFrame): No-show data.

    Returns:
        pd.DataFrame: No-show data with rows removed for columns below the missingness threshold.
    """
    missing_count_by_column = noshow.isna().sum()
    missing_rate_by_column = missing_count_by_column / len(noshow)
    low_missingness_columns = [
        column_name
        for column_name, missing_rate in missing_rate_by_column.items()
        if 0 < missing_rate < MISSING_DROP_THRESHOLD
    ]
    return noshow.dropna(subset=low_missingness_columns).copy()


def standardize_month_columns(noshow: pd.DataFrame) -> pd.DataFrame:
    """Standardize month names to title case, e.g. "jAnuary" to "January".

    Args:
        noshow (pd.DataFrame): No-show data.

    Returns:
        pd.DataFrame: No-show data with month names standardized to title case.
    """
    cleaned_data = noshow.copy()
    month_columns = [
        column_name
        for column_name in cleaned_data.select_dtypes(include="object").columns
        if column_name.endswith("_month")
    ]

    for column_name in month_columns:
        is_non_missing = cleaned_data[column_name].notna()
        cleaned_data.loc[is_non_missing, column_name] = (
            cleaned_data.loc[is_non_missing, column_name]
            .astype(str)
            .str.strip()
            .str.title()
        )

    return cleaned_data


def num_adults_words_to_numbers(noshow: pd.DataFrame) -> pd.DataFrame:
    """Convert words in num_adults to numeric strings, e.g. "one" to "1".

    Args:
        noshow (pd.DataFrame): No-show data.

    Returns:
        pd.DataFrame: No-show data with num_adults words converted to numeric strings.
    """
    cleaned_data = noshow.copy()
    cleaned_data["num_adults"] = (
        cleaned_data["num_adults"].astype(str).str.lower().replace(ADULT_COUNT_MAPPINGS)
    )

    return cleaned_data


def convert_numeric_column_types(noshow: pd.DataFrame) -> pd.DataFrame:
    """Convert columns listed in NUMERIC_COLUMN_TYPES to nullable integer type.

    Args:
        noshow (pd.DataFrame): No-show data.

    Returns:
        pd.DataFrame: No-show data with columns in NUMERIC_COLUMN_TYPES converted to nullable integer type.
    """
    cleaned_data = noshow.copy()

    for column_name, target_dtype in NUMERIC_COLUMN_TYPES.items():
        cleaned_data[column_name] = pd.to_numeric(
            cleaned_data[column_name], errors="coerce"
        ).astype(target_dtype)

    return cleaned_data


def set_invalid_day_of_month_to_missing(noshow: pd.DataFrame) -> pd.DataFrame:
    """Set day values outside the valid range for their month to missing, e.g. February 31.

    Args:
        noshow (pd.DataFrame): No-show data.

    Returns:
        pd.DataFrame: No-show data with invalid day-of-month values set to missing.
    """
    cleaned_data = noshow.copy()
    month_columns = [
        column_name
        for column_name in cleaned_data.columns
        if column_name.endswith("_month")
    ]

    for month_column in month_columns:
        day_column = f"{month_column.removesuffix('_month')}_day"
        if day_column not in cleaned_data:
            continue

        standardized_months = cleaned_data[month_column].map(
            lambda month_name: MONTH_MAPPINGS.get(str(month_name).strip().lower())
        )
        max_day = standardized_months.map(DAYS_IN_MONTH_BY_NAME)
        is_invalid_day = ~cleaned_data[day_column].between(1, max_day)
        cleaned_data.loc[is_invalid_day, day_column] = pd.NA

    return cleaned_data
