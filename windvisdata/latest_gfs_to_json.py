import glob
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
    grib_files = []
    for i, grib_file_path in enumerate(gfs_download.download_cycle(cycle)):
        tau = i * 3
        grib_data = pygrib.open(grib_file_path)
        u_grib_data = grib_data.select(name='U component of wind')[0]
        v_grib_data = grib_data.select(name='V component of wind')[0]

        data_1_deg = {}
        data_1_deg['uData'] = []
        data_1_deg['vData'] = []
        data_2_deg = {}
        data_2_deg['uData'] = []
        data_2_deg['vData'] = []
        for x in range(360):
            data_1_deg['uData'].append([])
            data_1_deg['vData'].append([])
            if x % 2 == 0:
                data_2_deg['uData'].append([])
                data_2_deg['vData'].append([])

            for y in range(180, -1, -1):
                data_1_deg['uData'][x].append(
                    round(float(u_grib_data['values'][y][x])))
                data_1_deg['vData'][x].append(
                    round(float(v_grib_data['values'][y][x])))
                if y % 2 == 0:
                    data_2_deg['uData'][x // 2].append(
                        round(float(u_grib_data['values'][y][x])))
                    data_2_deg['vData'][x // 2].append(
                        round(float(v_grib_data['values'][y][x])))

        json_1_deg_path = (f'{JSON_DIR}/'
                           f'gfs_100_{cycle:%Y%m%d_%H%M%S}_{tau:03d}.json')
        with open(json_1_deg_path, 'w') as w:
            json.dump({'gfsData': data_1_deg}, w)
        LOG.info(f'created {json_1_deg_path}')

        json_2_deg_path = (f'{JSON_DIR}/'
                           f'gfs_200_{cycle:%Y%m%d_%H%M%S}_{tau:03d}.json')
        with open(json_2_deg_path, 'w') as w:
            json.dump({'gfsData': data_2_deg}, w)
        LOG.info(f'created {json_2_deg_path}')

    with open(f'{JSON_DIR}/cycle.json', 'w') as w:
        json.dump({'cycle': f'{cycle:%Y%m%d_%H%M%S}'}, w)

    for f in glob.glob(gfs_download.GRIB_ + '/*'):
        os.remove(f)
    LOG.info(f'completed downloading cycle {cycle:%Y%m%d_%H%M%S}')
