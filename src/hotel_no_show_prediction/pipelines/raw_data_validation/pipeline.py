"""Raw structure gate and data-quality validation pipelines."""

from __future__ import annotations

from kedro.pipeline import Pipeline, node

from hotel_no_show_prediction.pipelines.cleaned_data_validation.pipeline import (
    create_validation_pipeline,
)
from hotel_no_show_prediction.pipelines.cleaned_data_validation.nodes import (
    build_failed_expectations_report,
    create_dataframe_batch_request,
    create_validation_context,
    create_validator,
    extract_failed_expectation_rows,
    get_validation_table_name,
    run_validation,
)
from hotel_no_show_prediction.pipelines.raw_data_validation.expectations import (
    build_raw_data_gate_suite,
)
from hotel_no_show_prediction.pipelines.raw_data_validation.nodes import (
    require_raw_gate_to_pass,
)

RAW_STRUCTURE_PREFIX = "raw1"
RAW_QUALITY_PREFIX = "raw2"


def create_pipeline(**kwargs) -> Pipeline:
    """Run the raw structure gate, then raw data-quality diagnostics."""
    raw_structure_validation = Pipeline(
        [
            node(
                func=build_raw_data_gate_suite,
                inputs=None,
                outputs=f"{RAW_STRUCTURE_PREFIX}_expectation_suite",
                name=f"{RAW_STRUCTURE_PREFIX}_build_expectation_suite",
            ),
            node(
                func=create_validation_context,
                inputs=None,
                outputs=f"{RAW_STRUCTURE_PREFIX}_validation_context",
                name=f"{RAW_STRUCTURE_PREFIX}_create_validation_context",
            ),
            node(
                func=get_validation_table_name,
                inputs="params:validation",
                outputs=f"{RAW_STRUCTURE_PREFIX}_validation_table_name",
                name=f"{RAW_STRUCTURE_PREFIX}_get_validation_table_name",
            ),
            node(
                func=create_dataframe_batch_request,
                inputs=[
                    f"{RAW_STRUCTURE_PREFIX}_validation_context",
                    "raw_noshow",
                    f"{RAW_STRUCTURE_PREFIX}_validation_table_name",
                ],
                outputs=[
                    f"{RAW_STRUCTURE_PREFIX}_validation_context_with_batch",
                    f"{RAW_STRUCTURE_PREFIX}_validation_batch_request",
                ],
                name=(
                    f"{RAW_STRUCTURE_PREFIX}_create_dataframe_batch_request"
                ),
            ),
            node(
                func=create_validator,
                inputs=[
                    f"{RAW_STRUCTURE_PREFIX}_validation_context_with_batch",
                    f"{RAW_STRUCTURE_PREFIX}_validation_batch_request",
                    f"{RAW_STRUCTURE_PREFIX}_expectation_suite",
                ],
                outputs=f"{RAW_STRUCTURE_PREFIX}_validator",
                name=f"{RAW_STRUCTURE_PREFIX}_create_validator",
            ),
            node(
                func=run_validation,
                inputs=f"{RAW_STRUCTURE_PREFIX}_validator",
                outputs=f"{RAW_STRUCTURE_PREFIX}_validation_results",
                name=f"{RAW_STRUCTURE_PREFIX}_run_validation",
            ),
            node(
                func=extract_failed_expectation_rows,
                inputs=f"{RAW_STRUCTURE_PREFIX}_validation_results",
                outputs=f"{RAW_STRUCTURE_PREFIX}_failed_expectation_rows",
                name=f"{RAW_STRUCTURE_PREFIX}_extract_failed_expectation_rows",
            ),
            node(
                func=build_failed_expectations_report,
                inputs=f"{RAW_STRUCTURE_PREFIX}_failed_expectation_rows",
                outputs=f"{RAW_STRUCTURE_PREFIX}_validation_failures",
                name=f"{RAW_STRUCTURE_PREFIX}_build_failed_expectations_report",
            ),
            node(
                func=require_raw_gate_to_pass,
                inputs=[f"{RAW_STRUCTURE_PREFIX}_validation_failures", "raw_noshow"],
                outputs="raw_noshow_validated",
                name=f"{RAW_STRUCTURE_PREFIX}_require_gate_to_pass",
            ),
        ]
    )
    raw_quality_validation = create_validation_pipeline(
        prefix=RAW_QUALITY_PREFIX,
        validation_data="raw_noshow_validated",
        node_prefix=RAW_QUALITY_PREFIX,
    )
    return raw_structure_validation + raw_quality_validation
