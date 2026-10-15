"""Project settings."""

from pathlib import Path


KEDRO_LOGGING_CONFIG = "conf/base/logging.yml"

# File handlers in the logging config need their parent directory to exist
# before Kedro configures logging, including for direct ``kedro run`` calls.
Path("logs").mkdir(exist_ok=True)
