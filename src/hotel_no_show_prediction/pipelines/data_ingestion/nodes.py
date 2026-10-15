"""Data ingestion nodes."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_raw_noshow(raw_data_config: dict[str, str]) -> pd.DataFrame:
    """Load no-show data from a SQLite table."""
    try:
        database_path = Path(raw_data_config["path"])
        table_name = raw_data_config["table_name"]
        if not database_path.is_file():
            raise FileNotFoundError(f"SQLite database does not exist: {database_path}")

        with sqlite3.connect(database_path) as connection:
            return pd.read_sql_query(
                f'SELECT * FROM "{table_name}"',
                connection,
            )
    except Exception:
        logger.exception("Failed to load raw data from SQLite")
        raise
