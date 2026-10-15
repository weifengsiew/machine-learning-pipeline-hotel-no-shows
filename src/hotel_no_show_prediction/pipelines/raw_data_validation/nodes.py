"""Raw-data gate result handling."""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def require_raw_gate_to_pass(
    failed_expectations_report: pd.DataFrame,
    raw_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Raise on structural failures; otherwise pass the raw frame downstream."""
    try:
        if not failed_expectations_report.empty:
            raise ValueError(
                "Raw data gate failed:\n"
                + failed_expectations_report.to_string(index=False)
            )
    except Exception:
        logger.exception("Raw data Great Expectations gate failed")
        raise

    return raw_frame
