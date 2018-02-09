from datetime import datetime, timedelta
import logging

from bs4 import BeautifulSoup
import requests

GFS_BASE_DIR = 'https://nomads.ncdc.noaa.gov/data/gfs4'
LOG = logging.getLogger(__name__)


def get_latest_gfs_cycle():
    # Get latest link to latest month on page
    req = requests.get(GFS_BASE_DIR)
    soup = BeautifulSoup(req.content, 'html.parser')
    months = []
    for link in soup.find_all('a'):
        try:
            months.append(datetime.strptime(link['href'], '%Y%m/'))
        except ValueError as e:
            # Link date parse failed
            pass
    latest_month = max(months)
    LOG.debug(f'Latest availble month: {latest_month:%Y%m}')

    # Get latest link to latest day on page
    month_dir = GFS_BASE_DIR + datetime.strftime(latest_month, '/%Y%m')
    req = requests.get(month_dir)
    soup = BeautifulSoup(req.content, 'html.parser')
    days = []
    for link in soup.find_all('a'):
        try:
            days.append(datetime.strptime(link['href'], '%Y%m%d/'))
        except ValueError as e:
            # Link date parse failed
            pass
    latest_day = max(days)
    LOG.debug(f'Latest availble day: {latest_day:%Y%m%d}')

    # Get latest cycle on page
    day_dir = month_dir + datetime.strftime(latest_day, '/%Y%m%d')
    req = requests.get(day_dir)
    soup = BeautifulSoup(req.content, 'html.parser')
    cycles = []
    for link in soup.find_all('a'):
        try:
            date_part = '_'.join(link['href'].split('_')[2:4])
            cycles.append(datetime.strptime(date_part, '%Y%m%d_%H%M'))
        except ValueError as e:
            # Link date parse failed
            pass
    latest_cycle = max(cycles)
    LOG.debug(f'Latest available cycle: {latest_cycle:%Y%m%d_%H%M}')

    if check_cycle_complete(latest_cycle):
        LOG.info(f'Latest complete cycle: {latest_cycle:%Y%m%d_%H%M}')
    else:
        latest_cycle = latest_cycle - timedelta(h=6)
        if check_cycle_complete(latest_cycle):
            LOG.info(
                'Latest complete cycle: {:%Y%m%d_%H%M}'.format(latest_cycle))
        else:
            raise RuntimeError("Unable to determine latest cycle")
    return latest_cycle


def check_cycle_complete(dt):
    full_path = f'{GFS_BASE_DIR}/{dt:%Y%m}/{dt:%Y%m%d}'
    req = requests.get(full_path)
    soup = BeautifulSoup(req.content, 'html.parser')
    cycle_files = []
    for link in soup.find_all('a'):
        try:
            date_part = '_'.join(link['href'].split('_')[2:4])
            cycle = datetime.strptime(date_part, '%Y%m%d_%H%M')
            if cycle == dt:
                cycle_files.append(link['href'])
        except ValueError as e:
            # Link date parse failed
            pass

    taus = set()
    for file_name in cycle_files:
        taus.add(int(file_name.split('_')[-1].split('.')[0]))

    return all(x in taus for x in range(0, 243, 3))


def download_cycle(dt):
    for tau in range(0, 15, 3):
        yield requests.get(
            f'{GFS_BASE_DIR}/{dt:%Y%m}/{dt:%Y%m%d}/'
            f'gfs_4_{dt:%Y%m%d}_{dt:%H%M}_{tau:03d}.grb2'
        ).content


if __name__ == '__main__':
    import sys
    logging.basicConfig(
        format='%(asctime)-15s %(message)s',
        stream=sys.stdout,
        level=logging.INFO)
    cycle = get_latest_gfs_cycle()
    gribs = download_cycle(cycle)
    for i, grib in enumerate(gribs):
        print(grib)

