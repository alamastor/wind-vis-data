import logging
from pathlib import Path
import re
from datetime import datetime, timedelta
from typing import Type

import requests
from bs4 import BeautifulSoup


GFS_BASE_DIR_URL = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
LOG = logging.getLogger(__name__)
EARLIEST_ALLOWED_RUN = datetime(2021, 6, 1)


def download_grib_file(run_datetime: datetime, tau: int, *, target_file: Path) -> None:
    req = requests.get(_grib_file_url(run_datetime, tau), stream=True)
    if req.status_code == 200:
        with open(target_file, "wb") as w:
            for chunk in req.iter_content(1024):
                w.write(chunk)
    else:
        raise RuntimeError(f"Unable to get {_grib_file_url(run_datetime, tau)}")
    LOG.info("Downloaded %s", target_file)


def get_latest_complete_run() -> datetime:
    run_datetime = _get_latest_run()
    while run_datetime > EARLIEST_ALLOWED_RUN:
        if _complete_run_available(run_datetime):
            return run_datetime
        run_datetime -= timedelta(hours=6)
    raise RuntimeError("No complete GFS cycles found.")


def _get_latest_run() -> datetime:
    latest_day = _get_latest_run_day()
    req = requests.get(GFS_BASE_DIR_URL + f"/gfs.{latest_day:%Y%m%d}/")
    soup = BeautifulSoup(req.content, "html.parser")
    hours = set()
    for link in soup.find_all("a"):
        try:
            hours.add(int(link.string[:-1]))
        except Exception:
            pass
    latest_run = latest_day + timedelta(hours=max(hours))
    LOG.debug("Latest available cycle: %s", latest_run)

    return latest_run


def _get_latest_run_day():
    req = requests.get(GFS_BASE_DIR_URL)
    soup = BeautifulSoup(req.content, "html.parser")
    days = set()
    for link in soup.find_all("a"):
        try:
            days.add(datetime.strptime(link.string, "gfs.%Y%m%d/"))
        except ValueError:
            # Link date parse failed
            pass
    latest_day = max(days)
    LOG.debug("Latest available day: %s", latest_day)
    return latest_day


def _complete_run_available(run: datetime):
    req = requests.get(
        f"{GFS_BASE_DIR_URL}/gfs.{run:%Y%m%d}/{run:%H}/atmos", timeout=10
    )
    soup = BeautifulSoup(req.content, "html.parser")

    taus = set()
    matcher = re.compile(r"^gfs.t\d\dz.pgrb2b.1p00.f\d\d\d$")
    for link in soup.find_all("a"):
        if matcher.match(link.string):
            taus.add(int(link.string[-3:]))

    return all(x in taus for x in range(0, 243, 3))


def _grib_file_url(run_datetime: datetime, tau: int):
    return (
        f"{GFS_BASE_DIR_URL}/gfs.{run_datetime:%Y%m%d}/"
        f"{run_datetime:%H}/atmos/gfs.t{run_datetime:%H}z.pgrb2.1p00.f{tau:03d}"
    )
