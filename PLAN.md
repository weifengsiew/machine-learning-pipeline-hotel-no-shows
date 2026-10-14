# Data quality and model reliability plan

## Goal

Ensure source and cleaned data are checked before they reach downstream
stages, and validate engineered features before model training. Preserve
uncleaned rows for review and use logs to make data changes and model runs
traceable.

## Log destinations and levels

| Destination | Level | Use |
| --- | --- | --- |
| Console | `INFO` and above | Concise run progress and key data/model summaries. |
| `logs/pipeline.log` | `DEBUG` and above | Detailed diagnostics with timestamp, level, logger name, source file and line, and message. |

Use Kedro's Rich handler for console output and a plain text formatter for the
file. Rotate the file at 10 MB and retain five backups. Configure
`conf/logging.yml` through `KEDRO_LOGGING_CONFIG` for every Kedro invocation.
The repository already ignores `logs/`.

## Highest priority: data gates

### Raw data gate plan

- Preserve the downloaded or reused source file unchanged for traceability.
- Before cleaning, verify that the source file can be read, the configured
  SQLite table exists, the table has rows, and the column names are unique.
- Validate the raw schema against required column names and explicitly
  approved optional columns. Compare names rather than relying on column count
  or order, and allow only raw value formats that the cleaning process is
  designed to handle.
- Record the source checksum/version and a schema summary. Report schema
  differences at DEBUG without logging booking-level rows.
- If the file, table, or required schema is invalid, retain the source and
  validation report for review and stop before cleaning.
- Make successful raw validation a required dependency of the cleaning nodes
  so cleaning cannot run on an unapproved source schema.

### Cleaned data gate plan

- Preserve the original source dataset for traceability.
- During cleaning, separate rows that meet the cleaning contract from rows that
  remain unclean or cannot be interpreted. Retain the latter in a separate
  review copy with reason codes.
- Validate the cleaned rows before saving them as the dataset used by feature
  engineering and later stages. Only rows that pass the cleaned-data contract
  may enter that downstream dataset; quarantined rows are excluded.
- If the cleaned dataset fails a blocking validation check, stop the pipeline
  before downstream stages run.
- Make the validation gate a dependency in the Kedro pipeline graph so later
  stages cannot run without a successful gate.

### Feature-engineered data gate plan

- Validate the feature-engineering output against the approved model input
  schema before the train/test split.
- Check feature names and types, target presence, row-count consistency, and
  agreed constraints on missing or non-finite values.
- Use one approved feature schema for both validation and preprocessing so the
  validator and `preprocessor_registry.py` cannot drift apart.
- If the engineered data fails a blocking check, raise an exception and stop
  before splitting or model training.
- Make the gate a required dependency of `split_features_and_target` so
  downstream modeling cannot bypass it.

## Remaining problems

## 1. Dataset versioning and checksums

The ingestion script reuses an existing database or downloads from a fixed
URL, but runs do not record an immutable dataset version. Results can be hard
to reproduce or compare if the source changes. Reusing a file based only on its
presence can also keep an older dataset in place after the remote source has
been updated.

## 2. Date semantics

Date features are derived from month and day values using a fixed reference
year and a 366-day wrap adjustment. These assumptions can produce incorrect
stay lengths when the source period or calendar convention changes. Because
the source values do not include a year, the constructed dates cannot
distinguish bookings from different years. Errors in stay length also affect
features such as price per night.

## 3. Currency conversion

USD prices are converted with a fixed rate that has no recorded source or
effective date. The resulting SGD price features may be inconsistent with the
booking period or intended exchange-rate policy. If the dataset covers a
different time period, the same rate may no longer represent the intended
conversion. This can shift price-derived model features without an obvious
pipeline failure.

## 4. Artifact traceability

Saved models and summaries do not fully identify the source data, feature
schema, configuration, and software environment used to create them. It can be
difficult to reproduce a result or determine whether a model matches a newer
dataset. A model file by itself does not show which input schema or
transformation assumptions it expects. This makes comparisons and safe reuse
harder when the source data or project dependencies change.

## 5. Missingness threshold and row removal

The fixed 5% missingness rule can remove different numbers of rows as dataset
size and missing-value patterns change. If removed rows are not retained with
reasons, it is hard to review what cleaning discarded. A column's missingness
rate can move across the 5% boundary between datasets, changing whether rows
are dropped or retained. The same cleaning code can therefore produce a
different retained population without a code change.

## 6. Missing derived price ratios

The ratio functions set the denominator to missing when guest count or stay
length is zero, and missing source prices or counts also propagate to the
ratios. This can make `price_per_guest`, `price_per_night`, and
`price_per_guest_per_night` missing while retaining the booking row. Numeric
preprocessing passes these values through without imputation. Changes in their
frequency can affect model fitting and evaluation, but the workflow does not
currently summarize their causes or frequency.

## 7. Class counts, cross-validation, and fit failures

Stratified splitting, cross-validation, and calibration require enough
examples of each target class. With a changed dataset, folds may be invalid or
candidate fits may fail. A smaller or less common no-show class can make the
configured split or folds impossible, or cause calibration to fail later in
the run. Failed candidate fits can also leave model selection with incomplete
results, making the selected model difficult to assess.

## 8. Data loading and source schema changes

The loader queries a configured SQLite path and table without an explicit
preflight check for a missing file, missing table, empty table, or changed
column names. The validation suite checks an exact ordered column list, but
its results currently do not stop the run. A source change can therefore be
reported only after loading and may not prevent later stages from running.

## 9. Silent coercion during cleaning

Numeric conversion uses `errors="coerce"`, so unfamiliar strings can become
missing values without distinguishing them from source values that were
already missing. Adult-count cleaning maps only `one` and `two`, leaving
other string forms to become missing during numeric conversion. Since this
conversion follows the low-missingness row-removal step, the resulting missing
values can pass through cleaning before validation reports them.
