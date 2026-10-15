#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

KEDRO="${KEDRO:-$PROJECT_ROOT/.venv/bin/kedro}"
export KEDRO_DISABLE_TELEMETRY="${KEDRO_DISABLE_TELEMETRY:-1}"
export KEDRO_LOGGING_CONFIG="${KEDRO_LOGGING_CONFIG:-$PROJECT_ROOT/conf/logging.yml}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/private/tmp/kedro-mplconfig}"
mkdir -p "$MPLCONFIGDIR" "$PROJECT_ROOT/logs"

printf '\n==> Running data cleaning and validation\n'
"$KEDRO" run --namespaces=data_ingestion,raw_data_validation,data_cleaning,cleaned_data_validation

printf '\nData cleaning and validation completed\n'
