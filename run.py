import logging
import sys
import os

from windvisdata.latest_gfs_to_json import latest_gfs_to_json

log_file = os.path.dirname(os.path.realpath(__file__)) + '/wind-vis-data.log'

logging.basicConfig(
    format='%(asctime)-15s %(message)s',
    filename=log_file,
    level=logging.INFO)

latest_gfs_to_json()
