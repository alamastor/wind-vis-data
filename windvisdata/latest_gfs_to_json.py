from datetime import datetime
import json
import logging
from pathlib import Path

import numpy as np
import pygrib

from . import gfs_download

LOG = logging.getLogger(__name__)
JSON_DIR = Path(__file__).parent.parent / "json_files"


def latest_gfs_to_json():
    latest_run = gfs_download.get_latest_complete_run()
    previous_run = cycle_file_datetime()
    if previous_run and latest_run <= previous_run:
        LOG.info("Latest run %s has already been processed, doing nothing.", latest_run)
        return
    LOG.info("Processing latest run %s.", latest_run)
    gfs_download.download_run(latest_run)
    gfs_run_to_json(latest_run)
    write_cycle_file(latest_run)
    gfs_download.cleanup_grib_files()
    LOG.info("completed processing run %s", latest_run)


def run_max_wind_speed(run_datetime):
    max_wind_speed = 0
    for tau in range(
        0, gfs_download.GFS_HOURS + gfs_download.GFS_INTERVAL, gfs_download.GFS_INTERVAL
    ):
        grib_data = pygrib.open(str(gfs_download.grib_file_path(run_datetime, tau)))
        u_data = grib_data.select(name="U component of wind")[0]["values"]
        v_data = grib_data.select(name="V component of wind")[0]["values"]
        max_wind_speed = max(np.max(np.sqrt(u_data ** 2 + v_data ** 2)), max_wind_speed)
    return max_wind_speed


def gfs_run_to_json(run_datetime):
    for tau in range(
        0, gfs_download.GFS_HOURS + gfs_download.GFS_INTERVAL, gfs_download.GFS_INTERVAL
    ):
        grib_to_json(run_datetime, tau)


def grib_to_json(run_datetime, tau):
    JSON_DIR.mkdir(exist_ok=True)
    grib_data = pygrib.open(str(gfs_download.grib_file_path(run_datetime, tau)))
    u_data = grib_data.select(name="U component of wind")[0]["values"]
    v_data = grib_data.select(name="V component of wind")[0]["values"]

    data_1_deg = {}
    data_1_deg["uData"] = []
    data_1_deg["vData"] = []
    data_2_deg = {}
    data_2_deg["uData"] = []
    data_2_deg["vData"] = []
    for x in range(360):
        data_1_deg["uData"].append([])
        data_1_deg["vData"].append([])
        if x % 2 == 0:
            data_2_deg["uData"].append([])
            data_2_deg["vData"].append([])

        for y in range(180, -1, -1):
            data_1_deg["uData"][x].append(round(float(u_data[y][x])))
            data_1_deg["vData"][x].append(round(float(v_data[y][x])))
            if y % 2 == 0:
                data_2_deg["uData"][x // 2].append(round(float(u_data[y][x])))
                data_2_deg["vData"][x // 2].append(round(float(v_data[y][x])))

    json_1_deg_path = JSON_DIR / f"gfs_100_{run_datetime:%Y%m%d_%H%M%S}_{tau:03d}.json"
    with open(json_1_deg_path, "w") as w:
        json.dump({"gfsData": data_1_deg}, w)
    LOG.info("created %s", json_1_deg_path)

    json_2_deg_path = JSON_DIR / f"gfs_200_{run_datetime:%Y%m%d_%H%M%S}_{tau:03d}.json"
    with open(json_2_deg_path, "w") as w:
        json.dump({"gfsData": data_2_deg}, w)
    LOG.info("created %s", json_2_deg_path)


def cycle_file_datetime():
    JSON_DIR.mkdir(exist_ok=True)
    try:
        with open(JSON_DIR / "cycle.json") as r:
            return datetime.strptime(json.load(r)["cycle"], r"%Y%m%d_%H%M%S")
    except Exception:
        LOG.warning("Reading cycle file failed.")


def write_cycle_file(run_datetime):
    JSON_DIR.mkdir(exist_ok=True)
    with open(JSON_DIR / "cycle.json", "w") as w:
        json.dump(
            {
                "cycle": f"{run_datetime:%Y%m%d_%H%M%S}",
                "maxWindSpeed": int(np.ceil(run_max_wind_speed(run_datetime))),
            },
            w,
        )
