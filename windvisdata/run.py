import time
import logging

from .latest_gfs_to_json import latest_gfs_to_json


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

LOG = logging.getLogger(__name__)
SLEEP_TIME = 5 * 60


def run():
    while True:
        try:
            latest_gfs_to_json()
            time.sleep(SLEEP_TIME)
        except Exception:
            LOG.exception("windvisdata crashed")


