# Raw data gate

This gate runs immediately after SQLite ingestion and before `data_cleaning`:

- The raw gate checks that the source matches the pipeline contract and that cleaning can run.

## Fail versus report

| Finding | Gate action | Reason |
| --- | --- | --- |
| Database file is missing/unreadable, table is missing, or query fails | Fail | The pipeline has no usable input. |
| Query returns zero rows | Fail | There is no data to clean. |
| Duplicate, missing, unexpected, or misordered columns | Fail | This project’s cleaners expect the fixed 15-column schema. |
| Unhashable cell value | Fail | `drop_duplicates()` cannot process it. |
| A cleaning function raises on the raw frame | Fail | The pipeline cannot complete its cleaning step. |
| Missing values, duplicate rows, invalid month/day pairs, numeric values coerced to missing, unknown categories, or malformed price strings | Report and continue | These findings do not prevent cleaning from running. |

## Logging configuration

Use Kedro’s project logging configuration at `conf/base/logging.yml`. Set the root logger to `DEBUG`; handler levels are thresholds, so higher severity records appear in each applicable file.

| Destination | Minimum level | File contents |
| --- | --- | --- |
| Rich console | `INFO` | Info, warning, error, and critical |
| `logs/debug.log` | `DEBUG` | All levels |
| `logs/info.log` | `INFO` | Info and above |
| `logs/warning.log` | `WARNING` | Warning and above |
| `logs/error.log` | `ERROR` | Error and critical |

Use rotating file handlers (for example, 10 MB per file with 5 backups), a file format with timestamp/level/logger/message, and `disable_existing_loggers: False`. Create `logs/` before starting Kedro; it is excluded from Git. Set the `hotel_no_show_prediction` logger to `DEBUG` so project debug messages reach the root handlers.

```yaml
version: 1
disable_existing_loggers: false

formatters:
  file:
    format: "%(asctime)s %(levelname)s %(name)s: %(message)s"

handlers:
  console:
    class: kedro.logging.RichHandler
    level: INFO
    rich_tracebacks: true
  debug_file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: file
    filename: logs/debug.log
    maxBytes: 10485760
    backupCount: 5
    encoding: utf8
  info_file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: file
    filename: logs/info.log
    maxBytes: 10485760
    backupCount: 5
    encoding: utf8
  warning_file:
    class: logging.handlers.RotatingFileHandler
    level: WARNING
    formatter: file
    filename: logs/warning.log
    maxBytes: 10485760
    backupCount: 5
    encoding: utf8
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: file
    filename: logs/error.log
    maxBytes: 10485760
    backupCount: 5
    encoding: utf8

loggers:
  hotel_no_show_prediction:
    level: DEBUG
  kedro:
    level: INFO

root:
  level: DEBUG
  handlers: [console, debug_file, info_file, warning_file, error_file]
```

In each module, use `logger = logging.getLogger(__name__)`. Log an exception once at the operation boundary with `logger.exception(...)`, then re-raise so the pipeline stops.

For a SQLite loading failure, log the exception and traceback, then re-raise so the pipeline stops:

```python
try:
    raw_data = load_raw_noshow(config)
except Exception:
    logger.exception("Failed to load raw data from SQLite")
    raise
```

`logger.exception()` records the traceback when called inside an `except` block; it does not stop execution by itself. Re-raising preserves the failure for Kedro and prevents later steps from running with missing input.

## Structural gate with Great Expectations

Use a blocking Great Expectations suite on the loaded DataFrame. It checks for at least one row, the exact ordered 15-column schema, and hashable cell values. The hashability rule is a custom column expectation.

The raw validation node collects all failed expectations and raises one `ValueError` with the failures. It logs the exception once at that boundary and re-raises so cleaning does not run.

## Cleaning-step failure

If a cleaning function raises:

- Log the error and traceback, then re-raise to stop the pipeline.
- Do not let downstream cleaning nodes run with a missing or incomplete output.

```python
def run_cleaning_step(step, frame):
    try:
        return step(frame)
    except Exception:
        logger.exception("Cleaning step %s failed; stopping the pipeline", step.__name__)
        raise
```

Use this wrapper at the node boundary if you want each cleaning failure logged explicitly. Re-raising preserves the original exception and traceback for Kedro.
