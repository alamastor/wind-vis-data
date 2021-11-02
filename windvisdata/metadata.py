import json
from datetime import datetime, timezone
from pathlib import Path
import logging

import numpy as np


LOG = logging.getLogger(__name__)


def create_metadata_file(
    *, run_datetime: datetime, max_wind_speed: float, metadata_file: Path
):
    LOG.info("Writing metadata file.")
    with open(metadata_file, "w") as w:
        json.dump(
            {
                "run": run_datetime.replace(tzinfo=timezone.utc).isoformat(),
                "maxWindSpeed": int(np.ceil(max_wind_speed)),
            },
            w,
        )


def read_run_datetime(metadata_file: Path):
    try:
        with open(metadata_file) as r:
            return datetime.fromisoformat(json.load(r)["run"]).replace(tzinfo=None)
    except Exception:
        LOG.warning("Reading cycle file failed.")
