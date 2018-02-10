import json
import logging
import os

import pygrib

from . import gfs_download

LOG = logging.getLogger(__name__)
JSON_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../json_files'


def latest_gfs_to_json():
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
    cycle = gfs_download.get_latest_cycle()
    for i, grib_file_path in enumerate(gfs_download.download_cycle(cycle)):
        tau = i * 3
        grib_data = pygrib.open(grib_file_path)
        u_grib_data = grib_data.select(name='U component of wind')[0]
        v_grib_data = grib_data.select(name='V component of wind')[0]

        data = {}
        data['uData'] = []
        data['vData'] = []
        for x in range(360):
            data['uData'].append([])
            data['vData'].append([])
            for y in range(180, -1, -1):
                data['uData'][x].append(float(u_grib_data['values'][y][x]))
                data['vData'][x].append(float(v_grib_data['values'][y][x]))

        json_file_path = (f'{JSON_DIR}/'
                          f'gfs_3_{cycle:%Y%m%d}_{cycle:%H%M}_{tau:03d}.json')
        with open(json_file_path, 'w') as w:
            json.dump({'gfsData': data}, w)
        LOG.info(f'created {json_file_path}')
    with open(f'{JSON_DIR}/cycle', 'w') as w:
        w.write(f'{cycle:%Y%m%d_%H%M%S}\n')
    LOG.info(f'completed downloading cycle {cycle:%Y%m%d_%H%M%S}')

