"""Data ingestion nodes."""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd


def load_raw_noshow(raw_data_config: dict[str, str]) -> pd.DataFrame:
    """Load no-show data from a SQLite table.

    Args:
        raw_data_config (dict[str, str]): Config containing the SQLite database path and table name.

    Returns:
        pd.DataFrame: Loaded no-show data.
    """
    database_path = Path(raw_data_config["path"])
    table_name = raw_data_config["table_name"]

    with sqlite3.connect(database_path) as connection:
        return pd.read_sql_query(
            f'SELECT * FROM "{table_name}"',
            connection,
        )
