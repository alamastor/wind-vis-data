import logging
import os
import time
import itertools
from pathlib import Path
from datetime import datetime, timedelta, timezone

import sentry_sdk

from . import gfs_download, metadata, grib_data


JSON_DIR = Path(__file__).parent.parent / "json_files"
JSON_DIR.mkdir(exist_ok=True)
JSON_KEEP_WINDOW = timedelta(hours=48)
LOG = logging.getLogger(__name__)
SLEEP_TIME = 5 * 60

if SENTRY_URL := os.environ.get("SENTRY_URL"):
    sentry_sdk.init(SENTRY_URL)

METADATA_FILE = JSON_DIR / "metadata.json"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

PARAMS = [
    ("U component of wind", "wind_u_sfc", "m s**-1"),
    ("V component of wind", "wind_v_sfc", "m s**-1"),
    ("Temperature", "temp", "K"),
]
RESOLUTIONS = [1, 2]


def run():
    while True:
        try:
            _try_to_download()
        except Exception:
            LOG.exception("windvisdata crashed")
            raise

        grib_data.purge_all_grib_files()
        clean_up_old_json_files()
        LOG.debug("Waiting for %s seconds." % SLEEP_TIME)
        time.sleep(SLEEP_TIME)


def _try_to_download():
    LOG.debug(
        "Latest available run is %s."
        % (latest_run := gfs_download.get_latest_complete_run())
    )
    LOG.debug(
        "Latest processed run is %s."
        % (previous_run := metadata.read_run_datetime(METADATA_FILE))
    )
    if previous_run and latest_run <= previous_run:
        LOG.info(
            "Latest available run %s has already been processed, doing nothing.",
            latest_run,
        )
        return

    LOG.info("Processing latest run %s.", latest_run)

    grib_dataset = grib_data.GribDataset(latest_run)

    for tau in grib_dataset.taus:
        gfs_download.download_grib_file(
            grib_dataset.run_datetime,
            tau,
            target_file=grib_dataset.file_path(tau),
        )
        for (
            grib_param_name,
            json_param_name,
            unit,
        ), resolution in itertools.product(PARAMS, RESOLUTIONS):
            grib_dataset.tau_to_json(
                tau,
                grib_param_name,
                unit,
                json_file_path(
                    grib_dataset.run_datetime,
                    tau,
                    resolution,
                    json_param_name,
                ),
                target_resolution=resolution,
            )

    metadata.create_metadata_file(
        run_datetime=latest_run,
        max_wind_speed=grib_dataset.max_wind_speed,
        metadata_file=METADATA_FILE,
    )

    LOG.info("completed processing run %s", latest_run)


def json_file_path(run_datetime: datetime, tau: int, resolution: float, param: str):
    return (
        JSON_DIR
        / f"gfs_{resolution*100:03d}_{run_datetime.replace(tzinfo=timezone.utc).isoformat()}_{tau:03d}_{param}.json"
    )


def json_file_run(json_file: Path):
    return datetime.fromisoformat(json_file.name.split("_")[2]).replace(tzinfo=None)


def clean_up_old_json_files():
    latest_cycle = metadata.read_run_datetime(METADATA_FILE)
    if latest_cycle is not None:
        for file in JSON_DIR.glob("gfs_*.json"):
            if json_file_run(file) < latest_cycle - JSON_KEEP_WINDOW:
                file.unlink()
