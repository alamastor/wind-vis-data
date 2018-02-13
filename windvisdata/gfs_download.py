from datetime import datetime, timedelta
import logging
import os
import re

from bs4 import BeautifulSoup
import requests

GFS_BASE_DIR = 'http://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod'
LOG = logging.getLogger(__name__)
GRIB_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../grib_files'


def get_latest_cycle():
    if not os.path.exists(GRIB_DIR):
        os.makedirs(GRIB_DIR)

    # Get latest cycle link
    req = requests.get(GFS_BASE_DIR)
    soup = BeautifulSoup(req.content, 'html.parser')
    cycles = []
    for link in soup.find_all('a'):
        try:
            cycles.append(datetime.strptime(link['href'], 'gfs.%Y%m%d%H/'))
        except ValueError as e:
            # Link date parse failed
            pass
    latest_cycle = max(cycles)
    LOG.debug(f'Latest available cycle: {latest_cycle:%Y%m%d_%H%M}')

    if check_cycle_complete(latest_cycle):
        LOG.info(f'Latest complete cycle: {latest_cycle:%Y%m%d_%H%M}')
    else:
        latest_cycle = latest_cycle - timedelta(hours=6)
        if check_cycle_complete(latest_cycle):
            LOG.info(
                'Latest complete cycle: {:%Y%m%d_%H%M}'.format(latest_cycle))
        else:
            raise RuntimeError("Unable to determine latest cycle")
    return latest_cycle


def check_cycle_complete(dt):
    full_path = f'{GFS_BASE_DIR}/gfs.{dt:%Y%m%d%H}'
    req = requests.get(full_path)
    soup = BeautifulSoup(req.content, 'html.parser')

    taus = set()
    matcher = re.compile('^gfs.t\d\dz.pgrb2b.1p00.f\d\d\d$')
    for link in soup.find_all('a'):
        if matcher.match(link['href']):
            taus.add(int(link['href'][-3:]))

    return all(x in taus for x in range(0, 243, 3))


def download_cycle(dt):
    for tau in range(0, 6, 3):
        file_url = (f'{GFS_BASE_DIR}/gfs.{dt:%Y%m%d%H}/'
                    f'gfs.t{dt:%H}z.pgrb2.1p00.f{tau:03d}')
        req = requests.get(file_url, stream=True)
        out_file = f'{GRIB_DIR}/gfs_100_{dt:%Y%m%d}_{dt:%H%M}_{tau:03d}.grb2'
        if req.status_code == 200:
            with open(out_file, 'wb') as w:
                for chunk in req.iter_content(1024):
                    w.write(chunk)
            yield out_file
        else:
            raise RuntimeError(f'Unable to get {file_url}')
