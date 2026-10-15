#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

KEDRO="${KEDRO:-$PROJECT_ROOT/.venv/bin/kedro}"
export KEDRO_DISABLE_TELEMETRY="${KEDRO_DISABLE_TELEMETRY:-1}"
export KEDRO_LOGGING_CONFIG="${KEDRO_LOGGING_CONFIG:-$PROJECT_ROOT/conf/base/logging.yml}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/private/tmp/kedro-mplconfig}"
mkdir -p "$MPLCONFIGDIR" "$PROJECT_ROOT/logs"

printf '\n==> Training, evaluating, logging, and saving model\n'
"$KEDRO" run --namespaces=train_test_split,ml_experiment,pipeline_selection_and_calibration,holdout_evaluation,experiment_logging,pipeline_persistence

printf '\nModel workflow completed.\n'
