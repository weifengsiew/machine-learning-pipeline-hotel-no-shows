"""Great Expectations validation pipelines for tabular no-show data."""

from __future__ import annotations

from kedro.pipeline import Pipeline, node

from hotel_no_show_prediction.pipelines.cleaned_data_validation.nodes import (
    build_expectation_suite,
    build_failed_expectations_report,
    create_dataframe_batch_request,
    create_validation_context,
    create_validator,
    extract_failed_expectation_rows,
    get_validation_table_name,
    run_validation,
)


def create_validation_pipeline(
    *,
    prefix: str,
    validation_data: str,
    node_prefix: str | None = None,
) -> Pipeline:
    """Build a reusable GX pipeline for a named input dataframe."""
    node_prefix = node_prefix or prefix
    suite = f"{prefix}_expectation_suite"
    context = f"{prefix}_validation_context"
    table_name = f"{prefix}_validation_table_name"
    context_with_batch = f"{prefix}_validation_context_with_batch"
    batch_request = f"{prefix}_validation_batch_request"
    validator = f"{prefix}_validator"
    validation_results = f"{prefix}_validation_results"
    failed_rows = f"{prefix}_failed_expectation_rows"

    return Pipeline(
        [
            node(
                func=build_expectation_suite,
                inputs=None,
                outputs=suite,
                name=f"{node_prefix}_build_expectation_suite",
            ),
            node(
                func=create_validation_context,
                inputs=None,
                outputs=context,
                name=f"{node_prefix}_create_validation_context",
            ),
            node(
                func=get_validation_table_name,
                inputs="params:validation",
                outputs=table_name,
                name=f"{node_prefix}_get_validation_table_name",
            ),
            node(
                func=create_dataframe_batch_request,
                inputs=[context, validation_data, table_name],
                outputs=[context_with_batch, batch_request],
                name=f"{node_prefix}_create_dataframe_batch_request",
            ),
            node(
                func=create_validator,
                inputs=[context_with_batch, batch_request, suite],
                outputs=validator,
                name=f"{node_prefix}_create_validator",
            ),
            node(
                func=run_validation,
                inputs=validator,
                outputs=validation_results,
                name=f"{node_prefix}_run_validation",
            ),
            node(
                func=extract_failed_expectation_rows,
                inputs=validation_results,
                outputs=failed_rows,
                name=f"{node_prefix}_extract_failed_expectation_rows",
            ),
            node(
                func=build_failed_expectations_report,
                inputs=failed_rows,
                outputs=f"{prefix}_validation_failures",
                name=f"{node_prefix}_build_failed_expectations_report",
            ),
        ]
    )


def create_pipeline(**kwargs) -> Pipeline:
    """Validate cleaned data with the shared Great Expectations suite."""
    return create_validation_pipeline(
        prefix="cleaned",
        validation_data="noshow_cleaned",
    )
