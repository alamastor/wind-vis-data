import logging
import os
import time

import sentry_sdk

from .latest_gfs_to_json import latest_gfs_to_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

LOG = logging.getLogger(__name__)
SLEEP_TIME = 5 * 60

if SENTRY_URL := os.environ.get("SENTRY_URL"):
    sentry_sdk.init(SENTRY_URL)


def run():
    while True:
        try:
            latest_gfs_to_json()
            time.sleep(SLEEP_TIME)
        except Exception:
            LOG.exception("windvisdata crashed")
            raise
