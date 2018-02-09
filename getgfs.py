import json

import pygrib

GRIB_FILE_LOC = 'https://nomads.ncdc.noaa.gov/data/gfsanl/201801/20180119/gfsanl_3_20180119_0000_000.grb2'
GRIB_FILE = 'gfsanl_3_20180119_0000_000.grb2'


def main():
    grib_data = pygrib.open(GRIB_FILE)
    u_grib_data = grib_data.select(name='U component of wind')[0]
    v_grib_data = grib_data.select(name='V component of wind')[0]

    data = {}
    data['u_data'] = []
    data['v_data'] = []
    for x in range(360):
        data['u_data'].append([])
        data['v_data'].append([])
        for y in range(180, -1, -1):
            data['u_data'][x].append(float(u_grib_data['values'][y][x]))
            data['v_data'][x].append(float(v_grib_data['values'][y][x]))

    with open(GRIB_FILE.replace('grb2', 'json'), 'w') as w:
        json.dump(data, w)


if __name__ == '__main__':
    main()
