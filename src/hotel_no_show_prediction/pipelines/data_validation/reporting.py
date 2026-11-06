"""Validation failure reporting helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd

CSV_COLUMNS = [
    "expectation_type",
    "affected_field",
    "unexpected_count",
    "unexpected_percent",
    "examples",
]


def get_affected_field(expectation_kwargs: dict[str, Any]) -> str:
    """Get the field affected by a failed validation check.

    Args:
        expectation_kwargs (dict[str, Any]): Arguments from the validation rule.

    Returns:
        str: Affected column, affected column list, or "table" for table-level checks.
    """
    if "column" in expectation_kwargs:
        return expectation_kwargs["column"]
    if "column_list" in expectation_kwargs:
        return ", ".join(expectation_kwargs["column_list"])
    return "table"


def get_unexpected_percent(expectation_result: dict[str, Any]) -> float | None:
    """Get the percentage of rows that failed a validation check.

    Args:
        expectation_result (dict[str, Any]): Result details from a validation check.

    Returns:
        float | None: Percentage of failed rows, if reported by Great Expectations.
    """
    if "unexpected_percent_total" in expectation_result:
        return expectation_result["unexpected_percent_total"]
    return None


def format_examples(examples: list[Any]) -> str:
    """Format example failed values for the validation report.

    Args:
        examples (list[Any]): Example values that failed a validation check.

    Returns:
        str: Unique example values joined into one semicolon-separated string.
    """
    unique_examples = pd.Series(examples, dtype="object").drop_duplicates().head(30)
    return "; ".join(unique_examples.astype(str))


def extract_failed_expectations(validation_results: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert failed validation checks into rows for the validation report.

    Args:
        validation_results (dict[str, Any]): Validation results from Great Expectations.

    Returns:
        list[dict[str, Any]]: Failed validation checks formatted as rows.
    """
    failed_rows = []
    for expectation_result in validation_results["results"]:
        if expectation_result["success"]:
            continue

        expectation_config = expectation_result["expectation_config"]
        expectation_kwargs = expectation_config["kwargs"]
        result_details = expectation_result.get("result", {})

        failed_rows.append(
            {
                "expectation_type": expectation_config["type"],
                "affected_field": get_affected_field(expectation_kwargs),
                "unexpected_count": result_details.get("unexpected_count"),
                "unexpected_percent": get_unexpected_percent(result_details),
                "examples": format_examples(
                    result_details.get("partial_unexpected_list", [])
                ),
            }
        )

    return failed_rows


def format_failed_expectations_report(
    failed_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    """Convert failed validation rows into a report DataFrame.

    Args:
        failed_rows (list[dict[str, Any]]): Failed validation checks formatted as rows.

    Returns:
        pd.DataFrame: Failed validation report with columns ordered for CSV output.
    """
    return pd.DataFrame(failed_rows, columns=CSV_COLUMNS)
