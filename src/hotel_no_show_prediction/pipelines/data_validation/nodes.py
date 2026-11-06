"""Data validation nodes."""

from __future__ import annotations

from typing import Any

import great_expectations as gx
import pandas as pd
from great_expectations import ExpectationSuite

from hotel_no_show_prediction.pipelines.data_validation.expectations import (
    add_basic_expectations as add_basic_expectations_to_suite,
)
from hotel_no_show_prediction.pipelines.data_validation.expectations import (
    add_numeric_range_expectations as add_numeric_range_expectations_to_suite,
)
from hotel_no_show_prediction.pipelines.data_validation.expectations import (
    add_string_expectations as add_string_expectations_to_suite,
)
from hotel_no_show_prediction.pipelines.data_validation.expectations import (
    add_type_expectations as add_type_expectations_to_suite,
)
from hotel_no_show_prediction.pipelines.data_validation.reporting import (
    extract_failed_expectations,
    format_failed_expectations_report,
)

Validator = Any
EXPECTATION_SUITE_NAME = "noshow_validation_suite"


def create_validation_context() -> Any:
    """Create an in-memory Great Expectations context for the current pipeline run.

    Returns:
        Any: Great Expectations context that exists only during the pipeline run.
    """
    return gx.get_context(mode="ephemeral")


def get_validation_table_name(
    validation_config: dict[str, str],
) -> str:
    """Get the table name used for data validation.

    Args:
        validation_config (dict[str, str]): Data validation config containing the table name.

    Returns:
        str: Table name used to label the data being validated.
    """
    return validation_config["table_name"]


def create_dataframe_batch_request(
    validation_context: Any,
    validation_data: pd.DataFrame,
    table_name: str,
) -> tuple[Any, Any]:
    """Prepare no-show data for Great Expectations validation.

    Args:
        validation_context (Any): Great Expectations context used for this validation run.
        validation_data (pd.DataFrame): No-show data to validate.
        table_name (str): Name used to label the data being validated.

    Returns:
        tuple[Any, Any]: Updated Great Expectations context and request pointing to the data to validate.
    """
    data_source = validation_context.data_sources.add_pandas("pandas")
    data_asset = data_source.add_dataframe_asset(name=table_name)
    batch_definition = data_asset.add_batch_definition_whole_dataframe("whole_table")
    batch_request = batch_definition.build_batch_request(
        batch_parameters={"dataframe": validation_data}
    )
    return validation_context, batch_request


def build_expectation_suite() -> ExpectationSuite:
    """Build the validation rules collection for no-show data.

    Returns:
        ExpectationSuite: Validation rules collection for no-show data.
    """
    expectation_suite = gx.ExpectationSuite(name=EXPECTATION_SUITE_NAME)
    add_basic_expectations_to_suite(expectation_suite)
    add_type_expectations_to_suite(expectation_suite)
    add_numeric_range_expectations_to_suite(expectation_suite)
    add_string_expectations_to_suite(expectation_suite)
    return expectation_suite


def create_validator(
    validation_context: Any,
    batch_request: Any,
    expectation_suite: ExpectationSuite,
) -> Validator:
    """Create the object that checks no-show data against validation rules.

    Args:
        validation_context (Any): Great Expectations context containing the data to validate.
        batch_request (Any): Request pointing to the no-show data to validate.
        expectation_suite (ExpectationSuite): Validation rules collection used to check the no-show data.

    Returns:
        Validator: Object used to run the validation checks.
    """
    return validation_context.get_validator(
        batch_request=batch_request,
        expectation_suite=expectation_suite,
    )


def run_validation(validator: Validator) -> dict[str, Any]:
    """Run validation checks on no-show data.

    Args:
        validator (Validator): Object used to run the validation checks.

    Returns:
        dict[str, Any]: Validation results converted to a JSON-serializable dictionary.
    """
    validation_result = validator.validate()
    return validation_result.to_json_dict()


def extract_failed_expectation_rows(
    validation_results: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract failed validation checks from validation results.

    Args:
        validation_results (dict[str, Any]): Validation results from Great Expectations.

    Returns:
        list[dict[str, Any]]: Failed validation checks formatted as rows.
    """
    return extract_failed_expectations(validation_results)


def build_failed_expectations_report(
    failed_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build a report of failed validation checks.

    Args:
        failed_rows (list[dict[str, Any]]): Failed validation checks formatted as rows.

    Returns:
        pd.DataFrame: Failed validation report ready to save as CSV.
    """
    return format_failed_expectations_report(failed_rows)
