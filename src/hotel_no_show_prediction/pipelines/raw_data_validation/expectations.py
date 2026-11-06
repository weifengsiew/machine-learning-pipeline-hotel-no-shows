"""Great Expectations rules that block cleaning when raw structure is unusable."""

from __future__ import annotations

from great_expectations import ExpectationSuite
from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations import (
    ExpectTableColumnsToMatchOrderedList,
    ExpectTableRowCountToBeBetween,
)
from great_expectations.expectations.expectation import ColumnMapExpectation
from great_expectations.expectations.metrics import (
    ColumnMapMetricProvider,
    column_condition_partial,
)

EXPECTED_COLUMNS = [
    "booking_id",
    "no_show",
    "branch",
    "booking_month",
    "arrival_month",
    "arrival_day",
    "checkout_month",
    "checkout_day",
    "country",
    "first_time",
    "room",
    "price",
    "platform",
    "num_adults",
    "num_children",
]


def _is_hashable(value: object) -> bool:
    try:
        hash(value)
    except TypeError:
        return False
    return True


class _ColumnValuesHashableMetric(ColumnMapMetricProvider):
    condition_metric_name = "column_values.raw_data_gate_hashable"

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        return column.map(_is_hashable)


class ExpectColumnValuesToBeHashable(ColumnMapExpectation):
    """Expect every cell value in a column to support Python hashing."""

    map_metric = "column_values.raw_data_gate_hashable"


def build_raw_data_gate_suite() -> ExpectationSuite:
    """Build the blocking expectations required before cleaning can run."""
    suite = ExpectationSuite(name="raw_data_gate_suite")
    suite.expectations.extend(
        [
            ExpectTableRowCountToBeBetween(min_value=1),
            ExpectTableColumnsToMatchOrderedList(column_list=EXPECTED_COLUMNS),
        ]
    )
    suite.expectations.extend(
        ExpectColumnValuesToBeHashable(column=column, catch_exceptions=True)
        for column in EXPECTED_COLUMNS
    )
    return suite
