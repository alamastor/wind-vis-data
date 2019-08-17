from datetime import datetime, timedelta
import glob
import logging
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup
import requests

GFS_BASE_DIR = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
LOG = logging.getLogger(__name__)
GRIB_DIR = Path(__file__).parent.parent / "grib_files"
GFS_HOURS = 180
GFS_INTERVAL= 3


def get_latest_complete_run():
    run_datetime = get_latest_run()
    while run_datetime > datetime(2000, 1, 1):
        if check_cycle_complete(run_datetime):
            return run_datetime
        run_datetime -= timedelta(hours=6)
    raise RuntimeError("No complete GFS cycles found.")


def get_latest_run():
    latest_day = get_latest_run_day()
    req = requests.get(GFS_BASE_DIR + f"/gfs.{latest_day:%Y%m%d}/")
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


def get_latest_run_day():
    req = requests.get(GFS_BASE_DIR)
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


def check_cycle_complete(run: datetime):
    req = requests.get(f"{GFS_BASE_DIR}/gfs.{run:%Y%m%d}/{run:%H}")
    soup = BeautifulSoup(req.content, "html.parser")

    taus = set()
    matcher = re.compile(r"^gfs.t\d\dz.pgrb2b.1p00.f\d\d\d$")
    for link in soup.find_all("a"):
        if matcher.match(link.string):
            taus.add(int(link.string[-3:]))

    return all(x in taus for x in range(0, 243, 3))


def download_run(dt):
    GRIB_DIR.mkdir(parents=True, exist_ok=True)
    for tau in range(0, GFS_HOURS+GFS_INTERVAL, GFS_INTERVAL):
        file_url = (
            f"{GFS_BASE_DIR}/gfs.{dt:%Y%m%d}/{dt:%H}/gfs.t{dt:%H}z.pgrb2.1p00.f{tau:03d}"
        )
        req = requests.get(file_url, stream=True)
        if req.status_code == 200:
            with open(grib_file_path(dt, tau), "wb") as w:
                for chunk in req.iter_content(1024):
                    w.write(chunk)
        else:
            raise RuntimeError(f"Unable to get {file_url}")
        LOG.debug("Downloaded %s",grib_file_path(dt, tau))
    LOG.info("Downloaded GFS run %s", dt)

def grib_file_path(run_datetime, tau):
    return GRIB_DIR/f"gfs_100_{run_datetime:%Y%m%d}_{run_datetime:%H%M}_{tau:03d}.grb2"

def cleanup_grib_files():
    for f in glob.glob(str(GRIB_DIR) + "/*"):
        os.remove(f)